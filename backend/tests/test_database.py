"""Database tests for Agritech Platform."""

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.reference import Technology


pytestmark = pytest.mark.asyncio


class TestDatabaseConnection:
    """Test 1: Database connection functionality."""

    async def test_database_connection(self, db_session: AsyncSession):
        """Test that database connection works."""
        result = await db_session.execute(text("SELECT 1"))
        assert result.scalar_one() == 1


class TestRequiredFields:
    """Test 2: Required fields are enforced."""

    async def test_create_technology_without_name(self, db_session: AsyncSession):
        """Test that creating a Technology without a name raises IntegrityError."""
        technology = Technology(
            slug="test-slug",
            description="Test description",
        )
        db_session.add(technology)

        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestUniqueConstraints:
    """Test 3: Unique constraints work."""

    async def test_duplicate_slug_raises_error(self, db_session: AsyncSession):
        """Test that creating two Technologies with same slug raises IntegrityError."""
        tech1 = Technology(
            name="Technology 1",
            slug="same-slug",
        )
        tech2 = Technology(
            name="Technology 2",
            slug="same-slug",
        )

        db_session.add(tech1)
        await db_session.commit()

        db_session.add(tech2)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_duplicate_name_raises_error(self, db_session: AsyncSession):
        """Test that creating two Technologies with same name raises IntegrityError."""
        tech1 = Technology(
            name="Same Name",
            slug="slug-1",
        )
        tech2 = Technology(
            name="Same Name",
            slug="slug-2",
        )

        db_session.add(tech1)
        await db_session.commit()

        db_session.add(tech2)

        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestTransactionRollback:
    """Test 4: Transactions roll back properly."""

    async def test_transaction_rollback(self, db_session: AsyncSession):
        """Test that transaction rollback removes inserted records."""
        # Insert a record
        technology = Technology(
            name="Rollback Test",
            slug="rollback-test",
        )
        db_session.add(technology)
        await db_session.commit()

        # Verify it exists
        result = await db_session.execute(
            text("SELECT COUNT(*) FROM technologies WHERE name = 'Rollback Test'")
        )
        count = result.scalar_one()
        assert count == 1

        # Rollback
        await db_session.rollback()

        # Create a new session to verify the record still exists in database
        # (rollback only affects the current session, not committed data)
        # Instead test that rolling back prevents insertion
        test_tech = Technology(
            name="Never Committed",
            slug="never-committed",
        )
        db_session.add(test_tech)
        await db_session.rollback()

        # Verify the uncommitted record is not in the session
        assert test_tech not in db_session


class TestHealthEndpoint:
    """Test 5: Health endpoint functionality."""

    async def test_database_health_endpoint(self, client: AsyncClient):
        """Test that database health endpoint returns correct response."""
        response = await client.get("/health/database")

        assert response.status_code == 200
        data = response.json()
        assert data["database"] == "connected"
        assert data["status"] == "healthy"

    async def test_health_endpoint(self, client: AsyncClient):
        """Test that general health endpoint works."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

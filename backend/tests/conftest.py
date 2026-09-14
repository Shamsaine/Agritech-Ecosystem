import asyncio
import os
import sys
from collections.abc import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_db_session
from main import app


# Windows ProactorEventLoop compatibility - must happen before any async code
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Override settings for test environment."""
    return Settings(
        postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
        postgres_port=int(os.getenv("POSTGRES_PORT", 5434)),
        postgres_db="agritech_test",
        postgres_user=os.getenv("POSTGRES_USER", "agritech_user"),
        postgres_password=os.getenv("POSTGRES_PASSWORD", "agritech_password"),
        app_env="testing",
        debug=False,
    )


async def create_test_database(test_settings: Settings) -> None:
    """Create the test database if it doesn't exist."""
    try:
        import psycopg
        
        # Connect to the default postgres database
        conn = await psycopg.AsyncConnection.connect(
            host=test_settings.postgres_host,
            port=test_settings.postgres_port,
            user=test_settings.postgres_user,
            password=test_settings.postgres_password,
            dbname="postgres",
            autocommit=True,  # Set autocommit on connection creation
        )
        
        try:
            # Check if test database exists
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (test_settings.postgres_db,),
                )
                row = await cur.fetchone()
                db_exists = row is not None
            
            if not db_exists:
                # Create test database
                async with conn.cursor() as cur:
                    await cur.execute(
                        f'CREATE DATABASE "{test_settings.postgres_db}"'
                    )
        finally:
            await conn.close()
    except Exception:
        # If we can't create the database, assume it exists or skip
        pass


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database(test_settings: Settings):
    """Setup test database before running tests."""
    await create_test_database(test_settings)
    yield
    # Cleanup could happen here if needed


@pytest.fixture
async def test_engine(test_settings: Settings):
    """Create test database engine."""
    engine = create_async_engine(
        test_settings.database_url,
        echo=False,
        poolclass=NullPool,  # Avoid connection pooling issues in tests
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture
async def client(test_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with overridden database dependency."""

    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield test_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def db_session(test_session: AsyncSession) -> AsyncSession:
    """Provide test session for non-endpoint tests."""
    return test_session


@pytest.fixture
async def imported_pilot_data(db_session: AsyncSession):
    """Seed a realistic public pilot dataset for browsing and detail tests."""
    from app.db.models import Application, Category, Location, Organisation, Technology

    location = Location(
        name="Nigeria",
        slug="nigeria",
        location_type="country",
        country_code="NG",
        is_active=True,
    )
    organisation = Organisation(
        name="TracTrac Mechanization Services Limited",
        slug="tractrac-mechanization-services-limited",
        organisation_type="organisation",
        verification_status="unverified",
        is_active=True,
        headquarters_location=location,
    )
    technology = Technology(name="GIS Remote Sensing", slug="gis-remote-sensing", is_active=True)
    category = Category(name="Crop Production Tools", slug="crop-production-tools", is_active=True)
    db_session.add_all([location, organisation, technology, category])
    await db_session.flush()

    for index in range(1, 39):
        app = Application(
            name=f"Pilot App {index}",
            slug=f"pilot-app-{index}",
            summary=f"App {index} summary",
            description=f"Description {index}",
            website_url=f"https://example.com/{index}",
            launch_year=2020 + (index % 5),
            owning_organisation_id=organisation.id,
            verification_status="unverified" if index % 3 else "verified",
            record_status="pilot",
            is_active=True,
            source_record_id=f"AGR-{1000 + index}",
        )
        app.locations.append(location)
        app.technologies.append(technology)
        app.categories.append(category)
        db_session.add(app)

    quarantined = Application(
        name="Quarantined App",
        slug="quarantined-app",
        summary="Hidden from public browsing",
        description="This record is quarantined",
        website_url="https://example.com/quarantined",
        launch_year=2024,
        owning_organisation_id=organisation.id,
        verification_status="rejected",
        record_status="quarantined",
        is_active=True,
        source_record_id="AGR-9999",
    )
    db_session.add(quarantined)

    await db_session.commit()
    return {"total_public": 38, "quarantined": quarantined.id}

"""Tests for Checkpoint 9 core entity models and schemas."""

from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    AccessType,
    Application,
    AvailabilityStatus,
    Developer,
    Location,
    Organisation,
)
from app.schemas.core import (
    ApplicationCreateRequest,
    LocationCreateRequest,
    OrganisationCreateRequest,
)

@pytest.mark.asyncio
async def test_core_entities_and_relationships(db_session: AsyncSession):
    location = Location(
        name="Nairobi",
        slug="nairobi",
        location_type="city",
        country_code="KE",
        latitude=-1.2864,
        longitude=36.8172,
    )
    organisation = Organisation(
        name="Agri Labs",
        slug="agri-labs",
        organisation_type="company",
        headquarters_location=location,
    )
    developer = Developer(
        name="Agri Labs Team",
        slug="agri-labs-team",
        developer_type="team",
        organisation=organisation,
    )
    access_type = AccessType(name="Open Source", slug="open-source")
    availability_status = AvailabilityStatus(name="Available", slug="available")
    db_session.add_all([location, organisation, developer, access_type, availability_status])
    await db_session.flush()

    application = Application(
        name="Field Monitor",
        slug="field-monitor",
        owning_organisation=organisation,
        access_type_id=access_type.id,
        availability_status_id=availability_status.id,
    )
    db_session.add(application)
    await db_session.commit()
    await db_session.refresh(application)

    assert organisation.headquarters_location is location
    assert developer.organisation is organisation
    assert application.owning_organisation is organisation
    assert application.access_type_id == access_type.id
    assert application.availability_status_id == availability_status.id

@pytest.mark.asyncio
async def test_duplicate_core_slug_is_rejected(db_session: AsyncSession):
    db_session.add(Location(name="Nairobi", slug="nairobi", location_type="city", country_code="KE"))
    await db_session.commit()

    db_session.add(Location(name="Another Nairobi", slug="nairobi", location_type="city", country_code="KE"))
    with pytest.raises(IntegrityError):
        await db_session.commit()

@pytest.mark.asyncio
async def test_location_coordinate_constraint_is_enforced(db_session: AsyncSession):
    db_session.add(
        Location(
            name="Invalid Location",
            slug="invalid-location",
            location_type="city",
            country_code="KE",
            latitude=91,
        )
    )

    with pytest.raises(IntegrityError):
        await db_session.commit()

@pytest.mark.asyncio
async def test_application_year_constraint_is_enforced(db_session: AsyncSession):
    db_session.add(
        Application(
            name="Invalid Application",
            slug="invalid-application",
            launch_year=1899,
        )
    )

    with pytest.raises(IntegrityError):
        await db_session.commit()


def test_schema_validates_slug_and_coordinates():
    location = LocationCreateRequest(
        name="Nairobi",
        slug="nairobi-city",
        location_type="city",
        country_code="KE",
        latitude=-1.2864,
        longitude=36.8172,
    )
    assert location.slug == "nairobi-city"

    with pytest.raises(ValidationError):
        LocationCreateRequest(
            name="Nairobi",
            slug="Nairobi City",
            location_type="city",
            country_code="KE",
        )

    with pytest.raises(ValidationError):
        LocationCreateRequest(
            name="Nairobi",
            slug="nairobi-city",
            location_type="city",
            country_code="KE",
            latitude=91,
        )


def test_schema_required_fields_and_year_bounds():
    with pytest.raises(ValidationError):
        OrganisationCreateRequest(
            name="Agri Labs",
            slug="agri-labs",
        )

    with pytest.raises(ValidationError):
        ApplicationCreateRequest(
            name="Field Monitor",
            slug="field-monitor",
            launch_year=1899,
        )

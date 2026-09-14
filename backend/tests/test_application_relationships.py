"""Tests for Checkpoint 10 application relationships."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Application,
    Category,
    Developer,
    FocusArea,
    Language,
    Location,
    PhysicalComponent,
    Platform,
    Technology,
)
from app.db.models.associations import (
    application_categories,
    application_developers,
    application_focus_areas,
    application_languages,
    application_locations,
    application_physical_components,
    application_platforms,
    application_technologies,
)

pytestmark = pytest.mark.asyncio


async def test_application_relationships_navigate_both_directions(
    db_session: AsyncSession,
):
    application = Application(name="Farm Guide", slug="farm-guide")
    second_application = Application(name="Crop Adviser", slug="crop-adviser")
    developer = Developer(
        name="Agri Team",
        slug="agri-team",
        developer_type="team",
    )
    location = Location(
        name="Nairobi",
        slug="nairobi",
        location_type="city",
        country_code="KE",
    )
    technology = Technology(name="Artificial Intelligence", slug="artificial-intelligence")
    second_technology = Technology(name="Internet of Things", slug="internet-of-things")
    platform = Platform(name="Web", slug="web")
    language = Language(name="English", slug="english")
    category = Category(name="Advisory", slug="advisory")
    focus_area = FocusArea(name="Crop Health", slug="crop-health")
    physical_component = PhysicalComponent(name="Sensor", slug="sensor")

    application.developers.append(developer)
    application.locations.append(location)
    application.technologies.extend([technology, second_technology])
    application.platforms.append(platform)
    application.languages.append(language)
    application.categories.append(category)
    application.focus_areas.append(focus_area)
    application.physical_components.append(physical_component)
    second_application.technologies.append(technology)
    db_session.add_all([application, second_application])
    await db_session.commit()

    assert [item.slug for item in application.technologies] == [
        "artificial-intelligence",
        "internet-of-things",
    ]
    assert application in technology.applications
    assert second_application in technology.applications
    assert application in developer.applications
    assert application in location.applications
    assert application in category.applications
    assert application in platform.applications
    assert application in language.applications
    assert application in focus_area.applications
    assert application in physical_component.applications


async def test_duplicate_relationship_is_rejected(db_session: AsyncSession):
    application = Application(name="Farm Guide", slug="farm-guide")
    technology = Technology(name="Artificial Intelligence", slug="artificial-intelligence")
    application.technologies.append(technology)
    db_session.add(application)
    await db_session.commit()

    with pytest.raises(IntegrityError):
        await db_session.execute(
            application_technologies.insert().values(
                application_id=application.id,
                technology_id=technology.id,
            )
        )


async def test_deleting_application_cascades_relationship_rows_but_keeps_shared_entities(
    db_session: AsyncSession,
):
    application = Application(name="Farm Guide", slug="farm-guide")
    shared_technology = Technology(name="Artificial Intelligence", slug="artificial-intelligence")
    application.technologies.append(shared_technology)
    db_session.add(application)
    await db_session.commit()
    application_id = application.id
    technology_id = shared_technology.id

    await db_session.delete(application)
    await db_session.commit()

    relationship_row = await db_session.execute(
        select(application_technologies).where(
            application_technologies.c.application_id == application_id,
        )
    )
    technology = await db_session.get(Technology, technology_id)
    assert relationship_row.first() is None
    assert technology is not None


async def test_association_tables_have_composite_primary_keys_and_cascade_fks():
    association_tables = (
        application_developers,
        application_locations,
        application_technologies,
        application_platforms,
        application_languages,
        application_categories,
        application_focus_areas,
        application_physical_components,
    )

    for table in association_tables:
        assert len(table.primary_key.columns) == 2
        assert {column.name for column in table.primary_key.columns} == {
            "application_id",
            next(column.name for column in table.columns if column.name.endswith("_id") and column.name != "application_id"),
        }
        foreign_keys = list(table.foreign_keys)
        assert len(foreign_keys) == 2
        assert all(foreign_key.ondelete == "CASCADE" for foreign_key in foreign_keys)
        assert table.c.created_at.nullable is False

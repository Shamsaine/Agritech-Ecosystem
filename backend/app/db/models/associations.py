"""Many-to-many association tables for applications."""

from sqlalchemy import Column, DateTime, ForeignKey, Table, func
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


def application_association_table(
    name: str,
    related_table: str,
    related_key: str,
) -> Table:
    """Create a standard application-to-entity association table."""
    return Table(
        name,
        Base.metadata,
        Column(
            "application_id",
            UUID(as_uuid=True),
            ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
            primary_key=True,
        ),
        Column(
            related_key,
            UUID(as_uuid=True),
            ForeignKey(f"{related_table}.id", ondelete="CASCADE"),
            nullable=False,
            primary_key=True,
        ),
        Column(
            "created_at",
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )


application_developers = application_association_table(
    "application_developers",
    "developers",
    "developer_id",
)
application_locations = application_association_table(
    "application_locations",
    "locations",
    "location_id",
)
application_technologies = application_association_table(
    "application_technologies",
    "technologies",
    "technology_id",
)
application_platforms = application_association_table(
    "application_platforms",
    "platforms",
    "platform_id",
)
application_languages = application_association_table(
    "application_languages",
    "languages",
    "language_id",
)
application_categories = application_association_table(
    "application_categories",
    "categories",
    "category_id",
)
application_focus_areas = application_association_table(
    "application_focus_areas",
    "focus_areas",
    "focus_area_id",
)
application_physical_components = application_association_table(
    "application_physical_components",
    "physical_components",
    "physical_component_id",
)

__all__ = [
    "application_association_table",
    "application_categories",
    "application_developers",
    "application_focus_areas",
    "application_languages",
    "application_locations",
    "application_physical_components",
    "application_platforms",
    "application_technologies",
]

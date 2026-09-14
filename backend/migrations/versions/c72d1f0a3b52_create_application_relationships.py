"""create application relationship tables

Revision ID: c72d1f0a3b52
Revises: cbb0d6b57968

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c72d1f0a3b52"
down_revision: Union[str, Sequence[str], None] = "cbb0d6b57968"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ASSOCIATIONS = (
    ("application_developers", "developer_id", "developers"),
    ("application_locations", "location_id", "locations"),
    ("application_technologies", "technology_id", "technologies"),
    ("application_platforms", "platform_id", "platforms"),
    ("application_languages", "language_id", "languages"),
    ("application_categories", "category_id", "categories"),
    ("application_focus_areas", "focus_area_id", "focus_areas"),
    ("application_physical_components", "physical_component_id", "physical_components"),
)


def upgrade() -> None:
    """Create application many-to-many relationship tables."""
    for table_name, related_key, related_table in ASSOCIATIONS:
        op.create_table(
            table_name,
            sa.Column(
                "application_id",
                sa.UUID(),
                nullable=False,
            ),
            sa.Column(
                related_key,
                sa.UUID(),
                nullable=False,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["application_id"],
                ["applications.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                [related_key],
                [f"{related_table}.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("application_id", related_key),
        )


def downgrade() -> None:
    """Drop application many-to-many relationship tables."""
    for table_name, _, _ in reversed(ASSOCIATIONS):
        op.drop_table(table_name)

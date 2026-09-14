"""support transactional pilot import

Revision ID: e91f4c2d8a12
Revises: d83e2a1b4c63
Create Date: 2026-09-13 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e91f4c2d8a12"
down_revision: Union[str, Sequence[str], None] = "d83e2a1b4c63"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ASSOCIATION_TABLES = (
    "application_developers",
    "application_locations",
    "application_technologies",
    "application_platforms",
    "application_languages",
    "application_categories",
    "application_focus_areas",
    "application_physical_components",
)


def upgrade() -> None:
    op.add_column("applications", sa.Column("source_record_id", sa.String(length=50), nullable=True))
    op.add_column("applications", sa.Column("record_status", sa.String(length=30), server_default="draft", nullable=False))
    op.create_index(op.f("ix_applications_source_record_id"), "applications", ["source_record_id"], unique=True)
    op.create_index(op.f("ix_applications_record_status"), "applications", ["record_status"], unique=False)

    op.alter_column("evidence_sources", "title", existing_type=sa.String(length=255), type_=sa.String(length=300), nullable=False)
    op.alter_column("evidence_sources", "url", existing_type=sa.String(length=2048), nullable=True)
    op.drop_constraint(op.f("uq_evidence_sources_url"), "evidence_sources", type_="unique")
    op.drop_index(op.f("ix_evidence_sources_url"), table_name="evidence_sources")
    op.create_index(op.f("ix_evidence_sources_url"), "evidence_sources", ["url"], unique=False)

    op.add_column("import_batches", sa.Column("quarantined_rows", sa.Integer(), server_default="0", nullable=False))
    op.create_check_constraint(
        "quarantined_rows_nonnegative",
        "import_batches",
        "quarantined_rows >= 0",
    )
    op.drop_constraint(op.f("ck_import_batches_results_le_processed"), "import_batches", type_="check")
    op.create_check_constraint(
        "ck_import_batches_results_le_processed",
        "import_batches",
        "successful_rows + failed_rows + quarantined_rows <= processed_rows",
    )

    op.alter_column(
        "locations",
        "country_code",
        existing_type=sa.String(length=2),
        nullable=True,
    )
    op.alter_column(
        "data_quality_issues",
        "field_name",
        existing_type=sa.String(length=100),
        nullable=True,
    )

    for table_name in ASSOCIATION_TABLES:
        op.add_column(table_name, sa.Column("role", sa.String(length=50), nullable=True))
        op.add_column(table_name, sa.Column("relationship_type", sa.String(length=80), nullable=True))
        op.add_column(
            table_name,
            sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        )
        op.add_column(table_name, sa.Column("confidence", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("applications", "record_status")
    op.drop_index(op.f("ix_applications_source_record_id"), table_name="applications")
    op.drop_column("applications", "source_record_id")

    op.drop_index(op.f("ix_evidence_sources_url"), table_name="evidence_sources")
    op.alter_column("evidence_sources", "url", existing_type=sa.String(length=2048), nullable=False)
    op.alter_column("evidence_sources", "title", existing_type=sa.String(length=300), type_=sa.String(length=255), nullable=False)
    op.create_index(op.f("ix_evidence_sources_url"), "evidence_sources", ["url"], unique=True)

    op.drop_constraint(op.f("ck_import_batches_results_le_processed"), "import_batches", type_="check")
    op.create_check_constraint(
        "ck_import_batches_results_le_processed",
        "import_batches",
        "successful_rows + failed_rows <= processed_rows",
    )

    op.drop_constraint("quarantined_rows_nonnegative", "import_batches", type_="check")
    op.drop_column("import_batches", "quarantined_rows")

    op.alter_column(
        "data_quality_issues",
        "field_name",
        existing_type=sa.String(length=100),
        nullable=False,
    )
    op.alter_column(
        "locations",
        "country_code",
        existing_type=sa.String(length=2),
        nullable=False,
    )

    for table_name in reversed(ASSOCIATION_TABLES):
        op.drop_column(table_name, "confidence")
        op.drop_column(table_name, "is_primary")
        op.drop_column(table_name, "relationship_type")
        op.drop_column(table_name, "role")

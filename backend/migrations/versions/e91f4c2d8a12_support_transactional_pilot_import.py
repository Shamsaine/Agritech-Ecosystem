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


def upgrade() -> None:
    op.add_column("applications", sa.Column("source_record_id", sa.String(length=50), nullable=True))
    op.add_column("applications", sa.Column("record_status", sa.String(length=30), server_default="draft", nullable=False))
    op.create_index(op.f("ix_applications_source_record_id"), "applications", ["source_record_id"], unique=True)
    op.create_index(op.f("ix_applications_record_status"), "applications", ["record_status"], unique=False)

    op.alter_column("evidence_sources", "title", existing_type=sa.String(length=255), type_=sa.String(length=300), nullable=False)
    op.alter_column("evidence_sources", "url", existing_type=sa.String(length=2048), nullable=True)
    op.drop_constraint(op.f("uq_evidence_sources_url"), "evidence_sources", type_="unique")
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

    op.add_column("application_association_tables", sa.Column("role", sa.String(length=50), nullable=True))
    op.add_column("application_association_tables", sa.Column("relationship_type", sa.String(length=80), nullable=True))
    op.add_column("application_association_tables", sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("application_association_tables", sa.Column("confidence", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("applications", "record_status")
    op.drop_index(op.f("ix_applications_source_record_id"), table_name="applications")
    op.drop_column("applications", "source_record_id")

    op.drop_index(op.f("ix_evidence_sources_url"), table_name="evidence_sources")
    op.alter_column("evidence_sources", "url", existing_type=sa.String(length=2048), nullable=False)
    op.alter_column("evidence_sources", "title", existing_type=sa.String(length=300), type_=sa.String(length=255), nullable=False)
    op.create_index(op.f("ix_evidence_sources_url"), "evidence_sources", ["url"], unique=True)

    op.drop_column("import_batches", "quarantined_rows")
    op.drop_constraint(op.f("ck_import_batches_results_le_processed"), "import_batches", type_="check")
    op.create_check_constraint(
        "ck_import_batches_results_le_processed",
        "import_batches",
        "successful_rows + failed_rows <= processed_rows",
    )

    op.drop_column("application_association_tables", "confidence")
    op.drop_column("application_association_tables", "is_primary")
    op.drop_column("application_association_tables", "relationship_type")
    op.drop_column("application_association_tables", "role")

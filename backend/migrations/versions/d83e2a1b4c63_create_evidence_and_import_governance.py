"""create evidence and import governance tables

Revision ID: d83e2a1b4c63
Revises: c72d1f0a3b52

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d83e2a1b4c63"
down_revision: Union[str, Sequence[str], None] = "c72d1f0a3b52"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create evidence, verification, import, and quality tables."""
    op.create_table(
        "evidence_sources",
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("publisher", sa.String(length=255), nullable=True),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accessed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evidence_sources")),
        sa.UniqueConstraint("url", name=op.f("uq_evidence_sources_url")),
    )
    op.create_index(op.f("ix_evidence_sources_url"), "evidence_sources", ["url"], unique=True)

    op.create_table(
        "application_evidence",
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("claim_field", sa.String(length=100), nullable=False),
        sa.Column("claim_value", sa.Text(), nullable=False),
        sa.Column("supporting_note", sa.Text(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("verification_status", sa.String(length=50), server_default="unverified", nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["evidence_sources.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_application_evidence")),
        sa.UniqueConstraint(
            "application_id",
            "source_id",
            "claim_field",
            name="uq_application_evidence_application_source_field",
        ),
    )
    op.create_index(op.f("ix_application_evidence_application_id"), "application_evidence", ["application_id"])
    op.create_index(op.f("ix_application_evidence_source_id"), "application_evidence", ["source_id"])

    op.create_table(
        "verification_reviews",
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("evidence_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("reviewer_name", sa.String(length=255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("next_review_due", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_id"], ["application_evidence.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_verification_reviews")),
    )
    op.create_index(op.f("ix_verification_reviews_application_id"), "verification_reviews", ["application_id"])
    op.create_index(op.f("ix_verification_reviews_evidence_id"), "verification_reviews", ["evidence_id"])

    op.create_table(
        "import_batches",
        sa.Column("filename", sa.String(length=500), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="pending", nullable=False),
        sa.Column("total_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("processed_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("successful_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("total_rows >= 0", name=op.f("ck_import_batches_total_rows_nonnegative")),
        sa.CheckConstraint("processed_rows >= 0", name=op.f("ck_import_batches_processed_rows_nonnegative")),
        sa.CheckConstraint("successful_rows >= 0", name=op.f("ck_import_batches_successful_rows_nonnegative")),
        sa.CheckConstraint("failed_rows >= 0", name=op.f("ck_import_batches_failed_rows_nonnegative")),
        sa.CheckConstraint("processed_rows <= total_rows", name=op.f("ck_import_batches_processed_le_total")),
        sa.CheckConstraint(
            "successful_rows + failed_rows <= processed_rows",
            name=op.f("ck_import_batches_results_le_processed"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_import_batches")),
        sa.UniqueConstraint("checksum_sha256", name=op.f("uq_import_batches_checksum_sha256")),
    )
    op.create_index(op.f("ix_import_batches_checksum_sha256"), "import_batches", ["checksum_sha256"], unique=True)

    op.create_table(
        "import_rows",
        sa.Column("batch_id", sa.UUID(), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("normalized_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="pending", nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("row_number > 0", name=op.f("ck_import_rows_row_number_positive")),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["batch_id"], ["import_batches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_import_rows")),
        sa.UniqueConstraint("batch_id", "row_number", name="uq_import_rows_batch_row_number"),
    )
    op.create_index(op.f("ix_import_rows_batch_id"), "import_rows", ["batch_id"])
    op.create_index(op.f("ix_import_rows_application_id"), "import_rows", ["application_id"])

    op.create_table(
        "data_quality_issues",
        sa.Column("application_id", sa.UUID(), nullable=True),
        sa.Column("import_row_id", sa.UUID(), nullable=True),
        sa.Column("field_name", sa.String(length=100), nullable=False),
        sa.Column("issue_type", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="open", nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "(application_id IS NOT NULL AND import_row_id IS NULL) OR "
            "(application_id IS NULL AND import_row_id IS NOT NULL)",
            name=op.f("ck_data_quality_issues_exactly_one_parent"),
        ),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["import_row_id"], ["import_rows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_data_quality_issues")),
    )
    op.create_index(op.f("ix_data_quality_issues_application_id"), "data_quality_issues", ["application_id"])
    op.create_index(op.f("ix_data_quality_issues_import_row_id"), "data_quality_issues", ["import_row_id"])


def downgrade() -> None:
    """Drop governance tables in dependency-safe order."""
    op.drop_index(op.f("ix_data_quality_issues_import_row_id"), table_name="data_quality_issues")
    op.drop_index(op.f("ix_data_quality_issues_application_id"), table_name="data_quality_issues")
    op.drop_table("data_quality_issues")
    op.drop_index(op.f("ix_import_rows_application_id"), table_name="import_rows")
    op.drop_index(op.f("ix_import_rows_batch_id"), table_name="import_rows")
    op.drop_table("import_rows")
    op.drop_index(op.f("ix_import_batches_checksum_sha256"), table_name="import_batches")
    op.drop_table("import_batches")
    op.drop_index(op.f("ix_verification_reviews_evidence_id"), table_name="verification_reviews")
    op.drop_index(op.f("ix_verification_reviews_application_id"), table_name="verification_reviews")
    op.drop_table("verification_reviews")
    op.drop_index(op.f("ix_application_evidence_source_id"), table_name="application_evidence")
    op.drop_index(op.f("ix_application_evidence_application_id"), table_name="application_evidence")
    op.drop_table("application_evidence")
    op.drop_index(op.f("ix_evidence_sources_url"), table_name="evidence_sources")
    op.drop_table("evidence_sources")

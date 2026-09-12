"""Evidence, verification, import, and data-quality governance models."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.core import Application


class EvidenceSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A source that supports one or more application claims."""

    __tablename__ = "evidence_sources"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True, index=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    evidence: Mapped[list["ApplicationEvidence"]] = relationship(
        "ApplicationEvidence",
        back_populates="source",
        passive_deletes=True,
    )


class ApplicationEvidence(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A claim about an application supported by a source."""

    __tablename__ = "application_evidence"

    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("evidence_sources.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    claim_field: Mapped[str] = mapped_column(String(100), nullable=False)
    claim_value: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    verification_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="unverified", server_default="unverified"
    )

    application: Mapped["Application"] = relationship("Application", back_populates="evidence")
    source: Mapped[EvidenceSource] = relationship("EvidenceSource", back_populates="evidence")
    reviews: Mapped[list["VerificationReview"]] = relationship(
        "VerificationReview",
        back_populates="evidence",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "application_id",
            "source_id",
            "claim_field",
            name="uq_application_evidence_application_source_field",
        ),
    )


class VerificationReview(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A human decision recorded against application evidence."""

    __tablename__ = "verification_reviews"

    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_id: Mapped[UUID] = mapped_column(
        ForeignKey("application_evidence.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    reviewer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    next_review_due: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    application: Mapped["Application"] = relationship("Application", back_populates="verification_reviews")
    evidence: Mapped[ApplicationEvidence] = relationship("ApplicationEvidence", back_populates="reviews")


class ImportBatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A controlled import attempt for one source file."""

    __tablename__ = "import_batches"

    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", server_default="pending")
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    processed_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    successful_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    failed_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    rows: Mapped[list["ImportRow"]] = relationship(
        "ImportRow",
        back_populates="batch",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint("total_rows >= 0", name="ck_import_batches_total_rows_nonnegative"),
        CheckConstraint("processed_rows >= 0", name="ck_import_batches_processed_rows_nonnegative"),
        CheckConstraint("successful_rows >= 0", name="ck_import_batches_successful_rows_nonnegative"),
        CheckConstraint("failed_rows >= 0", name="ck_import_batches_failed_rows_nonnegative"),
        CheckConstraint("processed_rows <= total_rows", name="ck_import_batches_processed_le_total"),
        CheckConstraint(
            "successful_rows + failed_rows <= processed_rows",
            name="ck_import_batches_results_le_processed",
        ),
    )


class ImportRow(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An immutable source row and its separately normalized representation."""

    __tablename__ = "import_rows"

    batch_id: Mapped[UUID] = mapped_column(
        ForeignKey("import_batches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    normalized_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", server_default="pending")
    application_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("applications.id", ondelete="SET NULL"), nullable=True, index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    batch: Mapped[ImportBatch] = relationship("ImportBatch", back_populates="rows")
    application: Mapped["Application | None"] = relationship("Application", back_populates="import_rows")
    quality_issues: Mapped[list["DataQualityIssue"]] = relationship(
        "DataQualityIssue",
        back_populates="import_row",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint("batch_id", "row_number", name="uq_import_rows_batch_row_number"),
        CheckConstraint("row_number > 0", name="ck_import_rows_row_number_positive"),
    )


class DataQualityIssue(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A problem discovered during import or review."""

    __tablename__ = "data_quality_issues"

    application_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=True, index=True
    )
    import_row_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("import_rows.id", ondelete="CASCADE"), nullable=True, index=True
    )
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    issue_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open", server_default="open")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    application: Mapped["Application | None"] = relationship("Application", back_populates="quality_issues")
    import_row: Mapped["ImportRow | None"] = relationship("ImportRow", back_populates="quality_issues")

    __table_args__ = (
        CheckConstraint(
            "(application_id IS NOT NULL AND import_row_id IS NULL) OR "
            "(application_id IS NULL AND import_row_id IS NOT NULL)",
            name="ck_data_quality_issues_exactly_one_parent",
        ),
    )


__all__ = [
    "ApplicationEvidence",
    "DataQualityIssue",
    "EvidenceSource",
    "ImportBatch",
    "ImportRow",
    "VerificationReview",
]

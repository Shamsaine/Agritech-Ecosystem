"""Tests for Checkpoint 11 evidence and import governance models."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Application,
    ApplicationEvidence,
    DataQualityIssue,
    EvidenceSource,
    ImportBatch,
    ImportRow,
    VerificationReview,
)

pytestmark = pytest.mark.asyncio


async def test_evidence_and_verification_history_are_linked(db_session: AsyncSession):
    application = Application(name="Farm Guide", slug="farm-guide")
    source = EvidenceSource(
        title="Farm Guide official website",
        url="https://example.com/farm-guide",
        publisher="Farm Guide",
        source_type="official_website",
    )
    db_session.add_all([application, source])
    await db_session.flush()

    evidence = ApplicationEvidence(
        application=application,
        source=source,
        claim_field="availability",
        claim_value="Available in Nigeria",
        is_primary=True,
    )
    review = VerificationReview(
        application=application,
        evidence=evidence,
        status="verified",
        reviewer_name="Reviewer One",
        notes="Confirmed against the official source.",
    )
    db_session.add(review)
    await db_session.commit()

    stored_evidence = await db_session.scalar(select(ApplicationEvidence))
    stored_review = await db_session.scalar(select(VerificationReview))
    assert stored_evidence is not None
    assert stored_review is not None
    assert stored_review.evidence_id == stored_evidence.id


async def test_duplicate_source_url_and_claim_are_rejected(db_session: AsyncSession):
    application = Application(name="Farm Guide", slug="farm-guide")
    source = EvidenceSource(title="Source", url="https://example.com/source", source_type="website")
    db_session.add_all([application, source])
    await db_session.commit()

    db_session.add(EvidenceSource(title="Duplicate", url="https://example.com/source", source_type="website"))
    await db_session.commit()

    application = Application(name="Farm Guide Two", slug="farm-guide-two")
    source = EvidenceSource(title="Source Two", url="https://example.com/source-two", source_type="website")
    db_session.add_all([application, source])
    await db_session.commit()
    evidence = ApplicationEvidence(
        application_id=application.id,
        source_id=source.id,
        claim_field="availability",
        claim_value="Available",
    )
    db_session.add(evidence)
    await db_session.flush()
    db_session.add(
        ApplicationEvidence(
            application_id=application.id,
            source_id=source.id,
            claim_field="availability",
            claim_value="Also available",
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_import_batch_counts_and_row_payload_are_governed(db_session: AsyncSession):
    batch = ImportBatch(
        filename="applications.csv",
        checksum_sha256="a" * 64,
        total_rows=2,
        processed_rows=2,
        successful_rows=1,
        failed_rows=1,
    )
    db_session.add(batch)
    await db_session.flush()

    row = ImportRow(
        batch=batch,
        row_number=1,
        raw_payload={"name": "Farm Guide", "year": "2025"},
        normalized_payload={"name": "Farm Guide", "launch_year": 2025},
        status="validated",
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)

    assert row.raw_payload["year"] == "2025"
    assert row.normalized_payload["launch_year"] == 2025
    stored_row = await db_session.scalar(select(ImportRow).where(ImportRow.id == row.id))
    assert stored_row is not None


async def test_import_batch_rejects_impossible_counts(db_session: AsyncSession):
    db_session.add(
        ImportBatch(
            filename="invalid.csv",
            checksum_sha256="b" * 64,
            total_rows=1,
            processed_rows=2,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_import_batch_checksum_is_idempotent(db_session: AsyncSession):
    db_session.add(
        ImportBatch(
            filename="applications.csv",
            checksum_sha256="d" * 64,
            total_rows=1,
        )
    )
    await db_session.commit()
    db_session.add(
        ImportBatch(
            filename="applications-copy.csv",
            checksum_sha256="d" * 64,
            total_rows=1,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_import_row_number_is_unique_per_batch(db_session: AsyncSession):
    batch = ImportBatch(filename="applications.csv", checksum_sha256="e" * 64, total_rows=2)
    db_session.add(batch)
    await db_session.flush()
    db_session.add_all(
        [
            ImportRow(batch=batch, row_number=1, raw_payload={"name": "One"}),
            ImportRow(batch=batch, row_number=1, raw_payload={"name": "Duplicate"}),
        ]
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_quality_issue_accepts_either_single_parent(db_session: AsyncSession):
    application = Application(name="Farm Guide", slug="farm-guide")
    batch = ImportBatch(filename="applications.csv", checksum_sha256="f" * 64, total_rows=1)
    db_session.add_all([application, batch])
    await db_session.flush()
    row = ImportRow(batch=batch, row_number=1, raw_payload={"name": "Farm Guide"})
    db_session.add(row)
    await db_session.flush()
    db_session.add(
        DataQualityIssue(
            application=application,
            field_name="website_url",
            issue_type="missing",
            severity="warning",
            message="Website URL is missing.",
        )
    )
    db_session.add(
        DataQualityIssue(
            import_row=row,
            field_name="website_url",
            issue_type="missing",
            severity="warning",
            message="Website URL is missing.",
        )
    )
    await db_session.commit()


async def test_quality_issue_requires_exactly_one_parent(db_session: AsyncSession):
    application = Application(name="Farm Guide", slug="farm-guide")
    batch = ImportBatch(filename="applications.csv", checksum_sha256="c" * 64, total_rows=1)
    db_session.add_all([application, batch])
    await db_session.flush()
    row = ImportRow(batch=batch, row_number=1, raw_payload={"name": "Farm Guide"})
    db_session.add(row)
    await db_session.commit()
    application_id = application.id
    row_id = row.id

    db_session.add(
        DataQualityIssue(
            field_name="website_url",
            issue_type="missing",
            severity="warning",
            message="Website URL is missing.",
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

    application = await db_session.get(Application, application_id)
    row = await db_session.get(ImportRow, row_id)
    db_session.add(
        DataQualityIssue(
            application=application,
            import_row=row,
            field_name="website_url",
            issue_type="conflict",
            severity="error",
            message="Both parent references are not allowed.",
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()

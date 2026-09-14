from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.models import (
    AccessType,
    Application,
    ApplicationEvidence,
    Category,
    DataQualityIssue,
    Developer,
    AvailabilityStatus,
    EvidenceSource,
    FocusArea,
    ImportBatch,
    ImportRow,
    Language,
    Location,
    Organisation,
    PhysicalComponent,
    Platform,
    Technology,
    application_categories,
    application_developers,
    application_focus_areas,
    application_languages,
    application_locations,
    application_physical_components,
    application_platforms,
    application_technologies,
)
from app.imports.identifiers import deterministic_id
from app.imports.normalizers import country_to_iso2
from app.imports.preflight import PreflightReport, safe_slug
from app.imports.result import ImportResult
from app.imports.workbook import WorkbookData


REFERENCE_SHEETS = {
    "access_types": (AccessType, "access_type_id"),
    "availability_statuses": (AvailabilityStatus, "availability_status_id"),
    "technologies": (Technology, "technology_id"),
    "categories": (Category, "category_id"),
    "focus_areas": (FocusArea, "focus_area_id"),
    "platforms": (Platform, "platform_id"),
    "languages": (Language, "language_id"),
    "physical_components": (PhysicalComponent, "physical_component_id"),
}

RELATIONSHIP_SHEETS = (
    ("application_devs", "developers", application_developers, "developer_id"),
    ("app_locations", "locations", application_locations, "location_id"),
    ("app_technologies", "technologies", application_technologies, "technology_id"),
    ("app_categories", "categories", application_categories, "category_id"),
    ("app_focus_areas", "focus_areas", application_focus_areas, "focus_area_id"),
    ("app_platforms", "platforms", application_platforms, "platform_id"),
    ("app_languages", "languages", application_languages, "language_id"),
    ("app_physical", "physical_components", application_physical_components, "physical_component_id"),
)


class PilotImporter:
    def __init__(self, session: AsyncSession, workbook: WorkbookData, preflight: PreflightReport) -> None:
        self.session = session
        self.workbook = workbook
        self.preflight = preflight
        self.result = ImportResult(
            checksum_sha256=workbook.checksum_sha256,
            total_rows=len(workbook.sheets.get("applications", [])),
        )
        self.ids: dict[str, dict[str, Any]] = {
            key: {} for key in (
                "locations", "organisations", "developers", "applications",
                "technologies", "categories", "focus_areas", "platforms",
                "languages", "physical_components", "access_types",
                "availability_statuses", "evidence_sources",
            )
        }

    def ensure_preflight_passed(self) -> None:
        if not self.preflight.passed:
            raise ValueError("Workbook preflight failed. Database writes are not allowed.")

    async def find_existing_batch(self) -> ImportBatch | None:
        result = await self.session.execute(
            select(ImportBatch).where(ImportBatch.checksum_sha256 == self.workbook.checksum_sha256)
        )
        return result.scalar_one_or_none()

    async def create_batch(self) -> ImportBatch:
        batch = ImportBatch(
            filename=self.workbook.path.name,
            checksum_sha256=self.workbook.checksum_sha256,
            status="processing",
            total_rows=len(self.workbook.sheets.get("applications", [])),
            processed_rows=0,
            successful_rows=0,
            quarantined_rows=0,
            failed_rows=0,
            started_at=datetime.now(timezone.utc),
            notes="Checkpoint 13 controlled 50-record pilot import",
        )
        self.session.add(batch)
        await self.session.flush()
        self.result.batch_id = str(batch.id)
        return batch

    async def stage_rows(self, batch: ImportBatch) -> dict[str, ImportRow]:
        staged: dict[str, ImportRow] = {}
        applications = self.workbook.sheets.get("applications", [])
        reviews = {str(row.get("application_id")): row for row in self.workbook.sheets.get("quality_review", [])}

        for row_number, application in enumerate(applications, start=2):
            application_id = str(application.get("application_id", ""))
            decision = self.preflight.application_decisions.get(application_id, "rejected")
            raw_payload = dict(application)
            normalized_payload = {
                "source_application_id": application_id,
                "source_record_id": application.get("source_record_id"),
                "name": application.get("name"),
                "website_url": application.get("website_url"),
                "launch_year": application.get("year_of_release"),
                "verification_status": application.get("verification_status") or "unverified",
                "import_decision": decision,
                "quality_review": reviews.get(application_id),
            }
            staged_row = ImportRow(
                batch_id=batch.id,
                row_number=row_number,
                raw_payload=raw_payload,
                normalized_payload=normalized_payload,
                status=decision,
            )
            self.session.add(staged_row)
            staged[application_id] = staged_row

        await self.session.flush()
        return staged

    async def get_or_create_reference(self, model: type[Any], source_id: str, name: str, description: str | None = None) -> Any:
        slug = safe_slug(str(name or source_id), str(source_id))
        result = await self.session.execute(select(model).where(model.slug == slug))
        record = result.scalar_one_or_none()

        if record is None:
            record = model(
                id=deterministic_id(model.__tablename__, source_id),
                name=name,
                slug=slug,
                description=description,
                is_active=True,
            )
            self.session.add(record)
            await self.session.flush()
            self.result.increment_created(model.__tablename__)
        else:
            self.result.increment_reused(model.__tablename__)

        return record

    async def import_locations(self) -> None:
        for row in self.workbook.sheets.get("locations", []):
            source_id = str(row["location_id"])
            slug = safe_slug(str(row["name"]), source_id)
            result = await self.session.execute(select(Location).where(Location.slug == slug))
            location = result.scalar_one_or_none()
            if location is None:
                country_code = None
                if row.get("location_type") == "country":
                    country_code = country_to_iso2(row.get("country") or row.get("name"))
                location = Location(
                    id=deterministic_id("location", source_id),
                    name=str(row["name"]),
                    slug=slug,
                    location_type=str(row.get("location_type") or "unknown"),
                    country_code=country_code,
                    latitude=None,
                    longitude=None,
                    parent_id=None,
                    is_active=True,
                )
                self.session.add(location)
                await self.session.flush()
                self.result.increment_created("locations")
            else:
                self.result.increment_reused("locations")
            self.ids["locations"][source_id] = location.id

    async def import_references(self) -> None:
        for sheet_name, (model, id_column) in REFERENCE_SHEETS.items():
            for row in self.workbook.sheets.get(sheet_name, []):
                source_id = str(row[id_column])
                record = await self.get_or_create_reference(
                    model,
                    source_id,
                    str(row.get("name") or source_id),
                    row.get("description") or row.get("notes"),
                )
                self.ids[sheet_name][source_id] = record.id

    async def import_organisations(self) -> None:
        for row in self.workbook.sheets.get("organisations", []):
            organisation_id = str(row["organisation_id"])
            name = str(row.get("name") or organisation_id)
            slug = safe_slug(name, organisation_id)
            result = await self.session.execute(select(Organisation).where(Organisation.slug == slug))

            record = result.scalar_one_or_none()
            if record is None:
                record = Organisation(
                    id=deterministic_id("organisation", organisation_id),
                    name=name,
                    slug=slug,
                    organisation_type=row.get("organisation_type") or "unknown",
                    headquarters_location_id=self.ids["locations"].get(str(row.get("country_location_id"))),
                    verification_status=row.get("verification_status") or "unverified",
                    is_active=True,
                )
                self.session.add(record)
                await self.session.flush()
                self.result.increment_created("organisations")
            else:
                self.result.increment_reused("organisations")
            self.ids["organisations"][organisation_id] = record.id

    async def import_developers(self) -> None:
        for row in self.workbook.sheets.get("developers", []):
            developer_id = str(row["developer_id"])
            name = str(row.get("display_name") or row.get("name") or developer_id)
            slug = safe_slug(name, developer_id)

            result = await self.session.execute(select(Developer).where(Developer.slug == slug))
            record = result.scalar_one_or_none()
            if record is None:
                record = Developer(
                    id=deterministic_id("developer", developer_id),
                    name=name,
                    slug=slug,
                    developer_type="individual",
                    organisation_id=None,
                    verification_status=row.get("verification_status") or "unverified",
                    is_active=True,
                )
                self.session.add(record)
                await self.session.flush()
                self.result.increment_created("developers")
            else:
                self.result.increment_reused("developers")
            self.ids["developers"][developer_id] = record.id

    async def import_applications(self, staged: dict[str, ImportRow]) -> None:
        self.result.processed_rows = 0
        self.result.successful_rows = 0
        self.result.quarantined_rows = 0
        self.result.failed_rows = 0
        for row in self.workbook.sheets.get("applications", []):
            application_id = str(row["application_id"])
            staged_row = staged[application_id]
            decision = self.preflight.application_decisions.get(application_id, "rejected")
            self.result.processed_rows += 1
            if decision == "quarantined":
                staged_row.status = "quarantined"
                self.result.quarantined_rows += 1
                continue

            organisation_uuid = self.ids["organisations"].get(
                next(
                    (
                        str(rel["organisation_id"])
                        for rel in self.workbook.sheets.get("application_orgs", [])
                        if str(rel.get("application_id")) == application_id and rel.get("is_primary")
                    ),
                    None,
                )
            )
            try:
                async with self.session.begin_nested():
                    application = Application(
                        id=deterministic_id("application", application_id),
                        source_record_id=row.get("source_record_id"),
                        name=row["name"],
                        slug=safe_slug(str(row["name"]), application_id),
                        description=row.get("description"),
                        website_url=row.get("website_url"),
                        launch_year=row.get("year_of_release"),
                        owning_organisation_id=organisation_uuid,
                        access_type_id=self.ids["access_types"].get(str(row.get("access_type_id"))),
                        availability_status_id=self.ids["availability_statuses"].get(str(row.get("availability_status_id"))),
                        verification_status=row.get("verification_status") or "unverified",
                        record_status="pilot",
                        is_active=True,
                    )
                    self.session.add(application)
                    await self.session.flush()
                    self.ids["applications"][application_id] = application.id
                    staged_row.application_id = application.id
                    staged_row.status = "imported"
            except Exception as exc:
                staged_row.status = "failed"
                staged_row.error_message = str(exc)
                self.result.failed_rows += 1
                self.result.errors.append({"application_id": application_id, "message": str(exc)})
            else:
                self.result.successful_rows += 1

    async def import_relationships(self) -> None:
        for sheet_name, mapping_name, table, related_key in RELATIONSHIP_SHEETS:
            for relationship in self.workbook.sheets.get(sheet_name, []):
                application_uuid = self.ids["applications"].get(str(relationship.get("application_id")))
                if application_uuid is None:
                    continue
                target_uuid = self.ids[mapping_name].get(str(relationship.get(related_key)))
                if target_uuid is None:
                    raise ValueError(f"{sheet_name} references an unknown {related_key}")
                values = {
                    "application_id": application_uuid,
                    related_key: target_uuid,
                    "role": relationship.get("role"),
                    "relationship_type": relationship.get("relationship_type"),
                    "is_primary": bool(relationship.get("is_primary") or relationship.get("role") == "primary"),
                    "confidence": relationship.get("confidence"),
                }
                await self.session.execute(pg_insert(table).values(**values).on_conflict_do_nothing())

    async def import_evidence(self) -> None:
        for row in self.workbook.sheets.get("evidence_sources", []):
            evidence_id = str(row["evidence_id"])
            evidence = EvidenceSource(
                id=deterministic_id("evidence", evidence_id),
                title=row.get("citation") or "Dataset evidence",
                url=row.get("url"),
                publisher=None,
                source_type=row.get("source_type") or "dataset_record",
                notes=f"Source record: {row.get('source_record_id')}",
                is_active=True,
            )
            self.session.add(evidence)
            await self.session.flush()
            self.ids["evidence_sources"][evidence_id] = evidence.id

        for row in self.workbook.sheets.get("entity_evidence", []):
            application_uuid = self.ids["applications"].get(str(row.get("entity_id")))
            if application_uuid is None:
                continue
            evidence_uuid = self.ids["evidence_sources"].get(str(row.get("evidence_id")))
            if evidence_uuid is None:
                raise ValueError("Evidence relationship references an unknown source")
            self.session.add(
                ApplicationEvidence(
                    id=deterministic_id("application_evidence", str(row["entity_evidence_id"])),
                    application_id=application_uuid,
                    source_id=evidence_uuid,
                    claim_field="general",
                    claim_value=row.get("evidence_role") or "supports_profile",
                    is_primary=bool(row.get("is_primary")),
                    verification_status="unverified",
                )
            )

    async def import_quality_issues(self, staged: dict[str, ImportRow]) -> None:
        for row in self.workbook.sheets.get("applications", []):
            application_id = str(row["application_id"])
            staged_row = staged.get(application_id)
            if staged_row is None:
                continue
            if self.preflight.application_decisions.get(application_id) == "quarantined":
                issue = DataQualityIssue(
                    application_id=None,
                    import_row_id=staged_row.id,
                    field_name=None,
                    issue_type="manual_review_required",
                    severity="review",
                    status="open",
                    message=f"Application {application_id} was quarantined during preflight.",
                )
                self.session.add(issue)
                continue
            if not row.get("website_url"):
                issue = DataQualityIssue(
                    application_id=self.ids["applications"].get(application_id),
                    import_row_id=None,
                    field_name="website_url",
                    issue_type="missing_value",
                    severity="warning",
                    status="open",
                    message="No website URL was supplied for this application.",
                )
                self.session.add(issue)

    async def finalize_batch(self, batch: ImportBatch) -> None:
        batch.processed_rows = self.result.processed_rows
        batch.successful_rows = self.result.successful_rows
        batch.quarantined_rows = self.result.quarantined_rows
        batch.failed_rows = self.result.failed_rows
        batch.completed_at = datetime.now(timezone.utc)
        batch.status = "completed_with_errors" if self.result.failed_rows > 0 else "completed"
        await self.session.flush()

    async def execute(self) -> ImportResult:
        self.ensure_preflight_passed()
        existing = await self.find_existing_batch()
        if existing is not None:
            raise ValueError(f"This exact workbook has already been registered as batch {existing.id}")

        batch = await self.create_batch()
        staged = await self.stage_rows(batch)

        await self.import_locations()
        await self.import_references()
        await self.import_organisations()
        await self.import_developers()
        await self.import_applications(staged)
        await self.import_relationships()
        await self.import_evidence()
        await self.import_quality_issues(staged)
        await self.finalize_batch(batch)
        return self.result

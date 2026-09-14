from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Application, DataQualityIssue, ImportBatch, ImportRow
from app.db.models.reference import (
    AccessType,
    AvailabilityStatus,
    Category,
    FocusArea,
    Language,
    PhysicalComponent,
    Platform,
    Technology,
)
from app.imports.identifiers import deterministic_id
from app.imports.preflight import PreflightReport, safe_slug
from app.imports.result import ImportResult
from app.imports.workbook import WorkbookData


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
            "locations": {},
            "organisations": {},
            "developers": {},
            "applications": {},
            "technologies": {},
            "categories": {},
            "focus_areas": {},
            "platforms": {},
            "languages": {},
            "physical_components": {},
            "access_types": {},
            "availability_statuses": {},
            "evidence_sources": {},
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
            location_id = str(row["location_id"])
            if location_id in self.ids["locations"]:
                continue
            location = self.session.get(
                type("Location", (), {}),
                None,
            )
            from app.db.models.core import Location

            location = Location(
                id=deterministic_id("location", location_id),
                name=row["name"],
                slug=safe_slug(str(row["name"]), location_id),
                location_type=row.get("location_type", "unknown"),
                country_code=row.get("country_code") or "",
                latitude=None,
                longitude=None,
                parent_id=None,
                is_active=True,
            )
            self.session.add(location)
            await self.session.flush()
            self.ids["locations"][location_id] = location.id

    async def import_references(self) -> None:
        reference_sheets = {
            "access_types": ("access_types", AccessType),
            "availability_statuses": ("availability_statuses", AvailabilityStatus),
            "technologies": ("technologies", Technology),
            "categories": ("categories", Category),
            "focus_areas": ("focus_areas", FocusArea),
            "platforms": ("platforms", Platform),
            "languages": ("languages", Language),
            "physical_components": ("physical_components", PhysicalComponent),
        }

        for key, (sheet_name, model) in reference_sheets.items():
            for row in self.workbook.sheets.get(sheet_name, []):
                source_id = str(row.get(f"{key[:-1]}_id") if key.endswith("s") else row.get("id"))
                name = str(row.get("name") or row.get("technology_name") or row.get("category_name") or row.get("name"))
                description = row.get("description") or row.get("notes")
                record = await self.get_or_create_reference(model, source_id, name, description)
                self.ids[key][row.get(next(iter(row.keys())))] = record.id

    async def import_organisations(self) -> None:
        for row in self.workbook.sheets.get("organisations", []):
            organisation_id = str(row["organisation_id"])
            slug = safe_slug(str(row.get("name") or organisation_id), organisation_id)
            result = await self.session.execute(select(type("Organisation", (), {})).where(type("Organisation", (), {}).slug == slug))
            from app.db.models.core import Organisation

            record = result.scalar_one_or_none()
            if record is None:
                record = Organisation(
                    id=deterministic_id("organisation", organisation_id),
                    name=row.get("name") or organisation_id,
                    slug=slug,
                    organisation_type=row.get("organisation_type") or "unknown",
                    headquarters_location_id=self.ids["locations"].get(row.get("country_location_id")),
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
            slug = safe_slug(str(row.get("name") or developer_id), developer_id)
            from app.db.models.core import Developer

            result = await self.session.execute(select(Developer).where(Developer.slug == slug))
            record = result.scalar_one_or_none()
            if record is None:
                record = Developer(
                    id=deterministic_id("developer", developer_id),
                    name=row.get("name") or developer_id,
                    slug=slug,
                    developer_type=row.get("developer_type") or "team",
                    description=row.get("description"),
                    website_url=row.get("website_url"),
                    email=row.get("email"),
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
        for row in self.workbook.sheets.get("applications", []):
            application_id = str(row["application_id"])
            staged_row = staged.get(application_id)
            decision = self.preflight.application_decisions.get(application_id, "rejected")
            if decision == "quarantined":
                if staged_row is not None:
                    staged_row.status = "quarantined"
                continue

            organisation_uuid = self.ids["organisations"].get(
                next((rel["organisation_id"] for rel in self.workbook.sheets.get("application_orgs", []) if rel.get("application_id") == application_id and rel.get("is_primary")), None)
            )
            access_type_id = self.ids["access_types"].get(row.get("access_type_id"))
            availability_status_id = self.ids["availability_statuses"].get(row.get("availability_status_id"))

            application = Application(
                id=deterministic_id("application", application_id),
                source_record_id=row.get("source_record_id"),
                name=row["name"],
                slug=safe_slug(str(row["name"]), application_id),
                description=row.get("description"),
                website_url=row.get("website_url"),
                launch_year=row.get("year_of_release"),
                owning_organisation_id=organisation_uuid,
                access_type_id=access_type_id,
                availability_status_id=availability_status_id,
                verification_status="unverified" if decision == "accepted_with_warnings" else row.get("verification_status", "unverified"),
                record_status="pilot",
                is_active=True,
            )
            self.session.add(application)
            await self.session.flush()
            self.ids["applications"][application_id] = application.id

            if staged_row is not None:
                staged_row.application_id = application.id
                staged_row.status = "imported"
                self.result.successful_rows += 1

    async def import_relationships(self) -> None:
        relationship_sheets = [
            ("app_technologies", "technologies", "technology_id"),
            ("app_categories", "categories", "category_id"),
            ("app_focus_areas", "focus_areas", "focus_area_id"),
            ("app_platforms", "platforms", "platform_id"),
            ("app_languages", "languages", "language_id"),
            ("app_physical", "physical_components", "physical_component_id"),
        ]
        for sheet_name, mapping_name, related_key in relationship_sheets:
            for relationship in self.workbook.sheets.get(sheet_name, []):
                application_id = relationship.get("application_id")
                application_uuid = self.ids["applications"].get(application_id)
                if application_uuid is None:
                    continue
                target_uuid = self.ids[mapping_name].get(relationship.get(related_key))
                if target_uuid is None:
                    continue
                target_table = self.session.bind.dialect.name
                if target_table == "postgresql":
                    pass
                from app.db.models.associations import application_association_table

                table = {
                    "technologies": "application_technologies",
                    "categories": "application_categories",
                    "focus_areas": "application_focus_areas",
                    "platforms": "application_platforms",
                    "languages": "application_languages",
                    "physical_components": "application_physical_components",
                }[mapping_name]
                if table == "application_technologies":
                    from app.db.models.associations import application_technologies
                    await self.session.execute(
                        application_technologies.insert().values(
                            application_id=application_uuid,
                            technology_id=target_uuid,
                            role=relationship.get("role"),
                            relationship_type=relationship.get("relationship_type"),
                            is_primary=bool(relationship.get("is_primary") or relationship.get("role") == "primary"),
                            confidence=relationship.get("confidence"),
                        )
                    )
                elif table == "application_categories":
                    from app.db.models.associations import application_categories
                    await self.session.execute(
                        application_categories.insert().values(
                            application_id=application_uuid,
                            category_id=target_uuid,
                            role=relationship.get("role"),
                            relationship_type=relationship.get("relationship_type"),
                            is_primary=bool(relationship.get("is_primary") or relationship.get("role") == "primary"),
                            confidence=relationship.get("confidence"),
                        )
                    )
                elif table == "application_focus_areas":
                    from app.db.models.associations import application_focus_areas
                    await self.session.execute(
                        application_focus_areas.insert().values(
                            application_id=application_uuid,
                            focus_area_id=target_uuid,
                            role=relationship.get("role"),
                            relationship_type=relationship.get("relationship_type"),
                            is_primary=bool(relationship.get("is_primary") or relationship.get("role") == "primary"),
                            confidence=relationship.get("confidence"),
                        )
                    )
                elif table == "application_platforms":
                    from app.db.models.associations import application_platforms
                    await self.session.execute(
                        application_platforms.insert().values(
                            application_id=application_uuid,
                            platform_id=target_uuid,
                            role=relationship.get("role"),
                            relationship_type=relationship.get("relationship_type"),
                            is_primary=bool(relationship.get("is_primary") or relationship.get("role") == "primary"),
                            confidence=relationship.get("confidence"),
                        )
                    )
                elif table == "application_languages":
                    from app.db.models.associations import application_languages
                    await self.session.execute(
                        application_languages.insert().values(
                            application_id=application_uuid,
                            language_id=target_uuid,
                            role=relationship.get("role"),
                            relationship_type=relationship.get("relationship_type"),
                            is_primary=bool(relationship.get("is_primary") or relationship.get("role") == "primary"),
                            confidence=relationship.get("confidence"),
                        )
                    )
                elif table == "application_physical_components":
                    from app.db.models.associations import application_physical_components
                    await self.session.execute(
                        application_physical_components.insert().values(
                            application_id=application_uuid,
                            physical_component_id=target_uuid,
                            role=relationship.get("role"),
                            relationship_type=relationship.get("relationship_type"),
                            is_primary=bool(relationship.get("is_primary") or relationship.get("role") == "primary"),
                            confidence=relationship.get("confidence"),
                        )
                    )

    async def import_evidence(self) -> None:
        for row in self.workbook.sheets.get("evidence_sources", []):
            evidence_id = str(row["evidence_id"])
            evidence = type("EvidenceSource", (), {})
            from app.db.models.governance import EvidenceSource

            feature = EvidenceSource(
                id=deterministic_id("evidence", evidence_id),
                title=row.get("citation") or "Dataset evidence",
                url=row.get("url"),
                publisher=None,
                source_type=row.get("source_type") or "dataset_record",
                notes=f"Source record: {row.get('source_record_id')}",
                is_active=True,
            )
            self.session.add(feature)
            await self.session.flush()
            self.ids["evidence_sources"][evidence_id] = feature.id

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

"""Database-independent validation for the pilot workbook."""

from collections import Counter
from dataclasses import asdict, dataclass, field
import re
import unicodedata
from typing import Any

from app.imports.scenarios import (
    ImportDecision,
    READINESS_DECISIONS,
    SCENARIO_BEHAVIOURS,
)
from app.imports.workbook import WorkbookData

PRIMARY_KEYS = {
    "applications": "application_id",
    "organisations": "organisation_id",
    "developers": "developer_id",
    "locations": "location_id",
    "categories": "category_id",
    "focus_areas": "focus_area_id",
    "technologies": "technology_id",
    "platforms": "platform_id",
    "languages": "language_id",
    "access_types": "access_type_id",
    "availability_statuses": "availability_status_id",
    "physical_components": "physical_component_id",
    "evidence_sources": "evidence_id",
    "quality_review": "quality_review_id",
    "import_batches": "import_batch_id",
    "import_records": "import_record_id",
}

REQUIRED_RELATIONSHIP_SHEETS = {
    "application_orgs",
    "application_devs",
    "app_locations",
    "app_categories",
    "app_focus_areas",
    "app_technologies",
    "app_platforms",
    "app_languages",
    "app_physical",
    "entity_evidence",
}
REQUIRED_SHEETS = set(PRIMARY_KEYS) | REQUIRED_RELATIONSHIP_SHEETS

FOREIGN_KEYS = (
    ("applications", "availability_status_id", "availability_statuses", "availability_status_id"),
    ("applications", "access_type_id", "access_types", "access_type_id"),
    ("applications", "country_location_id", "locations", "location_id"),
    ("application_orgs", "application_id", "applications", "application_id"),
    ("application_orgs", "organisation_id", "organisations", "organisation_id"),
    ("application_devs", "application_id", "applications", "application_id"),
    ("application_devs", "developer_id", "developers", "developer_id"),
    ("app_locations", "application_id", "applications", "application_id"),
    ("app_locations", "location_id", "locations", "location_id"),
    ("app_categories", "application_id", "applications", "application_id"),
    ("app_categories", "category_id", "categories", "category_id"),
    ("app_focus_areas", "application_id", "applications", "application_id"),
    ("app_focus_areas", "focus_area_id", "focus_areas", "focus_area_id"),
    ("app_technologies", "application_id", "applications", "application_id"),
    ("app_technologies", "technology_id", "technologies", "technology_id"),
    ("app_platforms", "application_id", "applications", "application_id"),
    ("app_platforms", "platform_id", "platforms", "platform_id"),
    ("app_languages", "application_id", "applications", "application_id"),
    ("app_languages", "language_id", "languages", "language_id"),
    ("app_physical", "application_id", "applications", "application_id"),
    ("app_physical", "physical_component_id", "physical_components", "physical_component_id"),
    ("entity_evidence", "evidence_id", "evidence_sources", "evidence_id"),
    ("quality_review", "application_id", "applications", "application_id"),
    ("import_records", "import_batch_id", "import_batches", "import_batch_id"),
    ("import_records", "application_id", "applications", "application_id"),
)


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    sheet: str | None = None
    row_id: str | None = None


@dataclass
class PreflightReport:
    filename: str
    checksum_sha256: str
    row_counts: dict[str, int]
    decisions: dict[str, int]
    scenario_counts: dict[str, int]
    findings: list[Finding] = field(default_factory=list)
    application_decisions: dict[str, str] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not any(finding.severity == "error" for finding in self.findings)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["passed"] = self.passed
        result["scenario_behaviours"] = SCENARIO_BEHAVIOURS
        return result


def safe_slug(value: str, fallback_id: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    return slug or f"application-{fallback_id.lower()}"


def _blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _ids(rows: list[dict[str, Any]], sheet: str, key: str, findings: list[Finding]) -> set[str]:
    identifiers: list[str] = []
    for row in rows:
        value = row.get(key)
        if _blank(value):
            findings.append(Finding("error", "blank_primary_key", f"{sheet}.{key} is blank", sheet, None))
        else:
            identifiers.append(str(value).strip())
    for identifier, count in Counter(identifiers).items():
        if count > 1:
            findings.append(Finding("error", "duplicate_primary_key", f"{identifier} appears {count} times", sheet, identifier))
    return set(identifiers)


def run_preflight(workbook: WorkbookData) -> PreflightReport:
    sheets = workbook.sheets
    findings: list[Finding] = []
    row_counts = {name: len(rows) for name, rows in sheets.items()}
    decisions: Counter[str] = Counter()
    scenarios: Counter[str] = Counter()
    application_decisions: dict[str, str] = {}

    missing_sheets = sorted(REQUIRED_SHEETS - set(sheets))
    for sheet in missing_sheets:
        findings.append(Finding("error", "missing_sheet", f"Required worksheet is missing: {sheet}"))

    known_ids: dict[str, set[str]] = {}
    for sheet, key in PRIMARY_KEYS.items():
        rows = sheets.get(sheet, [])
        if not rows or key not in rows[0]:
            findings.append(Finding("error", "missing_primary_key_column", f"{sheet}.{key} column is missing", sheet))
        known_ids[sheet] = _ids(rows, sheet, key, findings)

    for child_sheet, child_key, parent_sheet, parent_key in FOREIGN_KEYS:
        for row in sheets.get(child_sheet, []):
            value = row.get(child_key)
            if _blank(value):
                continue
            if str(value).strip() not in known_ids.get(parent_sheet, set()):
                findings.append(
                    Finding(
                        "error",
                        "orphan_foreign_key",
                        f"{child_sheet}.{child_key} references unknown {value}",
                        child_sheet,
                        str(row.get(PRIMARY_KEYS.get(child_sheet, ""), "")),
                    )
                )

    reviews = {str(row.get("application_id")): row for row in sheets.get("quality_review", [])}
    slugs: dict[str, str] = {}
    for application in sheets.get("applications", []):
        application_id = str(application.get("application_id", ""))
        readiness = str(reviews.get(application_id, {}).get("migration_readiness", "")).strip().lower()
        decision = READINESS_DECISIONS.get(readiness, ImportDecision.REJECTED)
        if readiness not in READINESS_DECISIONS:
            findings.append(Finding("error", "unknown_readiness", f"Unknown migration readiness: {readiness or '<blank'}", "quality_review", application_id))
        name = application.get("name")
        if _blank(name):
            decision = ImportDecision.REJECTED
            findings.append(Finding("error", "missing_required_value", "Application name is required", "applications", application_id))
        else:
            slug = safe_slug(str(name), application_id)
            if slug in slugs and slugs[slug] != application_id:
                decision = ImportDecision.QUARANTINED
                scenarios["duplicate_candidate"] += 1
                findings.append(Finding("warning", "duplicate_slug", f"Slug {slug} is shared by applications", "applications", application_id))
            slugs[slug] = application_id
        for optional_field in ("description", "website_url", "year_of_release"):
            if _blank(application.get(optional_field)):
                scenarios["missing_optional_value"] += 1
                findings.append(Finding("warning", "missing_optional_value", f"{optional_field} is missing", "applications", application_id))
        if not _blank(application.get("name")) and not application.get("normalized_name"):
            scenarios["unicode_name"] += 1
        decisions[decision.value] += 1
        application_decision = decision.value
        if application_id:
            application_decisions[application_id] = application_decision

    evidence_rows = sheets.get("evidence_sources", [])
    url_counts = Counter(str(row.get("url")).strip() for row in evidence_rows if not _blank(row.get("url")))
    for count in url_counts.values():
        if count > 1:
            scenarios["shared_evidence_url"] += count
    for row in evidence_rows:
        if _blank(row.get("url")) and not _blank(row.get("citation")):
            scenarios["missing_evidence_url"] += 1
            findings.append(Finding("warning", "missing_evidence_url", "Citation has no URL", "evidence_sources", str(row.get("evidence_id", ""))))

    return PreflightReport(
        filename=workbook.path.name,
        checksum_sha256=workbook.checksum_sha256,
        row_counts=row_counts,
        decisions=dict(decisions),
        scenario_counts=dict(scenarios),
        findings=findings,
        application_decisions=application_decisions,
    )

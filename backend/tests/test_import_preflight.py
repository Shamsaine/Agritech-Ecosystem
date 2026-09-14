"""Tests for database-independent Checkpoint 12 preflight validation."""

from pathlib import Path

from app.imports.preflight import PRIMARY_KEYS, REQUIRED_RELATIONSHIP_SHEETS, run_preflight, safe_slug
from app.imports.workbook import WorkbookData


def workbook_with_application(readiness: str = "ready_with_caveats") -> WorkbookData:
    sheets = {
        "applications": [
            {
                "application_id": "APP-0001",
                "name": "Farm Guide",
                "normalized_name": "farm-guide",
                "description": None,
                "availability_status_id": "AVL-0001",
                "access_type_id": "ACC-0001",
                "country_location_id": "LOC-0001",
                "website_url": None,
                "year_of_release": None,
            }
        ],
        "quality_review": [
            {"quality_review_id": "QR-0001", "application_id": "APP-0001", "migration_readiness": readiness}
        ],
        "availability_statuses": [{"availability_status_id": "AVL-0001"}],
        "access_types": [{"access_type_id": "ACC-0001"}],
        "locations": [{"location_id": "LOC-0001"}],
    }
    for sheet in REQUIRED_RELATIONSHIP_SHEETS:
        sheets.setdefault(sheet, [])
    for sheet, key in PRIMARY_KEYS.items():
        sheets.setdefault(sheet, [{key: f"{key.upper()}-0001"}])
    return WorkbookData(Path("pilot.xlsx"), "checksum", sheets)


def test_unicode_slug_has_fallback():
    assert safe_slug("খামারি", "APP-0014") == "application-app-0014"


def test_caveated_record_is_accepted_with_warnings():
    report = run_preflight(workbook_with_application())
    assert report.passed
    assert report.decisions == {"accepted_with_warnings": 1}


def test_broken_relationship_fails_preflight():
    workbook = workbook_with_application()
    workbook.sheets["applications"][0]["access_type_id"] = "ACC-9999"
    report = run_preflight(workbook)
    assert not report.passed
    assert any(finding.code == "orphan_foreign_key" for finding in report.findings)
"""Checkpoint 12 import decisions and scenario contract."""

from enum import StrEnum


class ImportDecision(StrEnum):
    ACCEPTED = "accepted"
    ACCEPTED_WITH_WARNINGS = "accepted_with_warnings"
    QUARANTINED = "quarantined"
    REJECTED = "rejected"


READINESS_DECISIONS = {
    "ready": ImportDecision.ACCEPTED,
    "ready_with_caveats": ImportDecision.ACCEPTED_WITH_WARNINGS,
    "manual_review": ImportDecision.QUARANTINED,
}


SCENARIO_BEHAVIOURS = {
    "valid_record": "Import into curated tables.",
    "missing_optional_value": "Preserve NULL and create a warning; never invent a value.",
    "missing_required_value": "Reject the record and retain its raw staged row.",
    "duplicate_candidate": "Quarantine for review; never merge automatically.",
    "shared_evidence_url": "Allow the source to support multiple applications.",
    "missing_evidence_url": "Accept citation-only evidence when citation text exists.",
    "unicode_name": "Preserve the name and generate a deterministic fallback slug.",
    "unknown_taxonomy": "Quarantine until mapped to an approved reference value.",
    "broken_foreign_key": "Reject the relationship and report a structural error.",
    "repeat_import": "Use the workbook checksum to prevent duplicate imports.",
}
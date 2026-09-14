# Checkpoint 12 Scenario Matrix

| Scenario | Decision | Behaviour |
| --- | --- | --- |
| Complete record | Accepted | Import normally. |
| Missing optional field | Warning | Preserve `NULL`; never invent a value. |
| Missing required field | Rejected | Retain the staged raw row. |
| Duplicate candidate | Quarantined | Require human review; never merge automatically. |
| Shared evidence URL | Accepted | Allow one source to support multiple applications. |
| Missing evidence URL | Warning | Accept citation-only evidence when citation text exists. |
| Unicode name | Accepted | Preserve the display name and generate a fallback slug. |
| Unknown taxonomy | Quarantined | Require mapping to an approved reference value. |
| Broken relationship | Rejected | Report a structural error and do not insert it. |
| Repeated workbook | Rejected before import | Compare the workbook checksum to prevent duplicates. |

The preflight report may contain warnings and quarantined records while still
passing. Structural errors are the only findings that make `passed` false.
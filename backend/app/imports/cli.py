"""Command-line entry point for read-only workbook preflight."""

import argparse
import json
from pathlib import Path

from app.imports.preflight import run_preflight
from app.imports.workbook import load_workbook_data


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate an agritech pilot workbook without writing to PostgreSQL."
    )
    parser.add_argument("workbook", help="Path to the .xlsx pilot workbook")
    parser.add_argument("--report", type=Path, help="Optional JSON report output path")
    args = parser.parse_args()

    report = run_preflight(load_workbook_data(args.workbook))
    rendered = json.dumps(report.to_dict(), indent=2, ensure_ascii=False, default=str)
    print(rendered)

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered + "\n", encoding="utf-8")

    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
import argparse
import asyncio
import json
import sys

from app.db.session import AsyncSessionFactory
from app.imports.preflight import run_preflight
from app.imports.service import PilotImporter
from app.imports.workbook import load_workbook_data


async def run_import(workbook_path: str, commit: bool) -> int:
    workbook = load_workbook_data(workbook_path)
    preflight = run_preflight(workbook)

    if not preflight.passed:
        print(json.dumps(preflight.to_dict(), indent=2, ensure_ascii=False, default=str))
        return 1

    if not commit:
        print("Preflight passed. No database writes performed.")
        return 0

    async with AsyncSessionFactory() as session:
        try:
            importer = PilotImporter(session, workbook, preflight)
            result = await importer.execute()
            await session.commit()
            print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False, default=str))
            return 0
        except Exception:
            await session.rollback()
            raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbook")
    parser.add_argument("--commit", action="store_true", help="Write validated records to PostgreSQL")
    args = parser.parse_args()
    loop_factory = asyncio.SelectorEventLoop if sys.platform == "win32" else None
    return asyncio.run(run_import(args.workbook, args.commit), loop_factory=loop_factory)


if __name__ == "__main__":
    raise SystemExit(main())

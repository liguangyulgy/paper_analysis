from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.storage.database import connect, get_database_path, init_database
from src.storage.repository import PaperRepository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="paper-analysis")
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="SQLite database path. Defaults to PAPER_ANALYSIS_DB or data/processed/paper_analysis.sqlite.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize project resources.")
    init_subparsers = init_parser.add_subparsers(dest="init_command", required=True)
    init_subparsers.add_parser("db", help="Initialize the SQLite database schema.")

    status_parser = subparsers.add_parser("status", help="Show database status.")
    status_subparsers = status_parser.add_subparsers(dest="status_command", required=True)
    status_summary = status_subparsers.add_parser("summary", help="Show paper status summary.")
    status_summary.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init" and args.init_command == "db":
        db_path = init_database(args.db)
        print(f"Initialized database: {db_path}")
        return 0

    if args.command == "status" and args.status_command == "summary":
        db_path = get_database_path(args.db)
        if not db_path.exists():
            parser.error(f"database does not exist: {db_path}. Run `python -m src.cli init db` first.")
        with connect(db_path) as connection:
            summary = PaperRepository(connection).get_status_summary()
        if args.json:
            print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            _print_status_summary(summary, db_path)
        return 0

    parser.error("unknown command")
    return 2


def _print_status_summary(summary: dict[str, Any], db_path: Path) -> None:
    print(f"Database: {db_path}")
    print(f"Total papers: {summary['total_papers']}")
    for field in (
        "abstract_status",
        "fulltext_status",
        "parse_status",
        "analysis_status",
        "reference_value",
        "review_status",
        "region_relevance",
    ):
        values = summary[field]
        rendered = ", ".join(f"{key}={value}" for key, value in sorted(values.items()))
        print(f"{field}: {rendered or '(none)'}")


if __name__ == "__main__":
    raise SystemExit(main())

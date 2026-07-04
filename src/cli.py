from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.collectors.pubmed import PubMedCollector
from src.reports.simple import export_simple_report
from src.storage.database import connect, get_database_path, init_database
from src.storage.repository import PaperRepository
from src.utils.http import inject_system_truststore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="paper-analysis")
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="SQLite database path. Defaults to PAPER_ANALYSIS_DB or data/processed/paper_analysis.sqlite.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    collect_parser = subparsers.add_parser("collect", help="Collect paper metadata.")
    collect_subparsers = collect_parser.add_subparsers(dest="collect_command", required=True)
    collect_abstracts = collect_subparsers.add_parser("abstracts", help="Collect paper abstracts.")
    collect_abstracts.add_argument("--source", choices=["pubmed"], required=True)
    collect_abstracts.add_argument("--query", required=True)
    collect_abstracts.add_argument("--limit", type=int, default=20)

    init_parser = subparsers.add_parser("init", help="Initialize project resources.")
    init_subparsers = init_parser.add_subparsers(dest="init_command", required=True)
    init_subparsers.add_parser("db", help="Initialize the SQLite database schema.")

    status_parser = subparsers.add_parser("status", help="Show database status.")
    status_subparsers = status_parser.add_subparsers(dest="status_command", required=True)
    status_summary = status_subparsers.add_parser("summary", help="Show paper status summary.")
    status_summary.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    status_keywords = status_subparsers.add_parser(
        "keywords", help="Show keyword hit counts grouped like tags."
    )
    status_keywords.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    report_parser = subparsers.add_parser("report", help="Export reports.")
    report_subparsers = report_parser.add_subparsers(dest="report_command", required=True)
    report_simple = report_subparsers.add_parser("simple", help="Export a simple paper list.")
    report_simple.add_argument("--format", choices=["csv", "markdown"], default="csv")
    report_simple.add_argument("--output", type=Path, default=None)

    return parser


def main(argv: list[str] | None = None) -> int:
    inject_system_truststore()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init" and args.init_command == "db":
        db_path = init_database(args.db)
        print(f"Initialized database: {db_path}")
        return 0

    if args.command == "collect" and args.collect_command == "abstracts":
        db_path = init_database(args.db)
        if args.source != "pubmed":
            parser.error("only --source pubmed is currently implemented")

        collector = PubMedCollector()
        result = collector.collect_by_keyword(args.query, limit=args.limit)
        created_count = 0
        updated_count = 0
        with connect(db_path) as connection:
            repository = PaperRepository(connection)
            for paper in result.papers:
                match = repository.upsert_paper(
                    paper,
                    source={
                        "source": "pubmed",
                        "source_record_id": paper.get("pmid"),
                        "query_keyword": args.query,
                        "source_url": _pubmed_url(paper.get("pmid")),
                    },
                )
                if match.created:
                    created_count += 1
                else:
                    updated_count += 1

        print(
            "Collected PubMed abstracts: "
            f"found={len(result.pmids)}, parsed={len(result.papers)}, "
            f"created={created_count}, updated={updated_count}"
        )
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

    if args.command == "status" and args.status_command == "keywords":
        db_path = get_database_path(args.db)
        if not db_path.exists():
            parser.error(f"database does not exist: {db_path}. Run `python -m src.cli init db` first.")
        with connect(db_path) as connection:
            rows = PaperRepository(connection).get_keyword_summary()
        summary = [
            {
                "keyword_group": row["keyword_group"],
                "keyword": row["keyword"],
                "paper_count": row["paper_count"],
            }
            for row in rows
        ]
        if args.json:
            print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            _print_keyword_summary(summary, db_path)
        return 0

    if args.command == "report" and args.report_command == "simple":
        db_path = init_database(args.db)
        if not db_path.exists():
            parser.error(f"database does not exist: {db_path}. Run `python -m src.cli init db` first.")
        output_path = args.output or _default_simple_report_path(args.format)
        with connect(db_path) as connection:
            path = export_simple_report(connection, output_path, output_format=args.format)
        print(f"Exported simple report: {path}")
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


def _print_keyword_summary(summary: list[dict[str, Any]], db_path: Path) -> None:
    print(f"Database: {db_path}")
    if not summary:
        print("Keyword hits: (none)")
        return
    print("Keyword hits:")
    for row in summary:
        print(f"- {row['keyword_group']}:{row['keyword']} = {row['paper_count']}")


def _pubmed_url(pmid: object | None) -> str | None:
    if not pmid:
        return None
    return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"


def _default_simple_report_path(output_format: str) -> Path:
    extension = "md" if output_format == "markdown" else "csv"
    return Path("data") / "exports" / f"simple_report.{extension}"


if __name__ == "__main__":
    raise SystemExit(main())

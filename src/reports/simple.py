from __future__ import annotations

import csv
from pathlib import Path


SIMPLE_REPORT_COLUMNS = [
    "id",
    "title",
    "year",
    "journal",
    "doi",
    "pmid",
    "pmcid",
    "abstract_status",
    "evidence_level",
    "reference_value",
    "review_status",
    "region_relevance",
    "keyword_tags",
]


def export_simple_report(connection, output_path: str | Path, *, output_format: str = "csv") -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = _simple_report_rows(connection)

    if output_format == "csv":
        _write_csv(path, rows)
    elif output_format == "markdown":
        _write_markdown(path, rows)
    else:
        raise ValueError(f"unsupported report format: {output_format}")
    return path


def _simple_report_rows(connection) -> list[dict[str, object]]:
    rows = connection.execute(
        """
        SELECT
          p.id,
          p.title,
          p.year,
          p.journal,
          p.doi,
          p.pmid,
          p.pmcid,
          p.abstract_status,
          p.evidence_level,
          p.reference_value,
          p.review_status,
          p.region_relevance,
          COALESCE(
            GROUP_CONCAT(DISTINCT kh.keyword_group || ':' || kh.keyword),
            ''
          ) AS keyword_tags
        FROM papers p
        LEFT JOIN paper_keyword_hits kh ON kh.paper_id = p.id
        GROUP BY p.id
        ORDER BY COALESCE(p.year, 0) DESC, p.id DESC
        """
    ).fetchall()
    return [{column: row[column] for column in SIMPLE_REPORT_COLUMNS} for row in rows]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=SIMPLE_REPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        output.write("| " + " | ".join(SIMPLE_REPORT_COLUMNS) + " |\n")
        output.write("| " + " | ".join(["---"] * len(SIMPLE_REPORT_COLUMNS)) + " |\n")
        for row in rows:
            output.write("| " + " | ".join(_markdown_cell(row[column]) for column in SIMPLE_REPORT_COLUMNS) + " |\n")


def _markdown_cell(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")

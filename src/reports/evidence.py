from __future__ import annotations

import csv
from pathlib import Path


EVIDENCE_REPORT_COLUMNS = [
    "bucket",
    "paper_id",
    "title",
    "year",
    "journal",
    "doi",
    "pmid",
    "evidence_type",
    "evidence_level",
    "evidence_sentence",
    "section_name",
    "needs_review",
]


def export_evidence_report(connection, output_path: str | Path, *, output_format: str = "csv") -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = _evidence_report_rows(connection)
    if output_format == "csv":
        _write_csv(path, rows)
    elif output_format == "markdown":
        _write_markdown(path, rows)
    else:
        raise ValueError(f"unsupported report format: {output_format}")
    return path


def _evidence_report_rows(connection) -> list[dict[str, object]]:
    rows = connection.execute(
        """
        SELECT
          p.id AS paper_id,
          p.title,
          p.year,
          p.journal,
          p.doi,
          p.pmid,
          e.evidence_type,
          e.evidence_level,
          e.evidence_sentence,
          e.section_name,
          e.needs_review
        FROM paper_evidence e
        JOIN papers p ON p.id = e.paper_id
        ORDER BY
          CASE e.evidence_type
            WHEN 'supplier_usage' THEN 1
            WHEN 'model_usage' THEN 2
            WHEN 'author_affiliation' THEN 3
            WHEN 'keyword_only' THEN 4
            ELSE 5
          END,
          COALESCE(p.year, 0) DESC,
          p.id DESC
        """
    ).fetchall()
    return [
        {
            "bucket": _bucket(row["evidence_type"]),
            **{column: row[column] for column in EVIDENCE_REPORT_COLUMNS if column not in {"bucket"}},
        }
        for row in rows
    ]


def _bucket(evidence_type: str) -> str:
    return {
        "supplier_usage": "明确使用 genOway 模型候选",
        "model_usage": "需要全文确认",
        "author_affiliation": "genOway 作者/合作线索",
        "keyword_only": "仅模型关键词线索",
    }.get(evidence_type, "其他线索")


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=EVIDENCE_REPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        output.write("| " + " | ".join(EVIDENCE_REPORT_COLUMNS) + " |\n")
        output.write("| " + " | ".join(["---"] * len(EVIDENCE_REPORT_COLUMNS)) + " |\n")
        for row in rows:
            output.write("| " + " | ".join(_markdown_cell(row[column]) for column in EVIDENCE_REPORT_COLUMNS) + " |\n")


def _markdown_cell(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")

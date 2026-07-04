from __future__ import annotations

from src.analysis.keywords import KeywordRule
from src.reports.evidence import export_evidence_report
from src.reports.simple import export_simple_report
from src.storage.database import connect, init_database
from src.storage.repository import PaperRepository


def make_report_repository(tmp_path):
    db_path = tmp_path / "paper_analysis.sqlite"
    init_database(db_path)
    connection = connect(db_path)
    repository = PaperRepository(
        connection,
        keyword_rules=[
            KeywordRule(keyword="genOway", keyword_group="company", source_config="test"),
            KeywordRule(keyword="BRGSF", keyword_group="model", source_config="test"),
        ],
    )
    return connection, repository


def test_export_simple_report_csv_includes_keyword_tags(tmp_path):
    connection, repository = make_report_repository(tmp_path)
    try:
        repository.upsert_paper(
            {
                "title": "BRGSF mouse model from genOway",
                "doi": "10.1/report",
                "pmid": "123",
                "year": 2025,
                "affiliations": "genOway, Lyon, France.",
            }
        )
        output_path = tmp_path / "report.csv"

        export_simple_report(connection, output_path, output_format="csv")
        content = output_path.read_text(encoding="utf-8-sig")

        assert "title,year,journal" in content
        assert "genoway_evidence" in content
        assert "BRGSF mouse model from genOway" in content
        assert "genOway, Lyon, France." in content
        assert "company:genOway" in content
        assert "model:BRGSF" in content
    finally:
        connection.close()


def test_export_simple_report_markdown(tmp_path):
    connection, repository = make_report_repository(tmp_path)
    try:
        repository.upsert_paper({"title": "Plain paper", "doi": "10.1/markdown"})
        output_path = tmp_path / "report.md"

        export_simple_report(connection, output_path, output_format="markdown")
        content = output_path.read_text(encoding="utf-8")

        assert "| id | title | year |" in content
        assert "| Plain paper |" in content
    finally:
        connection.close()


def test_export_evidence_report_separates_affiliation_bucket(tmp_path):
    connection, repository = make_report_repository(tmp_path)
    try:
        repository.upsert_paper(
            {
                "title": "A mouse model paper",
                "doi": "10.1/evidence",
                "affiliations": "genOway, Lyon, France.",
            }
        )
        output_path = tmp_path / "evidence.csv"

        export_evidence_report(connection, output_path, output_format="csv")
        content = output_path.read_text(encoding="utf-8-sig")

        assert "genOway 作者/合作线索" in content
        assert "author_affiliation" in content
        assert "supplier_usage" not in content
    finally:
        connection.close()

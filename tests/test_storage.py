from __future__ import annotations

import sqlite3

from src.analysis.keywords import KeywordRule
from src.storage.database import connect, init_database
from src.storage.repository import PaperRepository


def make_repository(tmp_path):
    db_path = tmp_path / "paper_analysis.sqlite"
    init_database(db_path)
    connection = connect(db_path)
    return connection, PaperRepository(connection)


def test_init_database_creates_core_tables(tmp_path):
    db_path = tmp_path / "paper_analysis.sqlite"
    init_database(db_path)

    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        ).fetchall()

    table_names = {row[0] for row in rows}
    assert "papers" in table_names
    assert "paper_sources" in table_names
    assert "paper_keyword_hits" in table_names
    assert "paper_status_events" in table_names


def test_upsert_paper_deduplicates_by_doi(tmp_path):
    connection, repository = make_repository(tmp_path)
    try:
        first = repository.upsert_paper(
            {
                "title": "A Humanized Mouse Model Study",
                "doi": "10.1234/example",
                "abstract_status": "fetched",
            },
            source={"source": "pubmed", "source_record_id": "123"},
        )
        second = repository.upsert_paper(
            {
                "title": "A Humanized Mouse Model Study",
                "doi": "10.1234/example",
                "journal": "Example Journal",
            },
            source={"source": "crossref", "source_record_id": "10.1234/example"},
        )

        assert first.created is True
        assert second.created is False
        assert first.paper_id == second.paper_id

        count = connection.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
        source_count = connection.execute("SELECT COUNT(*) FROM paper_sources").fetchone()[0]
        paper = repository.get_paper(first.paper_id)

        assert count == 1
        assert source_count == 2
        assert paper["journal"] == "Example Journal"
    finally:
        connection.close()


def test_status_summary_counts_current_states(tmp_path):
    connection, repository = make_repository(tmp_path)
    try:
        repository.upsert_paper({"title": "Paper One", "doi": "10.1/one"})
        repository.upsert_paper(
            {
                "title": "Paper Two",
                "doi": "10.1/two",
                "abstract_status": "fetched",
                "region_relevance": "china_domestic",
            }
        )

        summary = repository.get_status_summary()

        assert summary["total_papers"] == 2
        assert summary["abstract_status"]["not_checked"] == 1
        assert summary["abstract_status"]["fetched"] == 1
        assert summary["region_relevance"]["china_domestic"] == 1
    finally:
        connection.close()


def test_manual_override_protects_manual_fields_from_automatic_updates(tmp_path):
    connection, repository = make_repository(tmp_path)
    try:
        match = repository.upsert_paper({"title": "Manual Review Paper", "doi": "10.1/manual"})
        repository.update_manual_fields(
            match.paper_id,
            {"reference_value": "high", "review_status": "confirmed"},
            reviewer="tester",
            note="Confirmed as useful.",
        )
        repository.update_automatic_fields(
            match.paper_id,
            {
                "reference_value": "low",
                "review_status": "needs_review",
                "abstract_status": "fetched",
            },
            reason="automatic analysis rerun",
        )

        paper = repository.get_paper(match.paper_id)
        events = connection.execute(
            "SELECT field_name, new_value FROM paper_status_events WHERE paper_id = ?",
            (match.paper_id,),
        ).fetchall()

        assert paper["manual_override"] == 1
        assert paper["reference_value"] == "high"
        assert paper["review_status"] == "confirmed"
        assert paper["abstract_status"] == "fetched"
        assert ("abstract_status", "fetched") in [(row[0], row[1]) for row in events]
    finally:
        connection.close()


def test_upsert_paper_records_keyword_hits_from_title_and_abstract(tmp_path):
    rules = [
        KeywordRule(keyword="BRGSF", keyword_group="model", source_config="test"),
        KeywordRule(keyword="genOway", keyword_group="company", source_config="test"),
    ]
    db_path = tmp_path / "paper_analysis.sqlite"
    init_database(db_path)
    connection = connect(db_path)
    repository = PaperRepository(connection, keyword_rules=rules)
    try:
        match = repository.upsert_paper(
            {
                "title": "BRGSF mouse model study",
                "doi": "10.1/tags",
                "abstract": "This model was supplied by genOway for efficacy testing.",
            }
        )

        hits = repository.list_keyword_hits(match.paper_id)
        summary = repository.get_keyword_summary()

        assert [(row["keyword_group"], row["keyword"], row["matched_field"]) for row in hits] == [
            ("company", "genOway", "abstract"),
            ("model", "BRGSF", "title"),
        ]
        assert [(row["keyword_group"], row["keyword"], row["paper_count"]) for row in summary] == [
            ("company", "genOway", 1),
            ("model", "BRGSF", 1),
        ]
    finally:
        connection.close()


def test_keyword_hits_refresh_when_duplicate_adds_abstract(tmp_path):
    rules = [KeywordRule(keyword="genOway", keyword_group="company", source_config="test")]
    db_path = tmp_path / "paper_analysis.sqlite"
    init_database(db_path)
    connection = connect(db_path)
    repository = PaperRepository(connection, keyword_rules=rules)
    try:
        first = repository.upsert_paper({"title": "A model paper", "doi": "10.1/refresh"})
        assert repository.list_keyword_hits(first.paper_id) == []

        second = repository.upsert_paper(
            {
                "title": "A model paper",
                "doi": "10.1/refresh",
                "abstract": "The model was generated by genOway.",
            }
        )

        hits = repository.list_keyword_hits(second.paper_id)
        assert first.paper_id == second.paper_id
        assert len(hits) == 1
        assert hits[0]["keyword"] == "genOway"
        assert hits[0]["matched_field"] == "abstract"
    finally:
        connection.close()

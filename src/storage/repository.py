from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from src.analysis.keywords import KeywordRule, match_keywords
from src.domain.status import validate_status_fields
from src.utils.normalizers import normalize_doi, normalize_pmcid, normalize_pmid, normalize_title

MANUAL_PROTECTED_FIELDS = {
    "evidence_level",
    "reference_value",
    "review_status",
    "region_relevance",
    "model_name",
    "model_type",
    "target",
    "disease_area",
    "application_scenario",
}


@dataclass(frozen=True)
class PaperMatch:
    paper_id: int
    created: bool


class PaperRepository:
    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        keyword_rules: list[KeywordRule] | None = None,
    ) -> None:
        self.connection = connection
        self.keyword_rules = keyword_rules

    def upsert_paper(self, paper: dict[str, Any], source: dict[str, Any] | None = None) -> PaperMatch:
        paper = self._normalize_paper_identifiers(paper)
        self._validate_paper_statuses(paper)

        title = (paper.get("title") or "").strip()
        if not title:
            raise ValueError("paper title is required")

        existing = self.find_existing_paper(
            doi=paper.get("doi"),
            pmid=paper.get("pmid"),
            pmcid=paper.get("pmcid"),
            title=title,
            year=paper.get("year"),
        )
        if existing is not None:
            paper_id = int(existing["id"])
            self._merge_paper_fields(paper_id, paper)
            created = False
        else:
            paper_id = self._insert_paper(paper)
            created = True

        if source:
            self.add_source(paper_id, source)
        self.refresh_keyword_hits(paper_id)
        return PaperMatch(paper_id=paper_id, created=created)

    def find_existing_paper(
        self,
        *,
        doi: str | None = None,
        pmid: str | None = None,
        pmcid: str | None = None,
        title: str | None = None,
        year: int | None = None,
    ) -> sqlite3.Row | None:
        doi = normalize_doi(doi)
        pmid = normalize_pmid(pmid)
        pmcid = normalize_pmcid(pmcid)
        for field_name, value in (("doi", doi), ("pmid", pmid), ("pmcid", pmcid)):
            if value:
                row = self.connection.execute(
                    f"SELECT * FROM papers WHERE {field_name} = ?", (value,)
                ).fetchone()
                if row:
                    return row

        if title:
            normalized = normalize_title(title)
            if year is None:
                return self.connection.execute(
                    "SELECT * FROM papers WHERE normalized_title = ? ORDER BY id LIMIT 1",
                    (normalized,),
                ).fetchone()
            return self.connection.execute(
                """
                SELECT * FROM papers
                WHERE normalized_title = ? AND (year = ? OR year IS NULL)
                ORDER BY id
                LIMIT 1
                """,
                (normalized, year),
            ).fetchone()
        return None

    def add_source(self, paper_id: int, source: dict[str, Any]) -> None:
        self.connection.execute(
            """
            INSERT OR IGNORE INTO paper_sources (
              paper_id, source, source_record_id, query_keyword, source_url, raw_json_path
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                paper_id,
                source.get("source"),
                source.get("source_record_id"),
                source.get("query_keyword"),
                source.get("source_url"),
                source.get("raw_json_path"),
            ),
        )

    def refresh_keyword_hits(self, paper_id: int) -> None:
        paper = self.get_paper(paper_id)
        if paper is None:
            raise ValueError(f"paper not found: {paper_id}")

        hits = match_keywords(
            {
                "title": paper["title"],
                "abstract": paper["abstract"],
                "affiliations": paper["affiliations"],
            },
            self.keyword_rules,
        )
        self.connection.execute("DELETE FROM paper_keyword_hits WHERE paper_id = ?", (paper_id,))
        self.connection.executemany(
            """
            INSERT OR IGNORE INTO paper_keyword_hits (
              paper_id, keyword, keyword_group, matched_text, matched_field,
              evidence_sentence, source_config
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    paper_id,
                    hit.keyword,
                    hit.keyword_group,
                    hit.matched_text,
                    hit.matched_field,
                    hit.evidence_sentence,
                    hit.source_config,
                )
                for hit in hits
            ],
        )

    def list_keyword_hits(self, paper_id: int) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT *
            FROM paper_keyword_hits
            WHERE paper_id = ?
            ORDER BY keyword_group, keyword, matched_field
            """,
            (paper_id,),
        ).fetchall()

    def get_keyword_summary(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT keyword_group, keyword, COUNT(DISTINCT paper_id) AS paper_count
            FROM paper_keyword_hits
            GROUP BY keyword_group, keyword
            ORDER BY paper_count DESC, keyword_group, keyword
            """
        ).fetchall()

    def update_manual_fields(
        self,
        paper_id: int,
        fields: dict[str, Any],
        *,
        reviewer: str | None = None,
        note: str | None = None,
    ) -> None:
        allowed = MANUAL_PROTECTED_FIELDS | {"language"}
        updates = {key: value for key, value in fields.items() if key in allowed}
        validate_status_fields(updates)
        if not updates and not note:
            return

        if updates:
            self._update_fields(
                paper_id,
                {**updates, "manual_override": 1},
                changed_by=reviewer or "manual",
                change_source="manual",
                reason=note,
                respect_manual_override=False,
            )
        if note:
            self.connection.execute(
                "INSERT INTO manual_notes (paper_id, note, reviewer) VALUES (?, ?, ?)",
                (paper_id, note, reviewer),
            )

    def update_automatic_fields(
        self,
        paper_id: int,
        fields: dict[str, Any],
        *,
        reason: str | None = None,
    ) -> None:
        row = self.get_paper(paper_id)
        if row is None:
            raise ValueError(f"paper not found: {paper_id}")

        validate_status_fields(fields)

        blocked = set()
        if row["manual_override"]:
            blocked = MANUAL_PROTECTED_FIELDS

        updates = {key: value for key, value in fields.items() if key not in blocked}
        self._update_fields(
            paper_id,
            updates,
            changed_by="system",
            change_source="automatic",
            reason=reason,
            respect_manual_override=True,
        )

    def get_paper(self, paper_id: int) -> sqlite3.Row | None:
        return self.connection.execute("SELECT * FROM papers WHERE id = ?", (paper_id,)).fetchone()

    def get_status_summary(self) -> dict[str, Any]:
        total = self.connection.execute("SELECT COUNT(*) AS count FROM papers").fetchone()["count"]
        fields = [
            "abstract_status",
            "fulltext_status",
            "parse_status",
            "analysis_status",
            "reference_value",
            "review_status",
            "region_relevance",
        ]
        summary: dict[str, Any] = {"total_papers": total}
        for field in fields:
            rows = self.connection.execute(
                f"SELECT {field} AS value, COUNT(*) AS count FROM papers GROUP BY {field}"
            ).fetchall()
            summary[field] = {row["value"]: row["count"] for row in rows}
        return summary

    def _insert_paper(self, paper: dict[str, Any]) -> int:
        normalized_title = normalize_title(paper["title"])
        cursor = self.connection.execute(
            """
            INSERT INTO papers (
              title, normalized_title, abstract, authors, affiliations, journal, publication_date, year,
              doi, pmid, pmcid, language, region_relevance, abstract_status,
              evidence_level, manual_upload
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                paper["title"].strip(),
                normalized_title,
                paper.get("abstract"),
                paper.get("authors"),
                paper.get("affiliations"),
                paper.get("journal"),
                paper.get("publication_date"),
                paper.get("year"),
                paper.get("doi"),
                paper.get("pmid"),
                paper.get("pmcid"),
                paper.get("language", "unknown"),
                paper.get("region_relevance", "unknown"),
                paper.get("abstract_status", "not_checked"),
                paper.get("evidence_level", "unknown"),
                int(bool(paper.get("manual_upload", False))),
            ),
        )
        paper_id = int(cursor.lastrowid)
        self._record_event(paper_id, "discovery_status", None, "discovered", "system", "insert", None)
        return paper_id

    def _merge_paper_fields(self, paper_id: int, paper: dict[str, Any]) -> None:
        candidate_fields = {
            "abstract": paper.get("abstract"),
            "authors": paper.get("authors"),
            "affiliations": paper.get("affiliations"),
            "journal": paper.get("journal"),
            "publication_date": paper.get("publication_date"),
            "year": paper.get("year"),
            "doi": paper.get("doi"),
            "pmid": paper.get("pmid"),
            "pmcid": paper.get("pmcid"),
            "language": paper.get("language"),
            "region_relevance": paper.get("region_relevance"),
            "abstract_status": paper.get("abstract_status"),
        }
        candidate_fields = self._normalize_paper_identifiers(candidate_fields)
        self._validate_paper_statuses(candidate_fields)
        row = self.get_paper(paper_id)
        if row is None:
            raise ValueError(f"paper not found: {paper_id}")
        updates = {
            key: value
            for key, value in candidate_fields.items()
            if value not in (None, "") and row[key] in (None, "", "unknown", "not_checked")
        }
        self._update_fields(
            paper_id,
            updates,
            changed_by="system",
            change_source="merge",
            reason="merged metadata from duplicate record",
            respect_manual_override=True,
        )

    def _update_fields(
        self,
        paper_id: int,
        fields: dict[str, Any],
        *,
        changed_by: str,
        change_source: str,
        reason: str | None,
        respect_manual_override: bool,
    ) -> None:
        if not fields:
            return
        validate_status_fields(fields)
        row = self.get_paper(paper_id)
        if row is None:
            raise ValueError(f"paper not found: {paper_id}")

        updates: dict[str, Any] = {}
        for field, value in fields.items():
            if field not in row.keys():
                raise ValueError(f"unknown paper field: {field}")
            if respect_manual_override and row["manual_override"] and field in MANUAL_PROTECTED_FIELDS:
                continue
            if row[field] != value:
                updates[field] = value

        if not updates:
            return

        assignments = ", ".join(f"{field} = ?" for field in updates)
        values = list(updates.values())
        values.append(paper_id)
        self.connection.execute(
            f"UPDATE papers SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values,
        )
        for field, new_value in updates.items():
            self._record_event(
                paper_id,
                field,
                row[field],
                new_value,
                changed_by,
                change_source,
                reason,
            )

    def _normalize_paper_identifiers(self, paper: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(paper)
        if "doi" in normalized:
            normalized["doi"] = normalize_doi(normalized["doi"])
        if "pmid" in normalized:
            normalized["pmid"] = normalize_pmid(normalized["pmid"])
        if "pmcid" in normalized:
            normalized["pmcid"] = normalize_pmcid(normalized["pmcid"])
        return normalized

    def _validate_paper_statuses(self, paper: dict[str, Any]) -> None:
        validate_status_fields(
            {
                key: value
                for key, value in paper.items()
                if key
                in {
                    "discovery_status",
                    "abstract_status",
                    "fulltext_status",
                    "parse_status",
                    "analysis_status",
                    "evidence_level",
                    "reference_value",
                    "review_status",
                    "language",
                    "region_relevance",
                }
            }
        )

    def _record_event(
        self,
        paper_id: int,
        field_name: str,
        old_value: Any,
        new_value: Any,
        changed_by: str,
        change_source: str,
        reason: str | None,
    ) -> None:
        self.connection.execute(
            """
            INSERT INTO paper_status_events (
              paper_id, field_name, old_value, new_value, changed_by, change_source, reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                paper_id,
                field_name,
                None if old_value is None else str(old_value),
                None if new_value is None else str(new_value),
                changed_by,
                change_source,
                reason,
            ),
        )

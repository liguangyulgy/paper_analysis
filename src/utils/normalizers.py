from __future__ import annotations

import re


TRAILING_IDENTIFIER_PUNCTUATION = " .;,)］】"


def normalize_doi(value: object | None) -> str | None:
    if value is None:
        return None
    doi = str(value).strip()
    if not doi:
        return None

    doi = re.sub(r"^\s*doi\s*:\s*", "", doi, flags=re.IGNORECASE)
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    doi = doi.strip().strip(TRAILING_IDENTIFIER_PUNCTUATION).casefold()
    return doi or None


def normalize_pmid(value: object | None) -> str | None:
    if value is None:
        return None
    pmid = str(value).strip()
    if not pmid:
        return None
    pmid = re.sub(r"^\s*pmid\s*:\s*", "", pmid, flags=re.IGNORECASE)
    pmid = re.sub(r"\D", "", pmid)
    return pmid or None


def normalize_pmcid(value: object | None) -> str | None:
    if value is None:
        return None
    pmcid = str(value).strip()
    if not pmcid:
        return None
    pmcid = re.sub(r"^\s*pmcid\s*:\s*", "", pmcid, flags=re.IGNORECASE)
    pmcid = pmcid.strip().strip(TRAILING_IDENTIFIER_PUNCTUATION).upper()
    if pmcid and not pmcid.startswith("PMC") and pmcid.isdigit():
        pmcid = f"PMC{pmcid}"
    return pmcid or None


def normalize_title(title: object | None) -> str:
    if title is None:
        return ""
    normalized = str(title).casefold()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()

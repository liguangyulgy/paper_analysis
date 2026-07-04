from __future__ import annotations

import re
from dataclasses import dataclass


SUPPLIER_USAGE_PATTERNS = [
    r"\bfrom\s+genoway\b",
    r"\bprovided\s+by\s+genoway\b",
    r"\bpurchased\s+from\s+genoway\b",
    r"\bobtained\s+from\s+genoway\b",
    r"\bgenerated\s+by\s+genoway\b",
    r"\bdeveloped\s+by\s+genoway\b",
    r"\bcustomi[sz]ed\s+by\s+genoway\b",
    r"\bgenoway\s+(?:mouse|mice|model|models)\b",
]

MODEL_KEYWORDS = [
    "BRGSF",
    "BRGSF-HIS",
    "humanized mouse",
    "humanized mice",
    "humanized rat",
    "human immune system",
    "FcRn humanized",
    "IgE humanized",
]


@dataclass(frozen=True)
class EvidenceCandidate:
    evidence_type: str
    evidence_level: str
    evidence_sentence: str
    section_name: str
    confidence_score: float
    needs_review: bool


def classify_paper_evidence(paper: dict[str, object]) -> list[EvidenceCandidate]:
    candidates: list[EvidenceCandidate] = []
    fields = {
        "title": paper.get("title"),
        "abstract": paper.get("abstract"),
        "affiliations": paper.get("affiliations"),
    }

    for field_name, value in fields.items():
        text = "" if value is None else str(value)
        if not text:
            continue
        candidates.extend(_supplier_usage_candidates(text, field_name))
        candidates.extend(_keyword_only_candidates(text, field_name))

    affiliations = "" if paper.get("affiliations") is None else str(paper.get("affiliations"))
    if "genoway" in affiliations.casefold():
        for affiliation in affiliations.split("|"):
            if "genoway" in affiliation.casefold():
                candidates.append(
                    EvidenceCandidate(
                        evidence_type="author_affiliation",
                        evidence_level="C",
                        evidence_sentence=affiliation.strip(),
                        section_name="affiliations",
                        confidence_score=0.6,
                        needs_review=True,
                    )
                )

    return _dedupe_candidates(candidates)


def _supplier_usage_candidates(text: str, field_name: str) -> list[EvidenceCandidate]:
    candidates = []
    for pattern in SUPPLIER_USAGE_PATTERNS:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            candidates.append(
                EvidenceCandidate(
                    evidence_type="supplier_usage",
                    evidence_level="A",
                    evidence_sentence=_extract_sentence(text, match.start(), match.end()),
                    section_name=field_name,
                    confidence_score=0.9,
                    needs_review=False,
                )
            )
    return candidates


def _keyword_only_candidates(text: str, field_name: str) -> list[EvidenceCandidate]:
    candidates = []
    for keyword in MODEL_KEYWORDS:
        pattern = re.compile(re.escape(keyword), flags=re.IGNORECASE)
        for match in pattern.finditer(text):
            candidates.append(
                EvidenceCandidate(
                    evidence_type="keyword_only",
                    evidence_level="D",
                    evidence_sentence=_extract_sentence(text, match.start(), match.end()),
                    section_name=field_name,
                    confidence_score=0.4,
                    needs_review=True,
                )
            )
    return candidates


def _extract_sentence(text: str, start_index: int, end_index: int) -> str:
    start = max(text.rfind(".", 0, start_index), text.rfind("\n", 0, start_index))
    end_candidates = [text.find(".", end_index), text.find("\n", end_index)]
    end_candidates = [candidate for candidate in end_candidates if candidate != -1]
    end = min(end_candidates) if end_candidates else len(text)
    sentence = text[start + 1 : end + 1].strip()
    return re.sub(r"\s+", " ", sentence)


def _dedupe_candidates(candidates: list[EvidenceCandidate]) -> list[EvidenceCandidate]:
    seen = set()
    deduped = []
    for candidate in candidates:
        key = (
            candidate.evidence_type,
            candidate.section_name,
            candidate.evidence_sentence.casefold(),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped

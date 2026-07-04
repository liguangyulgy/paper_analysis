from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KEYWORD_CONFIG = PROJECT_ROOT / "configs" / "model_keywords.yaml"


@dataclass(frozen=True)
class KeywordRule:
    keyword: str
    keyword_group: str
    source_config: str


@dataclass(frozen=True)
class KeywordHit:
    keyword: str
    keyword_group: str
    matched_text: str
    matched_field: str
    evidence_sentence: str
    source_config: str


def load_keyword_rules(config_path: str | Path | None = None) -> list[KeywordRule]:
    path = Path(config_path) if config_path is not None else DEFAULT_KEYWORD_CONFIG
    if not path.exists():
        return []

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rules: list[KeywordRule] = []

    if isinstance(data.get("keyword_groups"), dict):
        for group, keywords in data["keyword_groups"].items():
            rules.extend(_rules_from_group(group, keywords, path))
    else:
        for group, keywords in data.items():
            if isinstance(keywords, list):
                rules.extend(_rules_from_group(_normalize_group_name(group), keywords, path))

    return rules


def match_keywords(
    fields: dict[str, str | None],
    rules: list[KeywordRule] | None = None,
) -> list[KeywordHit]:
    keyword_rules = rules if rules is not None else load_keyword_rules()
    hits: list[KeywordHit] = []
    seen: set[tuple[str, str, str, str]] = set()

    for field_name, value in fields.items():
        if not value:
            continue
        text = str(value)
        for rule in keyword_rules:
            if _contains_keyword(text, rule.keyword):
                sentence = _extract_sentence(text, rule.keyword)
                key = (rule.keyword.casefold(), rule.keyword_group, field_name, sentence.casefold())
                if key in seen:
                    continue
                seen.add(key)
                hits.append(
                    KeywordHit(
                        keyword=rule.keyword,
                        keyword_group=rule.keyword_group,
                        matched_text=rule.keyword,
                        matched_field=field_name,
                        evidence_sentence=sentence,
                        source_config=rule.source_config,
                    )
                )
    return hits


def _rules_from_group(group: str, keywords: Any, path: Path) -> list[KeywordRule]:
    if not isinstance(keywords, list):
        return []
    rules = []
    for keyword in keywords:
        if keyword is None:
            continue
        cleaned = str(keyword).strip()
        if cleaned:
            try:
                source_config = str(path.relative_to(PROJECT_ROOT))
            except ValueError:
                source_config = str(path)
            rules.append(
                KeywordRule(
                    keyword=cleaned,
                    keyword_group=str(group).strip(),
                    source_config=source_config,
                )
            )
    return rules


def _normalize_group_name(name: str) -> str:
    normalized = str(name).strip()
    if normalized.endswith("_keywords"):
        normalized = normalized[: -len("_keywords")]
    return normalized


def _contains_keyword(text: str, keyword: str) -> bool:
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    return pattern.search(text) is not None


def _extract_sentence(text: str, keyword: str) -> str:
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    match = pattern.search(text)
    if match is None:
        return text.strip()

    start = max(text.rfind(".", 0, match.start()), text.rfind("。", 0, match.start()))
    end_candidates = [text.find(".", match.end()), text.find("。", match.end())]
    end_candidates = [candidate for candidate in end_candidates if candidate != -1]
    end = min(end_candidates) if end_candidates else len(text)

    sentence = text[start + 1 : end + 1].strip()
    return re.sub(r"\s+", " ", sentence)

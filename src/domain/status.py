from __future__ import annotations

STATUS_VALUES: dict[str, set[str]] = {
    "discovery_status": {"discovered", "duplicate", "excluded"},
    "abstract_status": {"not_checked", "fetched", "missing", "failed"},
    "fulltext_status": {
        "not_checked",
        "resolving",
        "xml_available",
        "pdf_available",
        "downloaded",
        "unavailable",
        "restricted",
        "failed",
        "conversion_needed",
    },
    "parse_status": {"not_started", "pending", "parsed", "partial", "failed", "conversion_needed"},
    "analysis_status": {"not_started", "pending", "analyzed", "failed"},
    "evidence_level": {"unknown", "A", "B", "C", "D", "X"},
    "reference_value": {"high", "medium", "low", "exclude", "unknown"},
    "review_status": {"not_required", "needs_review", "reviewed", "confirmed", "rejected"},
    "language": {"en", "zh", "mixed", "unknown"},
    "region_relevance": {"china_domestic", "global", "unknown", "not_china_related"},
}


def validate_status_value(field_name: str, value: object) -> None:
    allowed = STATUS_VALUES.get(field_name)
    if allowed is None or value is None:
        return
    if str(value) not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise ValueError(f"invalid {field_name}: {value!r}. Allowed values: {allowed_values}")


def validate_status_fields(fields: dict[str, object]) -> None:
    for field_name, value in fields.items():
        validate_status_value(field_name, value)

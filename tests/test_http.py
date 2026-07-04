from __future__ import annotations

from src.utils.http import inject_system_truststore


def test_inject_system_truststore_returns_boolean():
    assert isinstance(inject_system_truststore(), bool)

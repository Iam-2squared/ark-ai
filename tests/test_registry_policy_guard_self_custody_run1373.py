"""Run1373: ToolRegistry admission guard functions retain their own identity."""

from __future__ import annotations

import pytest

import ark.agency.registry as registry
from ark.agency.registry import ToolRegistry


@pytest.mark.parametrize(
    ("guard_name", "entrypoint", "message"),
    (
        (
            "_require_original_registry_limits",
            "text",
            "registry admission limits changed",
        ),
        (
            "_require_original_registry_unicode",
            "text",
            "registry Unicode category dependency changed",
        ),
        (
            "_require_original_registry_digest",
            "revision",
            "registry digest dependencies changed",
        ),
    ),
)
def test_replaced_registry_guard_is_rejected_before_entrypoint_work(
    monkeypatch: pytest.MonkeyPatch,
    guard_name: str,
    entrypoint: str,
    message: str,
) -> None:
    canonical_calls: list[bool] = []
    monkeypatch.setattr(registry, guard_name, lambda: None)
    monkeypatch.setattr(
        registry,
        "_canonical_json",
        lambda _value: canonical_calls.append(True),
    )

    with pytest.raises(ValueError, match=message):
        if entrypoint == "text":
            registry._text("fixture.identity", "safe")
        else:
            ToolRegistry._compute_revision([])

    assert canonical_calls == []


@pytest.mark.parametrize(
    ("guard_name", "message"),
    (
        (
            "_require_original_registry_limits",
            "registry admission limits changed",
        ),
        (
            "_require_original_registry_unicode",
            "registry Unicode category dependency changed",
        ),
    ),
)
def test_registry_digest_guard_uses_retained_limit_and_unicode_guards(
    monkeypatch: pytest.MonkeyPatch,
    guard_name: str,
    message: str,
) -> None:
    monkeypatch.setattr(registry, guard_name, lambda: None)

    with pytest.raises(ValueError, match=message):
        registry._ORIGINAL_REQUIRE_REGISTRY_DIGEST()

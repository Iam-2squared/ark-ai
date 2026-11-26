"""Run1188: complete Unicode format-control admission for proactive identities."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import ark.proactive_state_ledger as proactive_state


def _policy(**overrides: object) -> proactive_state.SyntheticProactivePolicy:
    values: dict[str, object] = {
        "owner": "owner-a",
        "namespace": "personal",
        "definition_id": "daily-summary",
        "revision": 1,
        "policy_revision": "policy-v1",
        "minimum_interval_ms": 100,
        "cooldown_ms": 200,
        "rolling_window_ms": 1000,
        "max_previews_per_window": 2,
    }
    values.update(overrides)
    return proactive_state.SyntheticProactivePolicy(**values)


@pytest.mark.parametrize("field", ("owner", "namespace", "definition_id", "policy_revision"))
@pytest.mark.parametrize("control", ("\u0600", "\ufff9", "\U000e0001"))
def test_proactive_policy_rejects_every_unicode_cf_identity(
    field: str,
    control: str,
) -> None:
    with pytest.raises(
        proactive_state.SyntheticProactiveStateRejected,
        match="Unicode formatting control",
    ):
        _policy(**{field: f"valid{control}identity"})


def test_japanese_proactive_policy_identity_remains_supported() -> None:
    identity = _policy(
        owner="利用者",
        namespace="個人",
        definition_id="日次要約",
        policy_revision="方針-v1",
    ).identity()

    assert len(identity) == 2
    assert all(type(value) is str and len(value) == 64 for value in identity)


@pytest.mark.parametrize("phase", ("construction", "identity"))
def test_replaced_unicode_module_is_denied_before_category_callback(
    monkeypatch: pytest.MonkeyPatch,
    phase: str,
) -> None:
    policy = _policy() if phase == "identity" else None
    calls: list[str] = []

    def forbidden_category(character: str) -> str:
        calls.append(character)
        return "Cf"

    monkeypatch.setattr(
        proactive_state,
        "unicodedata",
        SimpleNamespace(category=forbidden_category),
    )

    with pytest.raises(
        proactive_state.SyntheticProactiveStateRejected,
        match="protocol changed",
    ):
        if phase == "construction":
            _policy(owner="private-owner")
        else:
            assert policy is not None
            policy.identity()

    assert calls == []

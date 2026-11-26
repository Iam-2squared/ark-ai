"""A disconnected recovery fence never executes substituted carrier hooks.

Pure synthetic claims and result diagnostics; no backend, network, consent,
trusted clock, or durable execution authority. Inherited CPython __new__ is
not monkeypatched in the shared test interpreter.
"""

import pytest

import ark.agency.disconnected_write_recovery_fence as recovery

PLAN = "plan_" + "a" * 64
WRITE = "step_" + "1" * 16
CHILD = "step_" + "2" * 16


def _claims():
    return (
        recovery.OfflineRecoveryStepClaim(WRITE, "WRITE", (), "UNKNOWN"),
        recovery.OfflineRecoveryStepClaim(
            CHILD, "READ", (WRITE,), "PENDING",
        ),
    )


@pytest.mark.parametrize(
    ("class_name", "member"),
    (
        *(("OfflineRecoveryStepClaim", name) for name in (
            "step_id", "effect", "depends_on", "state",
            "result_sha256", "reservation_id",
            "__init__", "__getattribute__", "__getattr__",
        )),
        *(("OfflineRecoveryDisposition", name) for name in (
            "step_id", "code", "__init__", "__getattribute__", "__getattr__",
        )),
        *(("OfflineRecoveryFence", name) for name in (
            "plan_id", "decisions", "digest",
            "__init__", "__getattribute__", "__getattr__",
        )),
    ),
)
def test_preinstalled_recovery_carrier_poison_is_denied_without_execution(
    monkeypatch, class_name: str, member: str,
):
    claims = _claims()
    called = []

    def malicious(*_args, **_kwargs):
        called.append(member)
        raise AssertionError("untrusted Python carrier executed")

    target = getattr(recovery, class_name)
    replacement = malicious if member.startswith("__") else property(malicious)
    monkeypatch.setattr(target, member, replacement, raising=False)
    with pytest.raises(
        recovery.OfflineRecoveryFenceRejected, match="authority descriptor changed",
    ):
        recovery.review_disconnected_recovery_fence(PLAN, claims)
    assert called == []


@pytest.mark.parametrize(
    ("callback", "target_name", "field"),
    (
        ("json", "OfflineRecoveryStepClaim", "state"),
        ("json", "OfflineRecoveryDisposition", "code"),
        ("digest", "OfflineRecoveryFence", "decisions"),
    ),
)
def test_substituted_digest_callback_denied_before_canonicalization(
    monkeypatch, callback: str, target_name: str, field: str,
):
    claims = _claims()
    attacked = []
    called = []
    target = getattr(recovery, target_name)
    original_field = vars(target).get(field)

    def malicious(*_args, **_kwargs):
        called.append(True)
        raise AssertionError("untrusted Python carrier executed")

    def install():
        if not attacked:
            attacked.append(callback)
            monkeypatch.setattr(target, field, property(malicious))

    if callback == "json":
        original = recovery.json.dumps

        def callback_json(*args, **kwargs):
            result = original(*args, **kwargs)
            install()
            return result

        monkeypatch.setattr(recovery.json, "dumps", callback_json)
    else:
        original = recovery.hashlib.sha256

        def callback_hash(value):
            result = original(value)
            install()
            return result

        monkeypatch.setattr(recovery.hashlib, "sha256", callback_hash)

    # Hash/JSON substitutions are rejected before the callback or class
    # mutation executes, not merely after a late output-carrier review.
    with pytest.raises(
        recovery.OfflineRecoveryFenceRejected,
        match="mixed-plan digest implementation or domain changed",
    ):
        recovery.review_disconnected_recovery_fence(PLAN, claims)
    assert attacked == []
    assert called == []
    assert vars(target).get(field) is original_field


def test_untampered_unknown_write_and_dependent_read_remain_denied():
    view = recovery.review_disconnected_recovery_fence(PLAN, _claims())
    assert tuple(item.code for item in view.decisions) == (
        "QUARANTINE_WRITE_UNKNOWN", "HOLD_UNCERTAIN",
    )
    assert view.dispatch_authorized is False
    assert view.automatic_replay_authorized is False
    assert view.write_authorized is False
    assert view.external_outcome_verified is False

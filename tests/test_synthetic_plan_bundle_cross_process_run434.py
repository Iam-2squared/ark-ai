"""A detached multi-WRITE forensic bundle never becomes replay authority.

Uses only disposable local SQLite and a separate local Python interpreter.
The digest is integrity evidence only, not a signature or consent token.
"""

import json
import subprocess
import sys

import pytest

import ark.agency.synthetic_plan_recovery_bundle_review as bundle_module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import (
    Effect,
    OneShotAuthorization,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticOccurrenceAuditLinkStore,
)
from ark.agency.synthetic_write_plan_recovery_review import (
    review_synthetic_write_plan,
)


class NoDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("offline recovery may not execute a backend")


def _fixture(root, *, unresolved=False):
    root.mkdir(parents=True, exist_ok=True)
    first = ToolCall("write", "offline.write", "mock", {"step": "first"})
    bridge = ToolCall("read", "offline.read", "mock")
    last = ToolCall("write", "offline.write", "mock", {"step": "last"})
    journal = SyntheticPlanJournal(root / "plan.sqlite", (
        PlanStep("first", first),
        PlanStep("bridge", bridge, depends_on=("first",)),
        PlanStep("last", last, depends_on=("bridge",)),
    ))
    ledger = SyntheticOccurrenceStore(root / "occ.sqlite")
    audit = SQLiteActionAudit(root / "audit.sqlite", clock_ms=lambda: 15)
    links = SyntheticOccurrenceAuditLinkStore(root / "links.sqlite")
    backend = NoDispatch()
    registry = ToolRegistry((
        ToolRegistration("write", "offline.write", Effect.WRITE, "mock", backend),
        ToolRegistration("read", "offline.read", Effect.READ, "mock", backend),
    ))
    if unresolved:
        journal.append("first", StepState.RUNNING, expected_revision=0, at_ms=10)
        ledger.reserve_synthetic(
            registry, last,
            OneShotAuthorization("reserved-once", last.request_id, 1000),
            occurrence_id="occ_" + "b" * 64, now_ms=12,
        )
    return journal, ledger, audit, links, registry, backend


def _review(state):
    journal, ledger, audit, links, registry, backend = state
    result = review_synthetic_write_plan(
        journal, ledger._path, audit, registry, link_store=links,
    )
    assert backend.calls == 0
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    return result


@pytest.mark.parametrize("unresolved", (False, True))
def test_bundle_restores_identical_detached_step_witnesses(tmp_path, unresolved):
    state = _fixture(tmp_path / "state", unresolved=unresolved)
    original = _review(state)
    bundle = bundle_module.bundle_synthetic_write_plan(original)
    assert bundle.canonical_json
    assert bundle.digest.startswith("splanbundle_")
    assert bundle.dispatch_authorized is False
    assert bundle.automatic_replay_authorized is False
    assert bundle.external_outcome_known is False
    restored = bundle_module.restore_synthetic_write_plan_bundle(bundle)
    assert len(restored) == 2
    assert tuple(
        bundle_module._restore(item)[0]["step_id"] for item in restored
    ) == ("first", "last")
    assert all(item.dispatch_authorized is False for item in restored)
    assert all(item.automatic_replay_authorized is False for item in restored)
    if unresolved:
        assert original.uncertain_step_ids == ("first", "last")
    else:
        assert original.uncertain_step_ids == ()
    assert state[5].calls == 0


_CHILD = r"""
import pathlib
import sys

from ark.agency.synthetic_plan_recovery_bundle_review import (
    SyntheticWritePlanBundle,
    restore_synthetic_write_plan_bundle,
)

contents = pathlib.Path(sys.argv[1]).read_bytes()
bundle = SyntheticWritePlanBundle(contents, sys.argv[2])
restored = restore_synthetic_write_plan_bundle(bundle)
assert not bundle.dispatch_authorized
assert not bundle.automatic_replay_authorized
assert not bundle.external_outcome_known
print("STEPS:" + str(len(restored)), flush=True)
"""


def test_bundle_survives_separate_process_without_opening_stores(tmp_path):
    state = _fixture(tmp_path / "state", unresolved=True)
    archived = bundle_module.bundle_synthetic_write_plan(_review(state))
    detached = tmp_path / "offline.json"
    detached.write_bytes(archived.canonical_json)
    result = subprocess.run(
        [sys.executable, "-c", _CHILD, str(detached), archived.digest],
        capture_output=True, text=True, timeout=35, check=True,
    )
    assert result.stdout.strip() == "STEPS:2"
    assert state[5].calls == 0


def _rewrite(bundle, mutate):
    payload = json.loads(bundle.canonical_json)
    mutate(payload)
    data = bundle_module._canonical(payload)
    return bundle_module.SyntheticWritePlanBundle(
        data, bundle_module._digest(data),
    )


@pytest.mark.parametrize("case", (
    "hide_uncertain", "duplicate_step", "reverse_step",
    "replace_topology", "forge_archive", "forge_hold",
))
def test_recomputed_digest_cannot_hide_malformed_local_bundle(
    tmp_path, case,
):
    state = _fixture(tmp_path / "state", unresolved=True)
    bundle = bundle_module.bundle_synthetic_write_plan(_review(state))

    def mutate(payload):
        if case == "hide_uncertain":
            payload["uncertain"] = []
        elif case == "duplicate_step":
            payload["steps"].append(payload["steps"][0])
        elif case == "reverse_step":
            payload["steps"].reverse()
        elif case == "replace_topology":
            payload["topology_digest"] = "plan_" + "0" * 64
        elif case == "forge_archive":
            payload["steps"][0]["digest"] = "srecovery_" + "0" * 64
        elif case == "forge_hold":
            payload["downstream_hold"] = ["does_not_exist"]
    with pytest.raises(bundle_module.SyntheticWritePlanBundleRejected):
        bundle_module.restore_synthetic_write_plan_bundle(
            _rewrite(bundle, mutate),
        )
    assert state[5].calls == 0


def test_noncanonical_and_oversized_bundle_is_rejected(tmp_path):
    state = _fixture(tmp_path / "state")
    original = bundle_module.bundle_synthetic_write_plan(_review(state))
    altered = (
        original.canonical_json.replace(b',"steps":', b', "steps":', 1)
    )
    assert altered != original.canonical_json
    for data in (
        altered,
        original.canonical_json + b" ",
        b"{" + b" " * bundle_module._MAX_BYTES + b"}",
    ):
        suspect = bundle_module.SyntheticWritePlanBundle(
            data, bundle_module._digest(data),
        )
        with pytest.raises(bundle_module.SyntheticWritePlanBundleRejected):
            bundle_module.restore_synthetic_write_plan_bundle(suspect)


@pytest.mark.parametrize("attribute", ("canonical_json", "digest"))
def test_bundle_reflective_carrier_swap_during_decode_is_rejected(
    tmp_path, monkeypatch, attribute,
):
    state = _fixture(tmp_path / "state")
    bundle = bundle_module.bundle_synthetic_write_plan(_review(state))
    original = bundle_module._restore
    injections = []

    def swapped(archive):
        value = original(archive)
        if not injections:
            old = getattr(bundle, attribute)
            new = (
                memoryview(old).tobytes()
                if type(old) is bytes else ("!" + old)[1:]
            )
            assert new == old and new is not old
            object.__setattr__(bundle, attribute, new)
            injections.append(True)
        return value

    monkeypatch.setattr(bundle_module, "_restore", swapped)
    with pytest.raises(
        bundle_module.SyntheticWritePlanBundleRejected,
        match="changed during decode",
    ):
        bundle_module.restore_synthetic_write_plan_bundle(bundle)
    assert injections == [True]
    assert state[5].calls == 0

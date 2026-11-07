"""Multi-step retained READ evidence never completes a missing ancestor.

All cases run on local disconnected SQLite journals, with a backend that
throws on invocation. These are correlations, not independent execution proof.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.agency.disconnected_planner_success_bundle_review as bundle
from ark.agency.contracts import CapabilityGrant, Effect, PlanStep, StepState, ToolCall
from ark.agency.disconnected_fixture_binding import bind_disconnected_fixture_result
from ark.agency.disconnected_planner_fence_projection import (
    DisconnectedPlannerProjectionRejected,
    project_disconnected_planner_fence,
)
from ark.agency.disconnected_read_journal import (
    DisconnectedReadJournal,
    genesis_witness,
)
from ark.agency.disconnected_read_receipt_bridge import prepare_disconnected_read_receipt
from ark.agency.disconnected_registered_fixture_join import (
    review_registered_disconnected_fixture,
)
from ark.agency.disconnected_registered_receipt_review import (
    review_retained_registered_receipt,
)
from ark.agency.disconnected_toolbox import (
    DisconnectedToolRequest,
    execute_disconnected_fixture_tool,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry

FIRST = "step_" + "a" * 16
SECOND = "step_" + "b" * 16


class _NoBackend:
    calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("offline bundle attempted real tool execution")


def _multi(tmp_path, *, finish_second=True):
    backend = _NoBackend()
    registry = ToolRegistry((
        ToolRegistration("math.sum", "math.sum", Effect.READ, "mock:1", backend),
    ))
    gate = PermissionGate()
    grants = (CapabilityGrant("math.sum", "scope:private", 200),)
    steps = (
        PlanStep(
            FIRST,
            ToolCall("math.sum", "math.sum", "scope:private", {"values": [1, 2]}),
        ),
        PlanStep(
            SECOND,
            ToolCall("math.sum", "math.sum", "scope:private", {"values": [3, 4]}),
            (FIRST,),
        ),
    )
    read_journal = DisconnectedReadJournal.create(tmp_path / "read.sqlite")
    retained = genesis_witness()
    payloads = []
    for step, value in zip(steps, ("a", "b"), strict=True):
        request = DisconnectedToolRequest(
            "req_" + value * 32, "math.sum",
            '{"values":[' + ("1,2" if value == "a" else "3,4") + "]}",
        )
        result = execute_disconnected_fixture_tool(request)
        binding = bind_disconnected_fixture_result(request, result)
        link = review_registered_disconnected_fixture(
            registry, gate, step.call, grants, step.step_id,
            request, result, binding, observed_at_ms=50,
        )
        retained = read_journal.append(
            prepare_disconnected_read_receipt(step.step_id, request, result, binding),
            retained,
        )
        payloads.append((step, request, result, binding, link))

    planner = SyntheticPlanJournal(tmp_path / "planner.sqlite", steps)
    genesis = planner.recover().tail
    planner.append(FIRST, StepState.RUNNING, expected_revision=0, at_ms=50, retained=genesis)
    planner.append(FIRST, StepState.SUCCEEDED, expected_revision=1, at_ms=51, retained=genesis)
    if finish_second:
        planner.append(
            SECOND, StepState.RUNNING, expected_revision=0, at_ms=52, retained=genesis,
        )
        planner.append(
            SECOND, StepState.SUCCEEDED, expected_revision=1, at_ms=53, retained=genesis,
        )
    recovered = SyntheticPlanJournal(tmp_path / "planner.sqlite", steps).recover(
        retained=genesis,
    )
    evidence = []
    for step, request, result, binding, link in payloads:
        reviewed = review_retained_registered_receipt(
            read_journal, retained, link, registry, gate, step.call,
            grants, step.step_id, request, result, binding, observed_at_ms=50,
        )
        evidence.append((link, reviewed))
    return read_journal, steps, recovered, tuple(evidence), backend


def test_two_step_bundle_requires_both_distinct_receipts_in_canonical_order(tmp_path):
    journal, steps, recovered, evidence, backend = _multi(tmp_path)
    try:
        result = bundle.review_synthetic_succeeded_read_bundle(
            recovered, steps, evidence[::-1],
        )
        assert result.step_ids == (FIRST, SECOND)
        assert result == bundle.review_synthetic_succeeded_read_bundle(
            recovered, steps, evidence,
        )
        assert len(result.correlation_sha256s) == 2
        assert result.external_execution_proven is False
        assert result.write_authorized is False
        assert result.dispatch_authorized is False
        assert result.automatic_replay_authorized is False
        with pytest.raises(DisconnectedPlannerProjectionRejected):
            project_disconnected_planner_fence(
                recovered, steps, ((FIRST, "READ"), (SECOND, "READ")),
            )
        assert backend.calls == 0
    finally:
        journal.close()


@pytest.mark.parametrize(
    "fault",
    ("missing_ancestor", "missing_successor", "duplicate", "wrong_step",
     "wrong_registry", "no_receipts", "non_tuple_pair", "duplicate_fixture"),
)
def test_incomplete_or_mismatched_multistep_evidence_is_not_success(
    tmp_path, fault,
):
    journal, steps, recovered, evidence, backend = _multi(tmp_path)
    try:
        if fault == "missing_ancestor":
            evidence = (evidence[1],)
        elif fault == "missing_successor":
            evidence = (evidence[0],)
        elif fault == "duplicate":
            evidence = (evidence[0], evidence[0])
        elif fault == "wrong_step":
            evidence = ((replace(evidence[0][0], step_id=SECOND), evidence[0][1]),
                        evidence[1])
        elif fault == "wrong_registry":
            evidence = ((replace(evidence[0][0], registry_revision="wrong"), evidence[0][1]),
                        evidence[1])
        elif fault == "no_receipts":
            evidence = ()
        elif fault == "non_tuple_pair":
            evidence = ([*evidence[0]], evidence[1])
        else:
            evidence = (
                evidence[0],
                (replace(evidence[1][0], fixture_request_id=evidence[0][0].fixture_request_id),
                 evidence[1][1]),
            )
        with pytest.raises(bundle.PlannerReadSuccessBundleRejected):
            bundle.review_synthetic_succeeded_read_bundle(
                recovered, steps, evidence,
            )
        assert backend.calls == 0
    finally:
        journal.close()


def test_succeeded_ancestor_with_pending_descendant_is_only_partial_evidence(tmp_path):
    journal, steps, recovered, evidence, backend = _multi(tmp_path, finish_second=False)
    try:
        result = bundle.review_synthetic_succeeded_read_bundle(
            recovered, steps, (evidence[0],),
        )
        assert result.step_ids == (FIRST,)
        with pytest.raises(bundle.PlannerReadSuccessBundleRejected):
            bundle.review_synthetic_succeeded_read_bundle(
                recovered, steps, evidence,
            )
        assert backend.calls == 0
    finally:
        journal.close()


def test_replaced_bundle_authority_carrier_rejected_before_read_review(
    tmp_path, monkeypatch,
):
    journal, steps, recovered, evidence, backend = _multi(tmp_path)
    try:
        with monkeypatch.context() as patch:
            patch.setattr(
                bundle.PlannerReadSuccessBundle,
                "dispatch_authorized", property(lambda _: True),
            )
            with pytest.raises(
                bundle.PlannerReadSuccessBundleRejected, match="carrier changed",
            ):
                bundle.review_synthetic_succeeded_read_bundle(
                    recovered, steps, evidence,
                )
        assert backend.calls == 0
    finally:
        journal.close()


def test_substituted_correlation_callback_cannot_supply_receipt(
    tmp_path, monkeypatch,
):
    """Reject an injected source before reading any synthetic success evidence."""
    journal, steps, recovered, evidence, backend = _multi(tmp_path)
    invoked = []

    def synthetic_forgery(*args, **kwargs):
        invoked.append((args, kwargs))
        raise AssertionError("unexpected untrusted callback")

    try:
        with monkeypatch.context() as patch:
            patch.setattr(
                bundle.single, "review_synthetic_succeeded_read_correlation",
                synthetic_forgery,
            )
            with pytest.raises(
                bundle.PlannerReadSuccessBundleRejected, match="callback changed",
            ):
                bundle.review_synthetic_succeeded_read_bundle(
                    recovered, steps, evidence,
                )
        assert invoked == []
        assert backend.calls == 0
        restored = bundle.review_synthetic_succeeded_read_bundle(
            recovered, steps, evidence,
        )
        assert restored.step_ids == (FIRST, SECOND)
        assert restored.dispatch_authorized is False
        assert backend.calls == 0
    finally:
        journal.close()


@pytest.mark.parametrize(
    "changed_dependency",
    ("single_originals", "tail_stability", "link_schema", "review_schema"),
)
def test_bundle_pins_original_nested_custody_checks_before_correlating(
    tmp_path, monkeypatch, changed_dependency,
):
    journal, steps, recovered, evidence, backend = _multi(tmp_path)
    invoked = []

    def forbidden(*args, **kwargs):
        invoked.append((args, kwargs))
        raise AssertionError("substituted dependency hook was executed")

    try:
        with monkeypatch.context() as patch:
            if changed_dependency == "single_originals":
                patch.setattr(bundle.single, "_originals", forbidden)
            elif changed_dependency == "tail_stability":
                patch.setattr(
                    bundle.journal, "_retained_tail_epoch_stable", forbidden,
                )
            elif changed_dependency == "link_schema":
                original = bundle.registered._LINK_FIELDS
                patch.setattr(
                    bundle.registered, "_LINK_FIELDS", tuple(list(original)),
                )
            else:
                original = bundle.registered._REVIEW_FIELDS
                patch.setattr(
                    bundle.registered, "_REVIEW_FIELDS", tuple(list(original)),
                )
            with pytest.raises(
                bundle.PlannerReadSuccessBundleRejected,
                match="dependency callback or schema changed",
            ):
                bundle.review_synthetic_succeeded_read_bundle(
                    recovered, steps, evidence,
                )

        assert invoked == []
        restored = bundle.review_synthetic_succeeded_read_bundle(
            recovered, steps, evidence,
        )
        assert restored.step_ids == (FIRST, SECOND)
        assert restored.dispatch_authorized is False
        assert backend.calls == 0
    finally:
        journal.close()


@pytest.mark.parametrize(
    "changed",
    ("hashlib_module", "json_module", "sha256", "dumps",
     "domain", "equal_domain_replacement"),
)
def test_bundle_pins_digest_primitives_and_domain_before_receipt_join(
    tmp_path, monkeypatch, changed,
):
    """A local digest must not be sourced from a mutable injected callback."""
    journal, steps, recovered, evidence, backend = _multi(tmp_path)
    invoked = []

    def forbidden(*args, **kwargs):
        invoked.append((args, kwargs))
        raise AssertionError("counterfeit digest callback executed")

    try:
        with monkeypatch.context() as patch:
            if changed == "hashlib_module":
                patch.setattr(bundle, "hashlib", object())
            elif changed == "json_module":
                patch.setattr(bundle, "json", object())
            elif changed == "sha256":
                patch.setattr(bundle.hashlib, "sha256", forbidden)
            elif changed == "dumps":
                patch.setattr(bundle.json, "dumps", forbidden)
            elif changed == "domain":
                patch.setattr(bundle, "_DOMAIN", b"altered-domain")
            else:
                identical_bytes = bytes(bytearray(bundle._DOMAIN))
                assert identical_bytes == bundle._DOMAIN
                assert identical_bytes is not bundle._DOMAIN
                patch.setattr(bundle, "_DOMAIN", identical_bytes)
            with pytest.raises(
                bundle.PlannerReadSuccessBundleRejected,
                match="bundle digest implementation or domain changed",
            ):
                bundle.review_synthetic_succeeded_read_bundle(
                    recovered, steps, evidence,
                )
        assert invoked == []
        valid = bundle.review_synthetic_succeeded_read_bundle(
            recovered, steps, evidence,
        )
        assert valid.step_ids == (FIRST, SECOND)
        assert valid.dispatch_authorized is False
        assert backend.calls == 0
    finally:
        journal.close()

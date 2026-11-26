"""Only enumerated codes enter offline diagnostic JSONL; never raw payload."""

import hashlib
import json
from dataclasses import fields

import pytest

from ark.private_diagnostic_ledger import (
    PrivateDiagnosticEvent,
    PrivateDiagnosticRejected,
    render_private_diagnostic_ledger,
)

ANCHOR = "a" * 64
SECRET = "DO_NOT_LEAK_personal_private_token_RUN453"
DOMAIN = b"ARK-detached-private-diagnostics-v1\0"


def event(sequence=1, component="memory", stage="ingress", outcome="rejected", reason="stale"):
    return PrivateDiagnosticEvent(sequence, component, stage, outcome, reason)


def render(*events, start=1, anchor=ANCHOR):
    return render_private_diagnostic_ledger(
        tuple(events), start_sequence=start, retained_anchor_sha256=anchor,
    )


def test_exact_bytes_are_deterministic_and_independently_chain_verified():
    result = render(event(), event(2, "privacy", "recovery", "deferred", "quarantined"))
    assert result.count == 2
    assert (result.first_sequence, result.last_sequence) == (1, 2)
    lines = [json.loads(line) for line in result.canonical_jsonl.splitlines()]
    assert [line["seq"] for line in lines] == [1, 2]
    expected_keys = {"v", "seq", "component", "stage", "outcome", "reason", "prior", "sha256"}
    assert set(lines[0]) == expected_keys
    chain = ANCHOR
    for row in lines:
        assert row["prior"] == chain
        data = [1, row["seq"], row["component"], row["stage"], row["outcome"],
                row["reason"], chain]
        encoded = json.dumps(data, ensure_ascii=True, separators=(",", ":")).encode("ascii")
        chain = hashlib.sha256(DOMAIN + encoded).hexdigest()
        assert row["sha256"] == chain
    assert result.final_sha256 == chain
    assert result == render(event(), event(2, "privacy", "recovery", "deferred", "quarantined"))
    assert not result.trusted_audit_evidence
    assert not result.external_log_export_authorized
    assert not result.action_authorized


def test_follow_on_chain_requires_exact_sequence_and_caller_anchor():
    first = render(event())
    second = render(event(2, "tool", "postcheck", "reviewed", "missing_evidence"),
                    start=2, anchor=first.final_sha256)
    assert second.first_sequence == 2
    assert json.loads(second.canonical_jsonl)["prior"] == first.final_sha256
    assert second.final_sha256 != first.final_sha256


@pytest.mark.parametrize(
    "bad",
    [event(component=SECRET), event(component="memory\nprivate"), event(stage=SECRET),
     event(outcome="approved"), event(reason=SECRET), event(sequence=True),
     event(sequence=0), event(sequence=2), event(reason=123),
     event(component="MEMORY"), event(stage="dispatch"),
     event(outcome="executed"), event(reason="ok")],
)
def test_never_serialize_raw_user_supplied_values(bad):
    with pytest.raises(PrivateDiagnosticRejected) as error:
        render(bad)
    assert SECRET not in str(error.value)


@pytest.mark.parametrize(
    ("start", "anchor"),
    [(True, ANCHOR), (0, ANCHOR), (-1, ANCHOR),
     (2**63, ANCHOR), (1, SECRET), (1, "A" * 64), (1, 7)],
)
def test_invalid_sequence_anchor_refused(start, anchor):
    with pytest.raises(PrivateDiagnosticRejected):
        render(event(), start=start, anchor=anchor)


def test_bad_container_subtype_and_over_budget_fail_closed():
    with pytest.raises(PrivateDiagnosticRejected):
        render_private_diagnostic_ledger([event()], start_sequence=1,
                                         retained_anchor_sha256=ANCHOR)
    with pytest.raises(PrivateDiagnosticRejected):
        render(*([event(i + 1) for i in range(129)]))
    with pytest.raises(PrivateDiagnosticRejected):
        render(event(2**63 - 1), event(2**63), start=2**63 - 1)
    with pytest.raises(PrivateDiagnosticRejected):
        render(object())


def test_result_repr_never_contains_full_jsonl():
    result = render(event())
    assert next(f for f in fields(type(result)) if f.name == "canonical_jsonl").repr is False
    assert result.canonical_jsonl not in repr(result)


def test_no_dynamic_non_enum_input_can_reach_serialized_output():
    class Secret(str):
        pass

    with pytest.raises(PrivateDiagnosticRejected):
        render(event(component=Secret("memory")))
    result = render(event(reason="missing_evidence"))
    assert SECRET not in result.canonical_jsonl
    assert "missing_evidence" in result.canonical_jsonl

"""Synthetic ActionAudit continuity has exact retained/result epochs.

All rows are disconnected fixture events; continuity is not a trusted clock,
backend outcome attestation, user consent or permission to replay a WRITE.
"""

from pathlib import Path

import pytest

import ark.agency.audit_continuity_review as module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _audit(tmp_path: Path) -> SQLiteActionAudit:
    audit = SQLiteActionAudit(tmp_path / "audit # %.sqlite", clock_ms=lambda: 100)
    for n in (1, 2):
        audit.append(
            ToolCall("offline.read", "read", "local", {"n": n}),
            outcome="synthetic-only",
        )
    return audit


def _clone(text: str) -> str:
    result = ("!" + text)[1:]
    assert result == text and result is not text
    return result


@pytest.mark.parametrize(
    "mutation", ("equal_digest", "count_float", "tail_float"),
)
def test_retained_audit_cannot_be_reflected_to_equal_value_carrier_or_type(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    audit = _audit(tmp_path)
    retained = module.review_audit_continuity(audit)
    original = module._row_payload

    def mutated(row, *, previous_id):
        data = original(row, previous_id=previous_id)
        if mutation == "equal_digest":
            object.__setattr__(
                retained, "chain_sha256", _clone(retained.chain_sha256)
            )
        elif mutation == "count_float":
            object.__setattr__(
                retained, "event_count", float(retained.event_count)
            )
        else:
            object.__setattr__(
                retained, "tail_event_id", float(retained.tail_event_id)
            )
        return data

    monkeypatch.setattr(module, "_row_payload", mutated)
    with pytest.raises(ActionAuditSchemaError, match="retained.*changed"):
        module.review_audit_continuity(audit, retained=retained)


@pytest.mark.parametrize("mutation", ("event_count", "tail_event_id", "digest", "path"))
def test_returned_audit_witness_rejects_late_constructor_side_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    audit = _audit(tmp_path)
    original_path = audit.path
    witness_type = module.AuditContinuityWitness
    original_post_init = witness_type.__post_init__

    def tampered(self):
        original_post_init(self)
        if mutation == "event_count":
            object.__setattr__(self, "event_count", self.event_count + 1)
        elif mutation == "tail_event_id":
            object.__setattr__(self, "tail_event_id", self.tail_event_id + 1)
        elif mutation == "digest":
            object.__setattr__(
                self, "chain_sha256", _clone(self.chain_sha256)
            )
        else:
            audit.path = Path(str(original_path))

    monkeypatch.setattr(witness_type, "__post_init__", tampered)
    expected = (
        "source changed" if mutation == "path"
        else "returned audit continuity witness changed"
    )
    with pytest.raises(ActionAuditSchemaError, match=expected):
        module.review_audit_continuity(audit)


def test_untampered_audit_history_stays_readonly_and_prefix_bound(
    tmp_path: Path,
) -> None:
    audit = _audit(tmp_path)
    first = module.review_audit_continuity(audit)
    second = module.review_audit_continuity(audit, retained=first)
    assert first == second
    assert first.event_count == 2
    assert first.tail_event_id == 2
    assert len(first.chain_sha256) == 64
    assert not hasattr(first, "dispatch_authorized")

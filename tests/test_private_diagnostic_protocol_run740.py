"""Public-only diagnostic writer + independent retained-chain verifier.

All evidence is local/caller asserted. These tests do not authorize export,
tool dispatch, forensic erasure, runtime identity, or real audit authority.
"""

from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace

import pytest

import ark.private_diagnostic_ledger as writer
import ark.private_diagnostic_ledger_verify as verifier


def _preview():
    return writer.render_private_diagnostic_ledger(
        (
            writer.PrivateDiagnosticEvent(
                10, "memory", "recovery", "deferred", "nonreplay_required",
            ),
            writer.PrivateDiagnosticEvent(
                11, "privacy", "postcheck", "reviewed", "missing_evidence",
            ),
        ),
        start_sequence=10,
        retained_anchor_sha256="a" * 64,
    )


def _verify(payload=None, *, count=2, start=10, anchor="a" * 64, tip=None):
    original = _preview()
    return verifier.verify_private_diagnostic_jsonl(
        original.canonical_jsonl if payload is None else payload,
        retained_anchor_sha256=anchor,
        expected_start_sequence=start,
        expected_count=count,
        expected_final_sha256=original.final_sha256 if tip is None else tip,
    )


def test_original_writer_chain_roundtrips_with_independent_verifier():
    preview = _preview()
    result = _verify()
    assert result.first_sequence == preview.first_sequence == 10
    assert result.last_sequence == preview.last_sequence == 11
    assert result.count == preview.count == 2
    assert result.final_sha256 == preview.final_sha256
    assert preview.action_authorized is False
    assert preview.trusted_audit_evidence is False
    assert preview.external_log_export_authorized is False
    assert result.audit_authenticated is False
    assert result.cleanup_authorized is False
    assert result.tool_execution_authorized is False
    assert result.private_data_export_authorized is False
    assert "canonical_jsonl" not in repr(result)


@pytest.mark.parametrize(("name", "replacement"), (
    ("_DOMAIN", b"ARK-unsafe-diagnostic\0"),
    ("_SHA", object()),
    ("_COMPONENT", frozenset(("memory", "SECRET"))),
    ("_STAGE", frozenset(("anything",))),
    ("_OUTCOME", frozenset(("approved",))),
    ("_REASON", frozenset(("secret",))),
    ("_MAX_EVENTS", 256),
    ("_MAX_SEQUENCE", True),
    ("_MAX_OUTPUT_BYTES", 1_000_000),
))
def test_writer_preaccess_protocol_pin_rejects_changed_rules(monkeypatch, name, replacement):
    monkeypatch.setattr(writer, name, replacement)
    with pytest.raises(writer.PrivateDiagnosticRejected, match="protocol"):
        _preview()


@pytest.mark.parametrize("target", ("json", "hashlib"))
def test_writer_rejects_replaced_codec_without_invoking_callback(monkeypatch, target):
    touched = []

    def poison(*args, **kwargs):
        touched.append(target)
        raise AssertionError("diagnostic codec touched private caller data")

    if target == "json":
        monkeypatch.setattr(writer, target, SimpleNamespace(dumps=poison))
    else:
        monkeypatch.setattr(writer, target, SimpleNamespace(sha256=poison))
    with pytest.raises(writer.PrivateDiagnosticRejected, match="protocol"):
        _preview()
    assert touched == []


@pytest.mark.parametrize(("cls", "field"), (
    ("event", "component"),
    ("event", "sequence"),
    ("preview", "canonical_jsonl"),
    ("preview", "action_authorized"),
    ("preview", "trusted_audit_evidence"),
))
def test_writer_rejects_replaced_dataclass_descriptors_before_getter(
    monkeypatch, cls, field,
):
    touched = []

    def poison(_self):
        touched.append(field)
        return False

    # Construct the fixture BEFORE installing a poisoned slot. Otherwise
    # the dataclass constructor itself would hit the malicious property,
    # rather than testing the renderer's preaccess refusal.
    prior_event = writer.PrivateDiagnosticEvent(
        10, "memory", "recovery", "deferred", "nonreplay_required",
    )
    target = writer.PrivateDiagnosticEvent if cls == "event" else writer.PrivateDiagnosticPreview
    monkeypatch.setattr(target, field, property(poison))
    with pytest.raises(writer.PrivateDiagnosticRejected, match="protocol"):
        writer.render_private_diagnostic_ledger(
            (prior_event,), start_sequence=10, retained_anchor_sha256="a" * 64,
        )
    assert touched == []


@pytest.mark.parametrize(("rule", "replacement"), (
    ("_DOMAIN", b"ARK-bad-verifier\0"),
    ("_SHA", object()),
    ("_COMPONENT", frozenset(("memory", "SECRET"))),
    ("_STAGE", frozenset(("x",))),
    ("_OUTCOME", frozenset(("authorized",))),
    ("_REASON", frozenset(("payload",))),
    ("_KEYS", frozenset(("v", "seq"))),
    ("_MAX_EVENTS", 129),
    ("_MAX_SEQUENCE", 123),
    ("_MAX_BYTES", 999999),
))
def test_verifier_refuses_changed_protocol_before_parsing(monkeypatch, rule, replacement):
    monkeypatch.setattr(verifier, rule, replacement)
    with pytest.raises(verifier.PrivateDiagnosticVerificationRejected, match="protocol"):
        _verify()


@pytest.mark.parametrize("codec", ("json", "hashlib"))
def test_verifier_refuses_replaced_private_parser_or_hash(monkeypatch, codec):
    touched = []

    def poison(*args, **kwargs):
        touched.append(codec)
        raise AssertionError("private input reached a substituted codec")

    if codec == "json":
        monkeypatch.setattr(
            verifier, codec, SimpleNamespace(loads=poison, dumps=poison),
        )
    else:
        monkeypatch.setattr(verifier, codec, SimpleNamespace(sha256=poison))
    with pytest.raises(verifier.PrivateDiagnosticVerificationRejected, match="protocol"):
        _verify()
    assert touched == []


@pytest.mark.parametrize("denial", (
    "audit_authenticated", "cleanup_authorized",
    "tool_execution_authorized", "private_data_export_authorized",
))
def test_verifier_deny_only_result_descriptors_are_pinned_preaccess(
    monkeypatch, denial,
):
    touched = []

    def forged(_self):
        touched.append(denial)
        return False

    monkeypatch.setattr(verifier.PrivateDiagnosticVerification, denial, property(forged))
    with pytest.raises(verifier.PrivateDiagnosticVerificationRejected, match="protocol"):
        _verify()
    assert touched == []


@pytest.mark.parametrize(("changes", "expected_message"), (
    ({"count": 1}, "record count"),
    ({"count": 3}, "record count"),
    ({"start": 9}, "record content"),
    ({"start": True}, "envelope"),
    ({"count": True}, "envelope"),
    ({"tip": "b" * 64}, "tip mismatch"),
    ({"anchor": "b" * 64}, "record content"),
    ({"anchor": "A" * 64}, "envelope"),
))
def test_retained_count_tip_start_and_anchor_fences(changes, expected_message):
    with pytest.raises(
        verifier.PrivateDiagnosticVerificationRejected, match=expected_message,
    ):
        _verify(**changes)


@pytest.mark.parametrize("kind", (
    "drop_last", "duplicate_last", "swap_lines", "missing_newline",
    "double_newline", "unicode", "unknown_key", "duplicate_key",
    "unknown_reason", "bool_sequence", "pretty_json", "reordered_keys",
    "invalid_json", "unbounded",
))
def test_noncanonical_or_tampered_jsonl_is_rejected(kind):
    original = _preview().canonical_jsonl
    lines = original.splitlines()
    row = json.loads(lines[0])
    if kind == "drop_last":
        changed = lines[0] + "\n"
    elif kind == "duplicate_last":
        changed = original + lines[1] + "\n"
    elif kind == "swap_lines":
        changed = lines[1] + "\n" + lines[0] + "\n"
    elif kind == "missing_newline":
        changed = original.rstrip("\n")
    elif kind == "double_newline":
        changed = original + "\n"
    elif kind == "unicode":
        changed = original.replace('"memory"', '"memøry"')
    elif kind == "unknown_key":
        row["raw_secret"] = "DO_NOT_EXPORT"
        changed = json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" + lines[1] + "\n"
    elif kind == "duplicate_key":
        changed = lines[0].replace('"v":1', '"v":1,"v":1') + "\n" + lines[1] + "\n"
    elif kind == "unknown_reason":
        row["reason"] = "DO_NOT_EXPORT"
        changed = json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" + lines[1] + "\n"
    elif kind == "bool_sequence":
        row["seq"] = True
        changed = json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" + lines[1] + "\n"
    elif kind == "pretty_json":
        changed = json.dumps(row, indent=2) + "\n" + lines[1] + "\n"
    elif kind == "reordered_keys":
        changed = json.dumps(row) + "\n" + lines[1] + "\n"
    elif kind == "invalid_json":
        changed = "{garbage}\n" + lines[1] + "\n"
    else:
        changed = " " * 50_001
    with pytest.raises(verifier.PrivateDiagnosticVerificationRejected) as err:
        _verify(changed)
    assert "DO_NOT_EXPORT" not in str(err.value)


def test_independent_digest_recomputation_matches_existing_writer_protocol():
    preview = _preview()
    first = json.loads(preview.canonical_jsonl.splitlines()[0])
    data = [
        1, first["seq"], first["component"], first["stage"],
        first["outcome"], first["reason"], "a" * 64,
    ]
    expected = hashlib.sha256(
        b"ARK-detached-private-diagnostics-v1\0"
        + json.dumps(data, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()
    assert first["sha256"] == expected
    assert _verify().final_sha256 == preview.final_sha256

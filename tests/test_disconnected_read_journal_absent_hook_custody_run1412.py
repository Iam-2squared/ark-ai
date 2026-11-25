"""Run1412: detached read journal pins true absence of carrier class hooks."""

from __future__ import annotations

import subprocess
import sys

import pytest

import ark.agency.disconnected_read_journal as journal

_CARRIERS = ("ReadReceipt", "ReadJournalWitness", "ReadJournalSnapshot")
_LOOKUP_HOOKS = ("__getattribute__", "__getattr__")


def _set_class_attribute(
    carrier: type,
    name: str,
    value: object,
) -> tuple[bool, object | None]:
    namespace = vars(carrier)
    was_present = name in namespace
    original = namespace.get(name)
    type.__setattr__(carrier, name, value)
    return was_present, original


def _restore_class_attribute(
    carrier: type,
    name: str,
    original: tuple[bool, object | None],
) -> None:
    was_present, value = original
    if was_present:
        type.__setattr__(carrier, name, value)
    else:
        type.__delattr__(carrier, name)


@pytest.mark.parametrize(
    ("carrier_name", "hook"),
    ((carrier_name, hook) for carrier_name in _CARRIERS for hook in _LOOKUP_HOOKS),
)
@pytest.mark.parametrize("replacement_kind", ["explicit-none", "sentinel-installed"])
def test_absent_read_carrier_lookup_hook_requires_namespace_absence(
    carrier_name: str,
    hook: str,
    replacement_kind: str,
) -> None:
    carrier = getattr(journal, carrier_name)
    replacement = (
        None
        if replacement_kind == "explicit-none"
        else journal._ABSENT_CLASS_HOOK
    )
    original = _set_class_attribute(carrier, hook, replacement)
    try:
        with pytest.raises(
            journal.ReadJournalRejected,
            match="carrier|witness|snapshot",
        ):
            journal._require_original_read_carriers()
    finally:
        _restore_class_attribute(carrier, hook, original)


@pytest.mark.parametrize(
    ("carrier_name", "replacement_kind"),
    [
        (carrier_name, replacement_kind)
        for carrier_name in _CARRIERS
        for replacement_kind in ("explicit-none", "sentinel-installed")
    ],
)
def test_absent_read_carrier_new_hook_is_rejected_in_an_isolated_process(
    carrier_name: str,
    replacement_kind: str,
) -> None:
    # Mutating and deleting __new__ can leave interpreter allocation-slot
    # state behind on some Python builds. Keep every special-slot probe isolated.
    script = f"""
import ark.agency.disconnected_read_journal as journal

carrier = getattr(journal, {carrier_name!r})
replacement = (
    None
    if {replacement_kind!r} == "explicit-none"
    else journal._ABSENT_CLASS_HOOK
)
type.__setattr__(carrier, "__new__", replacement)
try:
    journal._require_original_read_carriers()
except journal.ReadJournalRejected:
    pass
else:
    raise SystemExit("absent __new__ substitution was accepted")
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_replaced_absence_sentinel_is_rejected_before_carrier_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(journal, "_ABSENT_CLASS_HOOK", object())
    with pytest.raises(
        journal.ReadJournalRejected,
        match="synthetic READ carrier class changed",
    ):
        journal._require_original_read_carriers()


def test_joint_hook_vector_replacement_is_rejected_before_carrier_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    empty: tuple[object, ...] = ()
    monkeypatch.setattr(journal, "_CARRIER_HOOKS", empty)
    monkeypatch.setattr(journal, "_ORIGINAL_RECEIPT_HOOKS", empty)
    monkeypatch.setattr(journal, "_ORIGINAL_WITNESS_HOOKS", empty)

    with pytest.raises(
        journal.ReadJournalRejected,
        match="synthetic READ carrier class changed",
    ):
        journal._require_original_read_carriers()


def test_joint_snapshot_type_alias_replacement_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    replacement = type("ReplacementReadJournalSnapshot", (), {})
    monkeypatch.setattr(journal, "ReadJournalSnapshot", replacement)
    monkeypatch.setattr(journal, "_SNAPSHOT_TYPE", replacement)

    with pytest.raises(
        journal.ReadJournalRejected,
        match="synthetic READ carrier class changed",
    ):
        journal._require_original_snapshot_class()


def test_original_read_carrier_epoch_remains_valid() -> None:
    journal._require_original_read_carriers()
    journal._require_original_snapshot_class()

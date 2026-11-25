"""Run1416: Personal Context replay carriers pin true hook absence."""

from __future__ import annotations

import subprocess
import sys


def test_witness_and_receipt_reject_none_and_sentinel_hook_installation() -> None:
    script = r"""
import ark.personal_context_replay_ledger as replay

replay._require_original_witness_carrier()
replay._require_original_receipt_constructor()

def require_rejected(guard, label):
    try:
        guard()
    except replay.OfflineContextReplayRejected:
        return
    raise AssertionError(f"{label} was accepted")

for carrier, hooks, sentinel, guard in (
    (
        replay.OfflineContextReplayWitness,
        replay._WITNESS_HOOKS,
        replay._WITNESS_HOOK_ABSENT,
        replay._require_original_witness_carrier,
    ),
    (
        replay.OfflineContextReplayReceipt,
        replay._RECEIPT_HOOKS,
        replay._RECEIPT_HOOK_ABSENT,
        replay._require_original_receipt_constructor,
    ),
):
    for hook in hooks:
        if hook == "__init__":
            continue
        for replacement in (None, sentinel):
            type.__setattr__(carrier, hook, replacement)
            require_rejected(guard, f"{carrier.__name__}.{hook}")
            type.__delattr__(carrier, hook)
            guard()

def replace_and_restore(module, name, replacement, guard):
    original = getattr(module, name)
    setattr(module, name, replacement)
    require_rejected(guard, name)
    setattr(module, name, original)
    guard()

replace_and_restore(
    replay, "_WITNESS_HOOK_ABSENT", object(),
    replay._require_original_witness_carrier,
)
replace_and_restore(
    replay, "_WITNESS_HOOKS", tuple(list(replay._WITNESS_HOOKS)),
    replay._require_original_witness_carrier,
)
replace_and_restore(
    replay, "_ORIGINAL_WITNESS_HOOKS",
    tuple(list(replay._ORIGINAL_WITNESS_HOOKS)),
    replay._require_original_witness_carrier,
)
replace_and_restore(
    replay, "_ORIGINAL_WITNESS_EPOCH",
    tuple(list(replay._ORIGINAL_WITNESS_EPOCH)),
    replay._require_original_witness_carrier,
)
replace_and_restore(
    replay, "_RECEIPT_HOOK_ABSENT", object(),
    replay._require_original_receipt_constructor,
)
replace_and_restore(
    replay, "_RECEIPT_HOOKS", tuple(list(replay._RECEIPT_HOOKS)),
    replay._require_original_receipt_constructor,
)
replace_and_restore(
    replay, "_ORIGINAL_RECEIPT_HOOKS",
    tuple(list(replay._ORIGINAL_RECEIPT_HOOKS)),
    replay._require_original_receipt_constructor,
)
replace_and_restore(
    replay, "_ORIGINAL_RECEIPT_EPOCH",
    tuple(list(replay._ORIGINAL_RECEIPT_EPOCH)),
    replay._require_original_receipt_constructor,
)

old_witness_type = replay._WITNESS_TYPE
old_witness_alias = replay.OfflineContextReplayWitness
replacement_witness_type = type("ReplacementWitness", (), {})
replay._WITNESS_TYPE = replacement_witness_type
replay.OfflineContextReplayWitness = replacement_witness_type
require_rejected(
    replay._require_original_witness_carrier,
    "joint witness type-alias replacement",
)
replay._WITNESS_TYPE = old_witness_type
replay.OfflineContextReplayWitness = old_witness_alias
replay._require_original_witness_carrier()

old_receipt_type = replay._RECEIPT_TYPE
old_receipt_alias = replay.OfflineContextReplayReceipt
replacement_receipt_type = type("ReplacementReceipt", (), {})
replay._RECEIPT_TYPE = replacement_receipt_type
replay.OfflineContextReplayReceipt = replacement_receipt_type
require_rejected(
    replay._require_original_receipt_constructor,
    "joint receipt type-alias replacement",
)
replay._RECEIPT_TYPE = old_receipt_type
replay.OfflineContextReplayReceipt = old_receipt_alias
replay._require_original_receipt_constructor()
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_witness_hook_substitution_is_rejected_before_digest_callback() -> None:
    script = r"""
import ark.personal_context_replay_ledger as replay

calls = []
original_sha256 = replay.hashlib.sha256

def forbidden_sha256(*args, **kwargs):
    calls.append(True)
    raise AssertionError("digest callback must not run")

replay.hashlib.sha256 = forbidden_sha256
type.__setattr__(
    replay.OfflineContextReplayWitness,
    "__getattr__",
    None,
)
try:
    replay.genesis_offline_context_replay_witness()
except replay.OfflineContextReplayRejected as exc:
    assert "witness" in str(exc)
else:
    raise AssertionError("absent witness hook substitution was accepted")
assert calls == []
replay.hashlib.sha256 = original_sha256
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

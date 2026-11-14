"""Personal Context replay CAS denies altered receipt classes before SQLite.

Disposable hash-only fixtures and subprocess mutations; no user context is
disclosed, no external effect executes, and no consent is inferred.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

_SCRIPT = """
import hashlib
import sys
from pathlib import Path

import ark.personal_context_replay_ledger as replay
from ark.personal_context_offline_preview import (
    OfflineContextFixture, build_offline_context_preview,
)
from ark.personal_context_request_binding import (
    OfflineContextRequestBinding, bind_offline_context_request,
)

text = "synthetic-private-content"
fixture = OfflineContextFixture(
    "rec_" + "c" * 32, "a" * 64, "b" * 64,
    text, hashlib.sha256(text.encode()).hexdigest(), 1000,
)
preview = build_offline_context_preview(
    (fixture,), owner_digest="a" * 64,
    allowed_scope_digests=("b" * 64,), observed_at_ms=100,
)
binding = bind_offline_context_request("ctxreq_" + "1" * 64, preview)
ledger = replay.DisconnectedContextReplayLedger(Path(sys.argv[1]), create=True)
retained = replay.genesis_offline_context_replay_witness()
called = []
slot = sys.argv[2]

def hostile(*args, **kwargs):
    called.append(slot)
    raise AssertionError("mutated binding code executed")

def no_sqlite(*args, **kwargs):
    raise AssertionError("SQLite opened before rejecting forged binding")

if slot == "__new__":
    OfflineContextRequestBinding.__new__ = staticmethod(hostile)
elif slot.startswith("__"):
    setattr(OfflineContextRequestBinding, slot, hostile)
else:
    setattr(OfflineContextRequestBinding, slot, property(hostile))
replay.DisconnectedContextReplayLedger._open = no_sqlite

try:
    ledger.reserve(binding, retained=retained)
except replay.OfflineContextReplayRejected as exc:
    assert "untrusted context binding metadata or authority" in str(exc), str(exc)
else:
    raise AssertionError("forged Personal Context binding accepted")
assert called == [], called
"""


@pytest.mark.parametrize("slot", [
    "request_id", "owner_digest", "context_digest", "record_count",
    "binding_digest", "consent_verified", "revocation_freshness_verified",
    "external_export_authorized", "tool_dispatch_authorized",
    "retention_authorized", "__init__", "__new__", "__getattribute__",
    "__getattr__",
])
def test_context_binding_slots_refused_before_sqlite(tmp_path, slot):
    process = subprocess.run(
        [
            sys.executable, "-c", _SCRIPT,
            str(tmp_path / f"context-{slot}.sqlite"), slot,
        ],
        capture_output=True, text=True, check=False, timeout=20,
    )
    assert process.returncode == 0, process.stdout + process.stderr


def test_clean_context_replay_still_reserves_once_and_denies_disclosure(tmp_path):
    import hashlib
    from pathlib import Path

    from ark.personal_context_offline_preview import (
        OfflineContextFixture,
        build_offline_context_preview,
    )
    from ark.personal_context_replay_ledger import (
        DisconnectedContextReplayLedger,
        OfflineContextReplayRejected,
        genesis_offline_context_replay_witness,
    )
    from ark.personal_context_request_binding import bind_offline_context_request

    payload = "private test fixture"
    record = OfflineContextFixture(
        "rec_" + "c" * 32, "a" * 64, "b" * 64,
        payload, hashlib.sha256(payload.encode()).hexdigest(), 1000,
    )
    preview = build_offline_context_preview(
        (record,), owner_digest="a" * 64,
        allowed_scope_digests=("b" * 64,), observed_at_ms=100,
    )
    binding = bind_offline_context_request("ctxreq_" + "1" * 64, preview)
    ledger = DisconnectedContextReplayLedger(
        Path(tmp_path / "normal-context.sqlite"), create=True,
    )
    genesis = genesis_offline_context_replay_witness()
    receipt = ledger.reserve(binding, retained=genesis)
    assert receipt.witness.count == 1
    assert receipt.context_disclosure_authorized is False
    assert receipt.tool_dispatch_authorized is False
    assert payload.encode() not in (tmp_path / "normal-context.sqlite").read_bytes()
    with pytest.raises(OfflineContextReplayRejected, match="duplicate"):
        ledger.reserve(binding, retained=receipt.witness)

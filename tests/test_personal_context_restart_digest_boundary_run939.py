"""A detached context digest is stable across processes but never consent.

Only fabricated two-scope, in-memory strings are used. The subprocess
exposes no private fixture content, real data, credentials or tool execution.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys

import pytest

from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    build_offline_context_preview,
)

_OWNER = "a" * 64
_SCOPE_A = "b" * 64
_SCOPE_B = "c" * 64
_SECRET = "FAKE_LOCAL_ONLY_CONTEXT_939"
_CHILD = r"""
import hashlib
import json
import sys

from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    OfflineContextPreviewRejected,
    build_offline_context_preview,
    verify_offline_context_preview,
)

owner, scope_a, scope_b, prior_digest, mode = sys.argv[1:]
secret = "FAKE_LOCAL_ONLY_CONTEXT_939"
second = "second synthetic fixture"
if mode == "content":
    second = "changed synthetic fixture"
other_scope = "d" * 64 if mode == "scope" else scope_b
expiry = 100 if mode == "expiry" else 300
rows = (
    OfflineContextFixture(
        "rec_" + "0" * 31 + "1", owner, scope_a,
        secret, hashlib.sha256(secret.encode()).hexdigest(), 200,
    ),
    OfflineContextFixture(
        "rec_" + "0" * 31 + "2", owner, other_scope,
        second, hashlib.sha256(second.encode()).hexdigest(), expiry,
    ),
)
try:
    preview = build_offline_context_preview(
        rows, owner_digest=owner,
        allowed_scope_digests=(scope_a, scope_b), observed_at_ms=100,
    )
    verify_offline_context_preview(
        preview, rows, owner_digest=owner,
        allowed_scope_digests=(scope_a, scope_b), observed_at_ms=100,
        retained_local_digest=prior_digest,
    )
except OfflineContextPreviewRejected:
    print(json.dumps({"accepted": False}))
else:
    print(json.dumps({
        "accepted": True,
        "digest": preview.local_digest,
        "ids": preview.record_ids,
        "authority": (
            preview.consent_verified,
            preview.external_export_authorized,
            preview.tool_dispatch_authorized,
            preview.retention_authorized,
        ),
    }))
"""


@pytest.mark.parametrize("variant", ("same", "content", "scope", "expiry"))
def test_context_retained_digest_rechecked_after_process_restart(variant: str) -> None:
    first = OfflineContextFixture(
        "rec_" + "0" * 31 + "1", _OWNER, _SCOPE_A, _SECRET,
        hashlib.sha256(_SECRET.encode()).hexdigest(), 200,
    )
    second_content = "second synthetic fixture"
    second = OfflineContextFixture(
        "rec_" + "0" * 31 + "2", _OWNER, _SCOPE_B, second_content,
        hashlib.sha256(second_content.encode()).hexdigest(), 300,
    )
    parent = build_offline_context_preview(
        (first, second), owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE_A, _SCOPE_B), observed_at_ms=100,
    )
    process = subprocess.run(
        [sys.executable, "-c", _CHILD, _OWNER, _SCOPE_A, _SCOPE_B,
         parent.local_digest, variant],
        check=True, capture_output=True, text=True, timeout=30,
    )
    assert _SECRET not in process.stdout
    assert _SECRET not in process.stderr
    assert _SECRET not in repr(parent)
    receipt = json.loads(process.stdout)
    if variant == "same":
        assert receipt == {
            "accepted": True,
            "digest": parent.local_digest,
            "ids": list(parent.record_ids),
            "authority": [False, False, False, False],
        }
    else:
        assert receipt == {"accepted": False}

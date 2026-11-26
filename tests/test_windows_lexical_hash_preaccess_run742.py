"""Windows synthetic SQLite labels must not reach rebound hash helpers."""

from __future__ import annotations

import hashlib
from types import SimpleNamespace

import pytest

from ark import disconnected_windows_sqlite_lexical as reviewer

PATH = r"C:\ark\sensitive_local_memory.sqlite3"
SECRET = "PRIVATE_PATH_CONTENT_RUN742"


def test_original_synthetic_lexical_receipt_remains_deny_only():
    receipt = reviewer.review_windows_sqlite_lexical_path(PATH)
    assert len(receipt.path_sha256) == 64
    assert len(receipt.sidecar_sha256) == 3
    assert receipt.actual_open_authorized is False
    assert receipt.sqlite_snapshot_coherent is False
    assert receipt.filesystem_identity_verified is False
    assert receipt.tool_execution_authorized is False
    assert PATH not in repr(receipt)


@pytest.mark.parametrize("replacement", ("helper", "hash_module", "hash_function"))
def test_substituted_hashing_boundary_rejected_before_receiving_path(
    replacement, monkeypatch,
):
    observed = []

    def poison(*args, **kwargs):
        observed.append((args, kwargs))
        raise AssertionError("synthetic pathname reached untrusted hash function")

    if replacement == "helper":
        monkeypatch.setattr(reviewer, "_digest", poison)
    elif replacement == "hash_module":
        monkeypatch.setattr(
            reviewer, "hashlib", SimpleNamespace(sha256=hashlib.sha256),
        )
    else:
        monkeypatch.setattr(
            reviewer, "hashlib", SimpleNamespace(sha256=poison),
        )

    with pytest.raises(reviewer.WindowsSQLiteLexicalRejected, match="protocol") as err:
        reviewer.review_windows_sqlite_lexical_path(PATH)
    assert not observed
    assert PATH not in str(err.value)
    assert SECRET not in str(err.value)

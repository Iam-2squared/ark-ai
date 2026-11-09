"""Run749: no substituted seal slot/authority getter may read synthetic file custody.

The source is a local fixture only. A matching seal does not prove historical
authorship, WAL atomicity, external consent or permission to mutate data.
"""

from __future__ import annotations

import pytest

from ark import disconnected_file_seal as seal


def _file(tmp_path):
    path = tmp_path / "synthetic-private-fixture.db"
    path.write_bytes(b"fixture bytes for local read-only testing")
    return path


@pytest.mark.parametrize("descriptor", (
    "source_sha256", "size_bytes", "path_sha256",
    "independent_custody_proven", "source_authenticated",
    "wal_snapshot_verified", "context_disclosure_authorized",
    "file_mutation_authorized", "__init__", "__getattr__",
))
@pytest.mark.parametrize("operation", ("capture", "review"))
def test_replaced_class_carrier_rejected_before_os_open(
    tmp_path, monkeypatch, descriptor, operation,
):
    path = _file(tmp_path)
    retained = seal.capture_disconnected_file_seal(path)
    calls = []

    def poisoned(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("injected seal carrier executed")

    def no_open(*args, **kwargs):
        raise AssertionError("file should not be opened")

    replacement = (
        poisoned if descriptor in ("__init__", "__getattr__")
        else property(poisoned)
    )
    with monkeypatch.context() as patch:
        patch.setattr(seal.DisconnectedFileSeal, descriptor, replacement, raising=False)
        patch.setattr(seal.os, "open", no_open)
        with pytest.raises(
            seal.DisconnectedFileSealRejected, match="seal carrier changed",
        ):
            if operation == "capture":
                seal.capture_disconnected_file_seal(path)
            else:
                seal.review_disconnected_file_seal(path, retained)
    assert calls == []


@pytest.mark.parametrize("vector,other", (
    ("_SEAL_FIELD_NAMES", ("tampered",)),
    ("_SEAL_DENIAL_NAMES", ("file_mutation_authorized",)),
    ("_SEAL_HOOK_NAMES", ("__init__",)),
))
def test_protocol_vector_replacement_denied_before_private_read(
    tmp_path, monkeypatch, vector, other,
):
    path = _file(tmp_path)
    with monkeypatch.context() as patch:
        patch.setattr(seal, vector, other)
        with pytest.raises(
            seal.DisconnectedFileSealRejected, match="seal carrier changed",
        ):
            seal.capture_disconnected_file_seal(path)


def test_reflection_helper_replacement_denied_before_retained_read(
    tmp_path, monkeypatch,
):
    path = _file(tmp_path)
    prior = seal.capture_disconnected_file_seal(path)
    called = []

    def poisoned(*args, **kwargs):
        called.append((args, kwargs))
        raise AssertionError("untrusted reflected field enumerator called")

    with monkeypatch.context() as patch:
        patch.setattr(seal, "fields", poisoned)
        with pytest.raises(
            seal.DisconnectedFileSealRejected, match="seal carrier changed",
        ):
            seal.review_disconnected_file_seal(path, prior)
    assert called == []


def test_reentrant_read_cannot_replace_result_field_slot(tmp_path, monkeypatch):
    path = _file(tmp_path)
    original = seal._parents
    called = []

    def poisoned(*args, **kwargs):
        called.append((args, kwargs))
        raise AssertionError("forged source digest getter executed")

    with monkeypatch.context() as patch:
        def inject(candidate):
            result = original(candidate)
            patch.setattr(
                seal.DisconnectedFileSeal, "source_sha256", property(poisoned),
            )
            return result

        patch.setattr(seal, "_parents", inject)
        with pytest.raises(
            seal.DisconnectedFileSealRejected, match="seal carrier changed",
        ):
            seal.capture_disconnected_file_seal(path)
    assert called == []


def test_unmodified_file_seal_remains_read_only_and_non_authorizing(tmp_path):
    path = _file(tmp_path)
    retained = seal.capture_disconnected_file_seal(path)
    current = seal.review_disconnected_file_seal(path, retained)
    assert current == retained
    assert current.file_mutation_authorized is False
    assert current.context_disclosure_authorized is False
    assert current.wal_snapshot_verified is False

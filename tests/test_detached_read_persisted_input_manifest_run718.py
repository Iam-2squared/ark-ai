"""Write-once READ input digest manifests remain independent, deny-only evidence."""

from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor

import pytest

from ark.agency.disconnected_read_input_manifest import (
    ReadInputManifestRejected,
    load_read_input_manifest,
    review_persisted_read_input_binding,
    write_read_input_manifest_once,
)
from ark.agency.disconnected_read_journal import (
    ReadJournalSnapshot,
    ReadJournalWitness,
    ReadReceipt,
    _chain,
    genesis_witness,
)
from ark.agency.disconnected_read_recovery_schedule import ReadRecoveryStep

REQUEST = "req_" + "a" * 32
OTHER_REQUEST = "req_" + "b" * 32
A = "step_" + "1" * 16
B = "step_" + "2" * 16
IA, IB, IC = "c" * 64, "d" * 64, "e" * 64
RA, RB = "f" * 64, "a" * 64
INPUTS = ((A, IA), (B, IB))


def _recovered(first_input=IA):
    rows = (
        ReadReceipt(REQUEST, A, "math.sum", first_input, RA),
        ReadReceipt(REQUEST, B, "text.stats", IB, RB),
    )
    tip = genesis_witness().tip_sha256
    for index, row in enumerate(rows, 1):
        tip = _chain(tip, index, row)
    retained = ReadJournalWitness(len(rows), tip)
    snapshot = ReadJournalSnapshot(retained, rows)
    steps = (
        ReadRecoveryStep(A, "math.sum", (), "SUCCEEDED", RA),
        ReadRecoveryStep(B, "text.stats", (A,), "SUCCEEDED", RB),
    )
    return steps, snapshot, retained


def test_write_once_reopen_and_readonly_recovery_bind_exact_inputs(tmp_path):
    path = tmp_path / "detached-expected-inputs.json"
    saved = write_read_input_manifest_once(path, REQUEST, INPUTS)
    raw = path.read_bytes()
    before = path.stat().st_mtime_ns
    loaded = load_read_input_manifest(path, expected_sha256=saved.artifact_sha256)
    assert loaded == saved
    assert loaded.expected_inputs == INPUTS
    assert len(saved.artifact_sha256) == 64
    assert saved.backend_dispatched is False
    assert saved.independent_custody_proven is False
    assert saved.automatic_replay_authorized is False
    assert saved.external_result_proven is False
    result = review_persisted_read_input_binding(
        path, REQUEST, *_recovered(), expected_manifest_sha256=saved.artifact_sha256,
    )
    assert result.successful_step_ids == (A, B)
    assert result.backend_dispatched is False
    assert result.external_result_proven is False
    assert result.independent_custody_proven is False
    assert path.read_bytes() == raw
    assert path.stat().st_mtime_ns == before


def test_rehashed_journal_receipt_with_wrong_input_fails_retained_manifest(tmp_path):
    path = tmp_path / "manifest.json"
    saved = write_read_input_manifest_once(path, REQUEST, INPUTS)
    from ark.agency.disconnected_read_input_binding_review import ReadInputBindingRejected

    with pytest.raises(ReadInputBindingRejected, match="input digest"):
        review_persisted_read_input_binding(
            path, REQUEST, *_recovered(first_input=IC),
            expected_manifest_sha256=saved.artifact_sha256,
        )


def test_wrong_request_fails_even_with_valid_manifest_and_journal(tmp_path):
    path = tmp_path / "manifest.json"
    saved = write_read_input_manifest_once(path, REQUEST, INPUTS)
    with pytest.raises(ReadInputManifestRejected, match="request"):
        review_persisted_read_input_binding(
            path, OTHER_REQUEST, *_recovered(),
            expected_manifest_sha256=saved.artifact_sha256,
        )


@pytest.mark.parametrize("bad", (
    ((A, IA), (A, IB)),
    ((A, IA), (B, True)),
    ((A, IA), (B, "Z" * 64)),
    ((A, IA), ("other", IB)),
    [(A, IA)],
))
def test_invalid_or_duplicate_input_manifest_rejected_before_creating_file(
    tmp_path, bad,
):
    path = tmp_path / "not-created.json"
    with pytest.raises(ReadInputManifestRejected):
        write_read_input_manifest_once(path, REQUEST, bad)
    assert not path.exists()


def test_write_once_never_truncates_existing_original_or_partial_file(tmp_path):
    path = tmp_path / "existing.json"
    original = write_read_input_manifest_once(path, REQUEST, INPUTS)
    before = path.read_bytes()
    with pytest.raises(ReadInputManifestRejected, match="creation refused"):
        write_read_input_manifest_once(path, REQUEST, ((A, IC),))
    assert path.read_bytes() == before
    assert load_read_input_manifest(path) == original

    partial = tmp_path / "partial.json"
    partial.write_bytes(b'{"incomplete":')
    with pytest.raises(ReadInputManifestRejected):
        write_read_input_manifest_once(partial, REQUEST, INPUTS)
    assert partial.read_bytes() == b'{"incomplete":'
    with pytest.raises(ReadInputManifestRejected):
        load_read_input_manifest(partial)


def test_competing_writers_have_exactly_one_creator(tmp_path):
    path = tmp_path / "racing.json"

    def writer(value):
        try:
            return write_read_input_manifest_once(path, REQUEST, ((A, value),))
        except ReadInputManifestRejected:
            return None

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(writer, [IA, IC] * 4))
    winners = [result for result in outcomes if result is not None]
    assert len(winners) == 1
    assert load_read_input_manifest(path) == winners[0]


def test_changed_canonical_payload_cannot_reuse_retained_sha(tmp_path):
    path = tmp_path / "manifest.json"
    saved = write_read_input_manifest_once(path, REQUEST, INPUTS)
    data = json.loads(path.read_text(encoding="ascii"))
    data["expected_inputs"][0][1] = IC
    # The forged envelope can be made internally consistent only by
    # recomputing its digest, which the independent caller anchor rejects.
    path.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n")
    with pytest.raises(ReadInputManifestRejected, match="digest/canonical"):
        load_read_input_manifest(path, expected_sha256=saved.artifact_sha256)


def test_noncanonical_whitespace_and_reordered_keys_are_not_accepted(tmp_path):
    path = tmp_path / "manifest.json"
    write_read_input_manifest_once(path, REQUEST, INPUTS)
    data = json.loads(path.read_text(encoding="ascii"))
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="ascii")
    with pytest.raises(ReadInputManifestRejected, match="digest/canonical"):
        load_read_input_manifest(path)


@pytest.mark.parametrize("payload", (
    b"",
    b"[]\n",
    b"{}\n",
    b"invalid\n",
    b"x" * 8193,
    b'{"not": "terminated"}',
))
def test_broken_artifacts_never_return_a_partial_manifest(tmp_path, payload):
    path = tmp_path / "broken.json"
    path.write_bytes(payload)
    with pytest.raises(ReadInputManifestRejected):
        load_read_input_manifest(path)


def test_missing_file_or_invalid_retained_hash_fails_closed(tmp_path):
    path = tmp_path / "absent.json"
    with pytest.raises(ReadInputManifestRejected, match="read refused"):
        load_read_input_manifest(path)
    write_read_input_manifest_once(path, REQUEST, INPUTS)
    for digest in (None, "f" * 64, True, "F" * 64):
        if digest is None:
            assert load_read_input_manifest(path).request_id == REQUEST
        else:
            with pytest.raises(ReadInputManifestRejected):
                load_read_input_manifest(path, expected_sha256=digest)


def test_empty_success_manifest_is_diagnostic_only(tmp_path):
    path = tmp_path / "empty.json"
    saved = write_read_input_manifest_once(path, REQUEST, ())
    assert saved.expected_inputs == ()
    assert saved.automatic_replay_authorized is False


def test_manifest_existing_symlink_is_not_followed(tmp_path):
    original = tmp_path / "original.txt"
    original.write_text("unchanged")
    link = tmp_path / "linked.json"
    try:
        os.symlink(original, link)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation disallowed on this runner")
    with pytest.raises(ReadInputManifestRejected):
        write_read_input_manifest_once(link, REQUEST, INPUTS)
    with pytest.raises(ReadInputManifestRejected):
        load_read_input_manifest(link)
    assert original.read_text() == "unchanged"

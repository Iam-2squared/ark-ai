"""Create-only recovery archive for a hypothetical failed/blocked batch.

Stores step IDs, terminal labels and fixture digests only. The failure mask
comes from an independent caller-held tuple, NOT from the file. Restart
review re-simulates disconnected fixtures; it never proves a real failure,
authorizes dispatch, retries UNKNOWN WRITE or contacts a ToolBackend.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

from .disconnected_batch_cycle_archive import (
    DisconnectedBatchArchiveRejected,
    _path,
    _read_once,
)
from .disconnected_batch_failure_fixture import (
    DisconnectedFailureFixtureReceipt,
    simulate_disconnected_failure_fixture,
    verify_disconnected_failure_fixture,
)
from .disconnected_batch_plan import DisconnectedBatchPlan
from .disconnected_batch_schedule import DisconnectedBatchSchedule

_SCHEMA = "ARK-detached-failure-batch-archive-v1"
_MAX_BYTES = 8_192
_DENIALS = (
    "external_dispatch_authorized", "write_authorized",
    "automatic_replay_authorized", "failure_authenticated",
    "real_outcome_proven",
)


class DisconnectedFailureArchiveRejected(ValueError):
    """A synthetic terminal archive or its independently retained witness is invalid."""


@dataclass(frozen=True, slots=True)
class ArchivedDisconnectedFailure:
    file_sha256: str
    request_id: str
    plan_digest: str
    projection_digest: str
    fixture_digest: str
    failed_step_ids: tuple[str, ...]
    terminal_counts: tuple[int, int, int]

    @property
    def external_dispatch_authorized(self) -> bool:
        return False

    @property
    def write_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def failure_authenticated(self) -> bool:
        return False

    @property
    def real_outcome_proven(self) -> bool:
        return False


# The class denial methods must be the original definitions, not merely any
# callback returning False. Retain them before review/creation callbacks run.
_ORIGINAL_ARCHIVE_DENIALS = tuple(
    getattr(ArchivedDisconnectedFailure, key) for key in _DENIALS
)


def _require_original_archive_denials() -> None:
    if any(
        getattr(ArchivedDisconnectedFailure, key) is not original
        for key, original in zip(
            _DENIALS, _ORIGINAL_ARCHIVE_DENIALS, strict=True,
        )
    ):
        raise DisconnectedFailureArchiveRejected(
            "failure archive authority definition changed"
        )


def _receipt_epoch(receipt: DisconnectedFailureFixtureReceipt) -> tuple[object, ...]:
    if type(receipt) is not DisconnectedFailureFixtureReceipt:
        raise DisconnectedFailureArchiveRejected("exact hypothetical receipt required")
    return (
        receipt.request_id, receipt.plan_digest, receipt.schedule_digest,
        receipt.projection_digest, receipt.failed_step_ids,
        receipt.terminal_states, receipt.result_digests, receipt.fixture_digest,
    )


def _same_receipt_carriers(
    receipt: DisconnectedFailureFixtureReceipt,
    pinned: tuple[object, ...],
) -> bool:
    """Detect even equal-valued replacement across a verifier callback."""
    return all(
        current is prior
        for current, prior in zip(_receipt_epoch(receipt), pinned, strict=True)
    )


def _encode(receipt: DisconnectedFailureFixtureReceipt) -> bytes:
    values = _receipt_epoch(receipt)
    payload = {
        "schema": _SCHEMA,
        "request_id": values[0],
        "plan_digest": values[1],
        "schedule_digest": values[2],
        "projection_digest": values[3],
        "failed_step_ids": values[4],
        "terminal_states": values[5],
        "result_digests": values[6],
        "fixture_digest": values[7],
    }
    try:
        raw = json.dumps(
            payload, sort_keys=True, separators=(",", ":"),
            ensure_ascii=True, allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise DisconnectedFailureArchiveRejected("noncanonical failure archive") from exc
    if not 0 < len(raw) <= _MAX_BYTES:
        raise DisconnectedFailureArchiveRejected("failure archive byte budget exceeded")
    return raw


def _witness(sha256: str, receipt: DisconnectedFailureFixtureReceipt):
    _require_original_archive_denials()
    epoch = _receipt_epoch(receipt)
    counts = tuple(
        sum(state == target for _, state in receipt.terminal_states)
        for target in ("SUCCEEDED", "FAILED", "BLOCKED")
    )
    output = ArchivedDisconnectedFailure(
        sha256, receipt.request_id, receipt.plan_digest,
        receipt.projection_digest, receipt.fixture_digest,
        receipt.failed_step_ids, counts,
    )
    original = (
        output.file_sha256, output.request_id, output.plan_digest,
        output.projection_digest, output.fixture_digest,
        output.failed_step_ids, output.terminal_counts,
    )
    descriptors = _ORIGINAL_ARCHIVE_DENIALS

    def stable() -> None:
        if (
            type(output) is not ArchivedDisconnectedFailure
            or any(a is not b for a, b in zip(
                (output.file_sha256, output.request_id, output.plan_digest,
                 output.projection_digest, output.fixture_digest,
                 output.failed_step_ids, output.terminal_counts),
                original, strict=True,
            ))
            or not _same_receipt_carriers(receipt, epoch)
            or any(getattr(ArchivedDisconnectedFailure, key) is not descriptor
                   for key, descriptor in zip(_DENIALS, descriptors, strict=True))
        ):
            raise DisconnectedFailureArchiveRejected("failure archive witness changed")

    stable()
    for name in _DENIALS:
        if getattr(output, name) is not False:
            raise DisconnectedFailureArchiveRejected("failure archive gained authority")
        stable()
    return output


def review_disconnected_failure_archive(
    plan: DisconnectedBatchPlan,
    schedule: DisconnectedBatchSchedule,
    *,
    retained_plan_digest: str,
    retained_failed_step_ids: tuple[str, ...],
    path: Path,
    retained_file_sha256: str,
) -> ArchivedDisconnectedFailure:
    """Restart-safe read-only comparison with an independently held failure mask.

    File contents NEVER choose failed steps, and fixture re-simulation never
    dispatches actual actions or authenticates the claimed failure mask.
    """
    if (
        type(retained_file_sha256) is not str
        or len(retained_file_sha256) != 64
        or any(c not in "0123456789abcdef" for c in retained_file_sha256)
        or type(retained_failed_step_ids) is not tuple
    ):
        raise DisconnectedFailureArchiveRejected("independent archive pins required")
    _require_original_archive_denials()
    try:
        _path(path)
        expected = simulate_disconnected_failure_fixture(
            plan, schedule, retained_digest=retained_plan_digest,
            failed_step_ids=retained_failed_step_ids,
        )
        raw = _encode(expected)
        first, first_epoch = _read_once(path)
        if (
            first != raw
            or hashlib.sha256(first).hexdigest() != retained_file_sha256
        ):
            raise DisconnectedFailureArchiveRejected("failure archive content mismatch")
        second, second_epoch = _read_once(path)
        if second != first or second_epoch != first_epoch:
            raise DisconnectedFailureArchiveRejected("failure archive changed during read")
        again = simulate_disconnected_failure_fixture(
            plan, schedule, retained_digest=retained_plan_digest,
            failed_step_ids=retained_failed_step_ids,
        )
        if _encode(again) != raw:
            raise DisconnectedFailureArchiveRejected("failure fixture changed on replay")
        again_epoch = _receipt_epoch(again)
        # The final file read is a callback boundary. A custom read adapter
        # may mutate a frozen witness by reflection *after* _witness() has
        # checked it. Pin fields, receipt carriers and denial descriptors
        # across that last read, including equal-but-replaced carriers.
        source_epoch = _receipt_epoch(expected)
        descriptors = _ORIGINAL_ARCHIVE_DENIALS
        witness = _witness(retained_file_sha256, expected)
        witness_epoch = (
            witness.file_sha256, witness.request_id, witness.plan_digest,
            witness.projection_digest, witness.fixture_digest,
            witness.failed_step_ids, witness.terminal_counts,
        )

        def assert_final_epoch() -> None:
            if (
                type(witness) is not ArchivedDisconnectedFailure
                or any(now is not old for now, old in zip((
                    witness.file_sha256, witness.request_id, witness.plan_digest,
                    witness.projection_digest, witness.fixture_digest,
                    witness.failed_step_ids, witness.terminal_counts,
                ), witness_epoch, strict=True))
                or any(now is not old for now, old in zip(
                    _receipt_epoch(expected), source_epoch, strict=True,
                ))
                or any(getattr(ArchivedDisconnectedFailure, key) is not original
                       for key, original in zip(
                           _DENIALS, descriptors, strict=True,
                       ))
            ):
                raise DisconnectedFailureArchiveRejected(
                    "failure archive final witness/source changed"
                )

        assert_final_epoch()
        for name in _DENIALS:
            if getattr(witness, name) is not False:
                raise DisconnectedFailureArchiveRejected(
                    "failure archive final witness gained authority"
                )
            assert_final_epoch()
        final, final_epoch = _read_once(path)
        if final != first or final_epoch != first_epoch:
            raise DisconnectedFailureArchiveRejected("failure archive changed after review")
        if (
            _receipt_epoch(expected) != _receipt_epoch(again)
            or not _same_receipt_carriers(again, again_epoch)
        ):
            raise DisconnectedFailureArchiveRejected("failure receipt changed after review")
        assert_final_epoch()
        return witness
    except (DisconnectedBatchArchiveRejected, TypeError) as exc:
        raise DisconnectedFailureArchiveRejected(
            "failure archive path or fixture unavailable"
        ) from exc


def archive_disconnected_failure_fixture(
    receipt: DisconnectedFailureFixtureReceipt,
    plan: DisconnectedBatchPlan,
    schedule: DisconnectedBatchSchedule,
    *,
    retained_plan_digest: str,
    path: Path,
) -> ArchivedDisconnectedFailure:
    """Create, fsync and recheck one detached terminal file, without overwrite.

    If the operation fails after exclusive creation, leave the ambiguous
    artifact for manual review. Never auto-delete, retry or treat as consent.
    """
    original = _receipt_epoch(receipt)
    _require_original_archive_denials()
    try:
        _path(path)
        verify_disconnected_failure_fixture(
            receipt, plan, schedule, retained_digest=retained_plan_digest,
        )
        if not _same_receipt_carriers(receipt, original):
            raise DisconnectedFailureArchiveRejected("failure receipt changed before write")
        raw = _encode(receipt)
        sha256 = hashlib.sha256(raw).hexdigest()
        _require_original_archive_denials()
        if not _same_receipt_carriers(receipt, original):
            raise DisconnectedFailureArchiveRejected("failure receipt changed before create")
    except DisconnectedBatchArchiveRejected as exc:
        raise DisconnectedFailureArchiveRejected("failure archive path denied") from exc

    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    flags |= getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags, 0o600)
        with os.fdopen(fd, "wb") as handle:
            if handle.write(raw) != len(raw):
                raise DisconnectedFailureArchiveRejected("failure archive short write")
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise DisconnectedFailureArchiveRejected(
            "failure archive create-only write denied"
        ) from exc

    witness = review_disconnected_failure_archive(
        plan, schedule, retained_plan_digest=retained_plan_digest,
        retained_failed_step_ids=original[4], path=path, retained_file_sha256=sha256,
    )
    if not _same_receipt_carriers(receipt, original) or witness.fixture_digest != original[7]:
        raise DisconnectedFailureArchiveRejected("failure receipt changed after commit")
    return witness

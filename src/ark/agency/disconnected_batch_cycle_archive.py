"""Create-only local archive for a detached batch's deterministic mock cycle.

This archive holds ONLY fixture step IDs and digests. It never dispatches a
ToolBackend, replays a step, authenticates consent, or enables recovery of a
real-world WRITE. The separately retained file SHA must have independent
custody; neither the SHA nor the archive is signed evidence.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path

from .disconnected_batch_fixture_cycle import (
    DisconnectedBatchCycleReceipt,
    simulate_disconnected_batch_fixture_cycle,
    verify_disconnected_batch_fixture_cycle,
)
from .disconnected_batch_plan import (
    DisconnectedBatchPlan,
    verify_disconnected_batch_plan,
)
from .disconnected_batch_schedule import (
    DisconnectedBatchSchedule,
    verify_disconnected_batch_schedule,
)

_SCHEMA = "ARK-detached-batch-cycle-archive-v1"
_MAX_BYTES = 8_192
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DENIALS = (
    "external_dispatch_authorized", "write_authorized",
    "automatic_replay_authorized", "real_outcome_proven",
)


class DisconnectedBatchArchiveRejected(ValueError):
    """A synthetic receipt could not be safely archived or rechecked."""


@dataclass(frozen=True, slots=True)
class ArchivedDisconnectedBatchCycle:
    file_sha256: str
    request_id: str
    plan_digest: str
    cycle_digest: str

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
    def real_outcome_proven(self) -> bool:
        return False


def _path(path: Path) -> Path:
    if (
        type(path) is not type(Path("."))
        or not path.is_absolute()
        or ".." in path.parts
        or len(str(path)) > 4_096
    ):
        raise DisconnectedBatchArchiveRejected("exact absolute archive path required")
    try:
        for parent in path.parents:
            info = parent.lstat()
            if (
                not stat.S_ISDIR(info.st_mode)
                or stat.S_ISLNK(info.st_mode)
                or getattr(info, "st_file_attributes", 0) & 0x400
            ):
                raise DisconnectedBatchArchiveRejected(
                    "archive ancestor must be a real directory"
                )
    except OSError as exc:
        raise DisconnectedBatchArchiveRejected("archive ancestor cannot be inspected") from exc
    return path


def _epoch(info: os.stat_result) -> tuple[int, int, int, int]:
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_nlink != 1
        or getattr(info, "st_file_attributes", 0) & 0x400
    ):
        raise DisconnectedBatchArchiveRejected("archive must be a singly linked file")
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def _read_once(path: Path) -> tuple[bytes, tuple[int, int, int, int]]:
    _path(path)
    try:
        before = _epoch(path.lstat())
        if not 0 < before[2] <= _MAX_BYTES:
            raise DisconnectedBatchArchiveRejected("archive byte budget exceeded")
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(path, flags)
        try:
            opened = _epoch(os.fstat(fd))
            raw = os.read(fd, _MAX_BYTES + 1)
            at_end = _epoch(os.fstat(fd))
        finally:
            os.close(fd)
        after = _epoch(path.lstat())
    except OSError as exc:
        raise DisconnectedBatchArchiveRejected("archive cannot be read") from exc
    if (
        opened != before or at_end != before or after != before
        or len(raw) != before[2] or not 0 < len(raw) <= _MAX_BYTES
    ):
        raise DisconnectedBatchArchiveRejected("archive changed during read")
    _path(path)
    return raw, before


def _receipt_fields(receipt: DisconnectedBatchCycleReceipt) -> tuple[object, ...]:
    if type(receipt) is not DisconnectedBatchCycleReceipt:
        raise DisconnectedBatchArchiveRejected("exact fixture receipt required")
    fields = (
        receipt.request_id, receipt.plan_digest, receipt.schedule_digest,
        receipt.wave_result_hashes, receipt.cycle_digest,
    )
    if (
        any(type(value) is not str for value in (fields[0], fields[1], fields[2], fields[4]))
        or any(_SHA.fullmatch(value) is None for value in (fields[1], fields[2], fields[4]))
        or type(fields[3]) is not tuple
        or not 1 <= len(fields[3]) <= 24
        or any(
            type(wave) is not tuple
            or not wave
            or any(type(item) is not str or _SHA.fullmatch(item) is None for item in wave)
            for wave in fields[3]
        )
    ):
        raise DisconnectedBatchArchiveRejected("noncanonical fixture receipt")
    return fields


def _same_receipt_carriers(
    receipt: DisconnectedBatchCycleReceipt,
    pinned: tuple[object, ...],
) -> bool:
    """Reject even equal-valued carrier replacements across callbacks."""
    return all(
        current is original
        for current, original in zip(_receipt_fields(receipt), pinned, strict=True)
    )


def _raw(receipt: DisconnectedBatchCycleReceipt) -> bytes:
    request, plan_hash, schedule_hash, waves, cycle_hash = _receipt_fields(receipt)
    obj = {
        "schema": _SCHEMA, "request_id": request,
        "plan_digest": plan_hash, "schedule_digest": schedule_hash,
        "wave_result_hashes": waves, "cycle_digest": cycle_hash,
    }
    encoded = json.dumps(
        obj, sort_keys=True, ensure_ascii=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    if len(encoded) > _MAX_BYTES:
        raise DisconnectedBatchArchiveRejected("archive byte budget exceeded")
    return encoded


def _result(
    file_hash: str, receipt: DisconnectedBatchCycleReceipt,
) -> ArchivedDisconnectedBatchCycle:
    outcome = ArchivedDisconnectedBatchCycle(
        file_hash, receipt.request_id, receipt.plan_digest, receipt.cycle_digest,
    )
    pinned = (
        outcome.file_sha256, outcome.request_id, outcome.plan_digest,
        outcome.cycle_digest,
    )

    def stable() -> None:
        if (
            type(outcome) is not ArchivedDisconnectedBatchCycle
            or any(
                current is not original
                for current, original in zip(
                    (outcome.file_sha256, outcome.request_id, outcome.plan_digest,
                     outcome.cycle_digest), pinned, strict=True,
                )
            )
            or any(getattr(ArchivedDisconnectedBatchCycle, name) is not descriptor
                   for name, descriptor in zip(_DENIALS, descriptors, strict=True))
        ):
            raise DisconnectedBatchArchiveRejected("archive witness changed")

    descriptors = tuple(getattr(ArchivedDisconnectedBatchCycle, flag) for flag in _DENIALS)
    stable()
    for flag in _DENIALS:
        if getattr(outcome, flag) is not False:
            raise DisconnectedBatchArchiveRejected("archive gained authority")
        stable()
    return outcome


def archive_disconnected_batch_fixture_cycle(
    receipt: DisconnectedBatchCycleReceipt,
    plan: DisconnectedBatchPlan,
    schedule: DisconnectedBatchSchedule,
    *,
    retained_plan_digest: str,
    path: Path,
) -> ArchivedDisconnectedBatchCycle:
    """Create exactly one fixture-only archive file; never overwrite or delete.

    If a late write/fsync/review fails, the partially created file is left
    quarantined for manual inspection. No automatic retry or cleanup occurs.
    """
    _path(path)
    initial = _receipt_fields(receipt)
    verify_disconnected_batch_fixture_cycle(
        receipt, plan, schedule, retained_digest=retained_plan_digest,
    )
    if not _same_receipt_carriers(receipt, initial):
        raise DisconnectedBatchArchiveRejected("fixture receipt changed before archive")
    raw = _raw(receipt)
    file_hash = hashlib.sha256(raw).hexdigest()
    if not _same_receipt_carriers(receipt, initial):
        raise DisconnectedBatchArchiveRejected("fixture receipt changed before write")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    flags |= getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags, 0o600)
        with os.fdopen(fd, "wb") as handle:
            if handle.write(raw) != len(raw):
                raise DisconnectedBatchArchiveRejected("archive short write")
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise DisconnectedBatchArchiveRejected("archive create-only write denied") from exc
    reviewed = review_disconnected_batch_fixture_cycle_archive(
        plan, schedule, retained_plan_digest=retained_plan_digest,
        path=path, retained_file_sha256=file_hash,
    )
    if (
        not _same_receipt_carriers(receipt, initial)
        or reviewed.cycle_digest != receipt.cycle_digest
    ):
        raise DisconnectedBatchArchiveRejected("fixture changed after archive commit")
    return _result(file_hash, receipt)


def review_disconnected_batch_fixture_cycle_archive(
    plan: DisconnectedBatchPlan,
    schedule: DisconnectedBatchSchedule,
    *,
    retained_plan_digest: str,
    path: Path,
    retained_file_sha256: str,
) -> ArchivedDisconnectedBatchCycle:
    """Restart-safe read-only proof of a deterministic, non-executing fixture."""
    _path(path)
    if type(retained_file_sha256) is not str or _SHA.fullmatch(retained_file_sha256) is None:
        raise DisconnectedBatchArchiveRejected("independently retained file SHA required")
    verify_disconnected_batch_plan(plan, retained_digest=retained_plan_digest)
    verify_disconnected_batch_schedule(
        schedule, plan, retained_digest=retained_plan_digest,
    )
    expected = simulate_disconnected_batch_fixture_cycle(
        plan, schedule, retained_digest=retained_plan_digest,
    )
    expected_raw = _raw(expected)
    expected_carriers = _receipt_fields(expected)
    first, first_epoch = _read_once(path)
    if (
        first != expected_raw
        or hashlib.sha256(first).hexdigest() != retained_file_sha256
    ):
        raise DisconnectedBatchArchiveRejected("archive disagrees with retained fixture")
    second, second_epoch = _read_once(path)
    if second != first or second_epoch != first_epoch:
        raise DisconnectedBatchArchiveRejected("archive changed during review")
    verify_disconnected_batch_plan(plan, retained_digest=retained_plan_digest)
    verify_disconnected_batch_schedule(
        schedule, plan, retained_digest=retained_plan_digest,
    )
    again = simulate_disconnected_batch_fixture_cycle(
        plan, schedule, retained_digest=retained_plan_digest,
    )
    if _raw(again) != expected_raw:
        raise DisconnectedBatchArchiveRejected("fixture changed during archive review")
    again_carriers = _receipt_fields(again)
    witness = _result(retained_file_sha256, expected)
    witness_carriers = (
        witness.file_sha256, witness.request_id,
        witness.plan_digest, witness.cycle_digest,
    )
    denial_descriptors = tuple(
        getattr(ArchivedDisconnectedBatchCycle, name) for name in _DENIALS
    )
    if witness_carriers != (
        retained_file_sha256, expected_carriers[0],
        expected_carriers[1], expected_carriers[4],
    ):
        raise DisconnectedBatchArchiveRejected("archive witness content mismatch")
    final, final_epoch = _read_once(path)
    if final != first or final_epoch != first_epoch:
        raise DisconnectedBatchArchiveRejected("archive changed after witness review")
    # The last file read is an injectable callback boundary. It must not
    # invalidate a previously checked receipt or the non-authorizing result.
    if (
        not _same_receipt_carriers(expected, expected_carriers)
        or not _same_receipt_carriers(again, again_carriers)
        or type(witness) is not ArchivedDisconnectedBatchCycle
        or any(now is not pinned for now, pinned in zip((
            witness.file_sha256, witness.request_id,
            witness.plan_digest, witness.cycle_digest,
        ), witness_carriers, strict=True))
        or any(getattr(ArchivedDisconnectedBatchCycle, name) is not descriptor
               for name, descriptor in zip(_DENIALS, denial_descriptors, strict=True))
    ):
        raise DisconnectedBatchArchiveRejected("archive final witness/source changed")
    return witness

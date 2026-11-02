"""Restart-safe, read-only local custody check for a V3 review packet file.

A matching file hash is not authenticated user approval, provider billing
evidence, Candidate authorization or permission to perform any real compute.
No model, GPU, network, write, protected scorer or external tool is accessed.
"""

from __future__ import annotations

import json
import os
import re
import stat
from pathlib import Path

from .authorization_packet_verify import (
    LocalPacketBindingRejected,
    LocalPacketBindingWitness,
    verify_detached_authorization_packet,
)
from .execution import (
    _finite_json_float,
    _reject_nonstandard_json_constant,
    _unique_snapshot_pairs,
    canonical_json,
    sha256_bytes,
)
from .preflight import _assert_json_tree_epoch, _pin_json_tree

_MAX_PACKET_BYTES = 65_536
_SHA = re.compile(r"[0-9a-f]{64}\Z")


# An always-False replacement property remains an arbitrary callback.
# Bind the original denial descriptors before any packet read or verifier.
_WITNESS_TYPE = LocalPacketBindingWitness
_DENIAL_NAMES = (
    "external_compute_authorized", "candidate_generation_authorized",
    "protected_evaluation_authorized", "main_merge_authorized",
)
_ORIGINAL_DENIALS = tuple(getattr(_WITNESS_TYPE, key) for key in _DENIAL_NAMES)


def _assert_original_denials() -> None:
    if (
        LocalPacketBindingWitness is not _WITNESS_TYPE
        or any(
            getattr(_WITNESS_TYPE, name) is not original
            for name, original in zip(_DENIAL_NAMES, _ORIGINAL_DENIALS, strict=True)
        )
    ):
        raise LocalPacketBindingRejected(
            "review packet witness changed: authority denial descriptor changed during binding"
        )


def _file_epoch(info: os.stat_result) -> tuple[int, int, int, int]:
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)


def _read_exact_local_packet(path: Path) -> tuple[bytes, tuple[int, int, int, int]]:
    """Read the same local regular, non-aliased file twice without creating it."""
    try:
        before = path.lstat()
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or not 1 <= before.st_size <= _MAX_PACKET_BYTES
            or path.is_symlink()
            or any(parent.is_symlink() for parent in path.parents)
        ):
            raise LocalPacketBindingRejected("review packet file path or byte budget denied")
        # lstat()/open() is a race. O_NOFOLLOW denies a final symlink on
        # supported POSIX platforms. O_NONBLOCK also prevents a swapped FIFO
        # from hanging in open() before fstat can reject a nonregular inode.
        # Neither flag authenticates custody or closes ancestor-path races.
        flags = (
            os.O_RDONLY | getattr(os, "O_BINARY", 0)
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        with os.fdopen(os.open(path, flags), "rb") as handle:
            opened = os.fstat(handle.fileno())
            # A race may substitute a FIFO, device, or socket. Never read
            # unverified nonregular bytes merely because lstat saw a file.
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_nlink != 1
                or _file_epoch(opened) != _file_epoch(before)
            ):
                raise LocalPacketBindingRejected(
                    "review packet file changed during read"
                )
            content = handle.read(_MAX_PACKET_BYTES + 1)
        after = path.lstat()
    except OSError as exc:
        raise LocalPacketBindingRejected("review packet file cannot be read") from exc
    identity = _file_epoch(before)
    if (
        not stat.S_ISREG(opened.st_mode)
        or not stat.S_ISREG(after.st_mode)
        or opened.st_nlink != 1
        or after.st_nlink != 1
        or _file_epoch(opened) != identity
        or _file_epoch(after) != identity
        or len(content) != before.st_size
        or path.is_symlink()
        or any(parent.is_symlink() for parent in path.parents)
    ):
        raise LocalPacketBindingRejected("review packet file changed during read")
    return content, identity


def verify_local_authorization_packet_file(
    snapshot: dict,
    packet_path: Path,
    *,
    retained_packet_file_sha256: str,
) -> LocalPacketBindingWitness:
    """Reopen saved review bytes and bind them to the *unapproved* snapshot.

    The retained file digest must have been preserved independently. This is
    an integrity diagnostic, not an approval or an atomic filesystem lock.
    """
    if (
        type(snapshot) is not dict
        or type(packet_path) is not type(Path("."))
        or not packet_path.is_absolute()
        or ".." in packet_path.parts
        or len(str(packet_path)) > 4096
        or type(retained_packet_file_sha256) is not str
        or _SHA.fullmatch(retained_packet_file_sha256) is None
    ):
        raise LocalPacketBindingRejected("exact local packet review inputs required")
    _assert_original_denials()
    try:
        snapshot_epoch = _pin_json_tree(snapshot)

        def stable_snapshot() -> None:
            _assert_json_tree_epoch(snapshot, snapshot_epoch)

        stable_snapshot()
        raw, file_epoch = _read_exact_local_packet(packet_path)
        _assert_original_denials()
        stable_snapshot()
        if sha256_bytes(raw) != retained_packet_file_sha256:
            raise LocalPacketBindingRejected("retained packet file bytes mismatch")
        try:
            packet = json.loads(
                raw,
                object_pairs_hook=_unique_snapshot_pairs,
                parse_constant=_reject_nonstandard_json_constant,
                parse_float=_finite_json_float,
            )
        except (ValueError, RecursionError, OverflowError, UnicodeError) as exc:
            raise LocalPacketBindingRejected("review packet JSON is invalid") from exc
        _assert_original_denials()
        stable_snapshot()
        if type(packet) is not dict or canonical_json(packet) != raw:
            raise LocalPacketBindingRejected("review packet is not canonical JSON")
        stable_snapshot()
        # Keep the parsed packet itself pinned across the delegated verifier.
        # A detached verifier's successful return is not an immutable custody
        # boundary when its witness or input can be reflectively changed.
        packet_epoch = _pin_json_tree(packet)
        expected_snapshot_sha = packet["execution_snapshot_sha256"]
        expected_internal_sha = packet["packet_sha256"]
        _assert_original_denials()
        witness = verify_detached_authorization_packet(
            snapshot, packet,
            retained_packet_file_sha256=retained_packet_file_sha256,
        )
        _assert_original_denials()

        def stable_review() -> None:
            _assert_original_denials()
            stable_snapshot()
            _assert_json_tree_epoch(packet, packet_epoch)
            if (
                type(witness) is not _WITNESS_TYPE
                or type(witness.snapshot_sha256) is not str
                or witness.snapshot_sha256 != expected_snapshot_sha
                or type(witness.packet_file_sha256) is not str
                or witness.packet_file_sha256 != retained_packet_file_sha256
                or type(witness.internal_packet_sha256) is not str
                or witness.internal_packet_sha256 != expected_internal_sha
            ):
                raise LocalPacketBindingRejected("review packet witness changed after binding")

        def denied() -> None:
            # A false getter may mutate another descriptor or witness field.
            # Check all original boundaries after each individual callback.
            stable_review()
            for flag in _DENIAL_NAMES:
                if getattr(witness, flag) is not False:
                    raise LocalPacketBindingRejected(
                        "review packet witness gained authority"
                    )
                stable_review()

        stable_review()
        denied()
        # The detached review and denial callbacks may mutate the file.
        # Reopen after the callbacks, then repeat the identity/denial fences.
        final_raw, final_epoch = _read_exact_local_packet(packet_path)
        _assert_original_denials()
        stable_review()
        if final_epoch != file_epoch or final_raw != raw:
            raise LocalPacketBindingRejected("review packet file changed during binding")
        denied()
        stable_review()
        # No operation or approval is authorized by the returned witness.
        return witness
    except (TypeError, KeyError, UnicodeError, RecursionError) as exc:
        raise LocalPacketBindingRejected("review packet file cannot be verified") from exc

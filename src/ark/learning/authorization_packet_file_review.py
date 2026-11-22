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

_REPARSE_POINT_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_ORIGINAL_REPARSE_POINT_ATTRIBUTE = _REPARSE_POINT_ATTRIBUTE
_ORIGINAL_STAT = stat
_ORIGINAL_S_ISREG = stat.S_ISREG
_ORIGINAL_S_ISLNK = stat.S_ISLNK


def _require_original_path_policy() -> None:
    """Pin the exact local classifiers used by the detached packet reader."""
    if (
        stat is not _ORIGINAL_STAT
        or stat.S_ISREG is not _ORIGINAL_S_ISREG
        or stat.S_ISLNK is not _ORIGINAL_S_ISLNK
        or type(_REPARSE_POINT_ATTRIBUTE) is not int
        or _REPARSE_POINT_ATTRIBUTE != _ORIGINAL_REPARSE_POINT_ATTRIBUTE
    ):
        raise LocalPacketBindingRejected("review packet reparse-point guard changed")


def _is_regular_file(info: object) -> bool:
    _require_original_path_policy()
    mode = info.st_mode
    _require_original_path_policy()
    if type(mode) is not int:
        raise LocalPacketBindingRejected("review packet file mode is malformed")
    return _ORIGINAL_S_ISREG(mode)


def _is_reparse_point(info: object) -> bool:
    _require_original_path_policy()
    attributes = getattr(info, "st_file_attributes", 0)
    _require_original_path_policy()
    if type(attributes) is not int:
        raise LocalPacketBindingRejected("review packet reparse metadata is malformed")
    mode = info.st_mode
    _require_original_path_policy()
    if type(mode) is not int:
        raise LocalPacketBindingRejected("review packet file mode is malformed")
    return _ORIGINAL_S_ISLNK(mode) or bool(
        attributes & _ORIGINAL_REPARSE_POINT_ATTRIBUTE
    )


def _has_reparse_ancestor(path: Path) -> bool:
    """Reject symlink/junction ancestors before a packet path is opened."""
    _require_original_path_policy()
    for parent in path.parents:
        _require_original_path_policy()
        try:
            info = parent.lstat()
        except FileNotFoundError:
            _require_original_path_policy()
            continue
        except OSError as exc:
            raise LocalPacketBindingRejected(
                "review packet ancestry cannot be verified"
            ) from exc
        _require_original_path_policy()
        if _is_reparse_point(info):
            return True
    _require_original_path_policy()
    return False

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


def _file_epoch(info: os.stat_result) -> tuple[int, int, int, int, int]:
    # mtime alone is caller-restorable with os.utime(). Include ctime, which
    # records inode metadata changes on POSIX, to flag same-size, same-byte
    # rewrites that restore mtime between our two passive reads. Windows
    # path.stat and fstat may disagree on ctime even for an unchanged file;
    # preserve the original Windows epoch behavior instead of false rejection.
    # This remains unauthenticated local custody, never approval or provenance.
    _require_original_path_policy()
    device = info.st_dev
    _require_original_path_policy()
    inode = info.st_ino
    _require_original_path_policy()
    size = info.st_size
    _require_original_path_policy()
    modified = info.st_mtime_ns
    _require_original_path_policy()
    changed = info.st_ctime_ns if os.name == "posix" else 0
    _require_original_path_policy()
    values = (device, inode, size, modified, changed)
    if any(type(value) is not int for value in values):
        raise LocalPacketBindingRejected("review packet file metadata is malformed")
    return values


def _read_exact_local_packet(path: Path) -> tuple[bytes, tuple[int, int, int, int, int]]:
    """Read the same local regular, non-aliased file twice without creating it."""
    _require_original_path_policy()
    try:
        before = path.lstat()
        _require_original_path_policy()
        before_regular = _is_regular_file(before)
        before_reparse = _is_reparse_point(before)
        before_links = before.st_nlink
        _require_original_path_policy()
        before_size = before.st_size
        _require_original_path_policy()
        before_ancestor_reparse = _has_reparse_ancestor(path)
        _require_original_path_policy()
        before_symlink = path.is_symlink()
        _require_original_path_policy()
        before_parent_symlink = any(parent.is_symlink() for parent in path.parents)
        _require_original_path_policy()
        if (
            not before_regular
            or before_reparse
            or before_ancestor_reparse
            or type(before_links) is not int
            or before_links != 1
            or type(before_size) is not int
            or not 1 <= before_size <= _MAX_PACKET_BYTES
            or before_symlink
            or before_parent_symlink
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
        descriptor = os.open(path, flags)
        try:
            _require_original_path_policy()
            with os.fdopen(descriptor, "rb") as handle:
                descriptor = -1
                _require_original_path_policy()
                opened = os.fstat(handle.fileno())
                _require_original_path_policy()
                opened_regular = _is_regular_file(opened)
                opened_reparse = _is_reparse_point(opened)
                opened_links = opened.st_nlink
                _require_original_path_policy()
                before_epoch = _file_epoch(before)
                opened_epoch = _file_epoch(opened)
                if (
                    not opened_regular
                    or opened_reparse
                    or type(opened_links) is not int
                    or opened_links != 1
                    or opened_epoch != before_epoch
                ):
                    raise LocalPacketBindingRejected(
                        "review packet file changed during read"
                    )
                _require_original_path_policy()
                content = handle.read(_MAX_PACKET_BYTES + 1)
                _require_original_path_policy()
                after_handle = os.fstat(handle.fileno())
                _require_original_path_policy()
        finally:
            if descriptor >= 0:
                os.close(descriptor)
        after = path.lstat()
        _require_original_path_policy()
    except OSError as exc:
        raise LocalPacketBindingRejected("review packet file cannot be read") from exc

    identity = _file_epoch(before)
    opened_regular = _is_regular_file(opened)
    opened_reparse = _is_reparse_point(opened)
    opened_links = opened.st_nlink
    _require_original_path_policy()
    after_regular = _is_regular_file(after)
    after_reparse = _is_reparse_point(after)
    after_links = after.st_nlink
    _require_original_path_policy()
    after_handle_regular = _is_regular_file(after_handle)
    after_handle_reparse = _is_reparse_point(after_handle)
    after_handle_links = after_handle.st_nlink
    _require_original_path_policy()
    after_epoch = _file_epoch(after)
    after_handle_epoch = _file_epoch(after_handle)
    path_symlink = path.is_symlink()
    _require_original_path_policy()
    parent_symlink = any(parent.is_symlink() for parent in path.parents)
    _require_original_path_policy()
    ancestor_reparse = _has_reparse_ancestor(path)
    _require_original_path_policy()
    if (
        not opened_regular
        or opened_reparse
        or type(opened_links) is not int
        or opened_links != 1
        or not after_regular
        or after_reparse
        or type(after_links) is not int
        or after_links != 1
        or not after_handle_regular
        or after_handle_reparse
        or type(after_handle_links) is not int
        or after_handle_links != 1
        or after_epoch != identity
        or after_handle_epoch != identity
        or len(content) != before_size
        or path_symlink
        or parent_symlink
        or ancestor_reparse
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

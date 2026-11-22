"""Deterministic authorization packet generation for the pre-paid-compute STOP."""

from __future__ import annotations

import argparse
import stat
from copy import deepcopy
from pathlib import Path

from .execution import (
    canonical_json,
    execution_core_sha256,
    load_snapshot,
    sha256_bytes,
    validate_experiment_001,
)
from .preflight import _assert_json_tree_epoch, _pin_json_tree

_REPARSE_POINT_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_ORIGINAL_REPARSE_POINT_ATTRIBUTE = _REPARSE_POINT_ATTRIBUTE
_ORIGINAL_STAT = stat
_ORIGINAL_S_ISREG = stat.S_ISREG
_ORIGINAL_S_ISLNK = stat.S_ISLNK


def _require_original_reparse_point_policy() -> None:
    if (
        stat is not _ORIGINAL_STAT
        or _ORIGINAL_STAT.S_ISREG is not _ORIGINAL_S_ISREG
        or _ORIGINAL_STAT.S_ISLNK is not _ORIGINAL_S_ISLNK
        or type(_REPARSE_POINT_ATTRIBUTE) is not int
        or _REPARSE_POINT_ATTRIBUTE != _ORIGINAL_REPARSE_POINT_ATTRIBUTE
    ):
        raise ValueError("authorization packet reparse-point policy changed")


def _is_regular_file(info: object) -> bool:
    _require_original_reparse_point_policy()
    mode = info.st_mode
    _require_original_reparse_point_policy()
    if type(mode) is not int:
        raise ValueError("authorization packet file mode is malformed")
    return _ORIGINAL_S_ISREG(mode)


def _is_reparse_point(info: object) -> bool:
    _require_original_reparse_point_policy()
    attributes = getattr(info, "st_file_attributes", 0)
    _require_original_reparse_point_policy()
    if type(attributes) is not int:
        raise ValueError("authorization packet reparse metadata is malformed")
    mode = info.st_mode
    _require_original_reparse_point_policy()
    if type(mode) is not int:
        raise ValueError("authorization packet file mode is malformed")
    return _ORIGINAL_S_ISLNK(mode) or bool(
        attributes & _REPARSE_POINT_ATTRIBUTE
    )


def _has_reparse_ancestor(path: Path) -> bool:
    """Reject symlink/junction ancestors before packet output is opened."""
    for parent in path.parents:
        try:
            info = parent.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise ValueError(
                "authorization packet output ancestry cannot be verified"
            ) from exc
        if _is_reparse_point(info):
            return True
    return False


def build_preflight_authorization_packet(snapshot: dict) -> dict:
    """Build a user-review packet without authorizing or starting external compute."""
    # The packet is the artifact a human would inspect before separately
    # authorizing expensive operations. Never mix snapshot revisions across
    # validator, core-hash, nested-copy and packet-hash callbacks.
    if type(snapshot) is not dict:
        raise ValueError("exact execution snapshot mapping required")
    snapshot_epoch = _pin_json_tree(snapshot)

    def stable() -> None:
        _assert_json_tree_epoch(snapshot, snapshot_epoch)

    stable()
    snapshot_sha = validate_experiment_001(snapshot, authorization_scope="none")
    stable()
    auth = snapshot["authorization"]
    if any(
        auth[key]
        for key in (
            "external_compute_authorized",
            "preflight_authorized",
            "real_training_authorized",
        )
    ):
        raise ValueError("authorization packet must be generated from an unapproved snapshot")
    core_sha = execution_core_sha256(snapshot)
    stable()

    packet = {
        "schema_version": 1,
        "experiment_id": snapshot["experiment_id"],
        "request_scope": "EXTERNAL_COMPUTE_PLUS_NON_CANDIDATE_PREFLIGHT_ONLY",
        "execution_snapshot_sha256": snapshot_sha,
        "execution_core_sha256": core_sha,
        "code_git_sha": snapshot["code"]["git_sha"],
        "code_manifest_sha256": snapshot["code"]["manifest_sha256"],
        "base": {
            "model_id": snapshot["base"]["model_id"],
            "revision": snapshot["base"]["revision"],
            "manifest_sha256": snapshot["base"]["file_sha256_manifest"],
        },
        "tokenizer": {
            "revision": snapshot["tokenizer"]["revision"],
            "manifest_sha256": snapshot["tokenizer"]["file_sha256_manifest"],
            "chat_template_probe_sha256": snapshot["tokenizer"]["chat_template_probe_sha256"],
        },
        "dataset": {
            "canonical_sha256": snapshot["dataset"]["canonical_sha256"],
            "provenance_manifest_sha256": snapshot["dataset"]["provenance_manifest_sha256"],
            "contamination_report_sha256": snapshot["dataset"]["contamination_report_sha256"],
            "train_count": 120,
            "validation_count": 30,
        },
        "method": deepcopy(snapshot["method"]),
        "environment": deepcopy(snapshot["environment"]),
        "proposed_hardware": {
            "device": snapshot["hardware"]["device"],
            "vram_gib": snapshot["hardware"]["vram_gib"],
            "driver": snapshot["hardware"]["driver"],
        },
        "budget": {
            "max_cost_jpy": snapshot["budget"]["max_cost_jpy"],
            "wall_clock_timeout_minutes": snapshot["budget"]["wall_clock_timeout_minutes"],
        },
        "export": deepcopy(snapshot["export"]),
        "evaluation": deepcopy(snapshot["evaluation"]),
        "privacy": deepcopy(snapshot["privacy"]),
        "preflight": {
            "candidate_created": False,
            "validation_opened": False,
            "historical_v2_opened": False,
            "expected_outputs": [
                "base_load_success",
                "tokenizer_chat_template_probe_digest",
                "one_forward_backward_optimizer_step",
                "peak_vram_measurement",
                "wall_time",
                "dependency_hardware_manifest",
                "runtime_error_or_success",
            ],
        },
        "hard_stops_after_preflight": {
            "full_candidate_training_requires_new_explicit_authorization": True,
            "historical_v2_opening_requires_later_explicit_authorization": True,
            "promotion_requires_later_explicit_authorization": True,
            "main_merge_authorized": False,
        },
    }
    stable()
    # The review packet is a separate mutable JSON tree. A serializer or
    # digest callback can rewrite the packet AFTER returning its earlier
    # bytes without changing the pinned execution snapshot. Bind both epochs
    # before adding the derived digest; this does not grant approval.
    packet_epoch = _pin_json_tree(packet)
    stable()
    canonical_packet = canonical_json(packet)
    stable()
    _assert_json_tree_epoch(packet, packet_epoch)
    packet_digest = sha256_bytes(canonical_packet)
    stable()
    _assert_json_tree_epoch(packet, packet_epoch)
    packet["packet_sha256"] = packet_digest
    stable()
    if packet["packet_sha256"] != packet_digest:
        raise ValueError("authorization review packet changed after hashing")
    return packet



def _write_new_authorization_packet(path: Path, packet: dict) -> None:
    """Save review-only JSON, rejecting known path aliases before exclusive create.

    This is not an atomic directory-fd traversal or approval to spend money.
    The payload is generated without opening any execution or evaluation gate.
    """
    _require_original_reparse_point_policy()
    if (
        type(path) is not type(Path("."))
        or not path.is_absolute()
        or ".." in path.parts
        or len(str(path)) > 4096
        or path.name in ("", ".", "..")
    ):
        raise ValueError("authorization packet output must be a new non-aliased file")
    # Inspect ancestors with no-follow metadata before any operation that
    # follows a path. Then lstat the final leaf: Path.exists() can report
    # False for a dangling Windows reparse point even though an entry exists.
    if _has_reparse_ancestor(path):
        raise ValueError("authorization packet output must be a new non-aliased file")
    try:
        leaf_info = path.lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise ValueError(
            "authorization packet output must be a new non-aliased file"
        ) from exc
    else:
        # Validate the pinned reparse metadata even though every existing
        # leaf is denied. This catches dangling junction/reparse entries
        # before exclusive create can traverse or interact with them.
        _is_reparse_point(leaf_info)
        raise ValueError("authorization packet output must be a new non-aliased file")
    parent_is_dir = path.parent.is_dir()
    _require_original_reparse_point_policy()
    parent_symlink = any(parent.is_symlink() for parent in path.parents)
    _require_original_reparse_point_policy()
    if not parent_is_dir or parent_symlink:
        raise ValueError("authorization packet output must be a new non-aliased file")
    # A serializer callback must not make the reviewed JSON tree differ
    # from the exact bytes that will be exclusively created on disk.
    # This is local custody only: not approval, atomic directory traversal,
    # or a guarantee against an adversarial filesystem writer.
    if type(packet) is not dict:
        raise ValueError("exact authorization packet mapping required")
    epoch = _pin_json_tree(packet)
    data = canonical_json(packet)
    _assert_json_tree_epoch(packet, epoch)
    _require_original_reparse_point_policy()
    with path.open("xb") as handle:
        _require_original_reparse_point_policy()
        written = handle.write(data)
        _require_original_reparse_point_policy()
        if type(written) is not int or written != len(data):
            raise ValueError("authorization review packet write was incomplete")
    _require_original_reparse_point_policy()
    _assert_json_tree_epoch(packet, epoch)
    # COMMIT-equivalent boundary: a successful write call is not proof that
    # the exact reviewed bytes reached the new file. Re-open the local file
    # after the handle closes, and refuse an altered byte stream or alias.
    # Never interpret this check as approval to pay for compute or training.
    try:
        before = path.lstat()
        regular_before = _is_regular_file(before)
        reparse_before = _is_reparse_point(before)
        ancestor_reparse = _has_reparse_ancestor(path)
        leaf_symlink = path.is_symlink()
        _require_original_reparse_point_policy()
        parent_symlink = any(parent.is_symlink() for parent in path.parents)
        _require_original_reparse_point_policy()
        if (
            not regular_before
            or reparse_before
            or ancestor_reparse
            or before.st_nlink != 1
            or before.st_size != len(data)
            or leaf_symlink
            or parent_symlink
        ):
            raise ValueError("authorization packet output alias or size changed")
        saved_bytes = path.read_bytes()
        _require_original_reparse_point_policy()
        after = path.lstat()
        regular_after = _is_regular_file(after)
        reparse_after = _is_reparse_point(after)
        ancestor_reparse_after = _has_reparse_ancestor(path)
        leaf_symlink_after = path.is_symlink()
        _require_original_reparse_point_policy()
        parent_symlink_after = any(parent.is_symlink() for parent in path.parents)
        _require_original_reparse_point_policy()
    except OSError as exc:
        raise ValueError("authorization packet output cannot be rechecked") from exc
    _assert_json_tree_epoch(packet, epoch)
    if (
        saved_bytes != data
        or not regular_after
        or reparse_after
        or ancestor_reparse_after
        or after.st_nlink != 1
        or (after.st_dev, after.st_ino, after.st_size)
        != (before.st_dev, before.st_ino, before.st_size)
        or leaf_symlink_after
        or parent_symlink_after
    ):
        raise ValueError("authorization packet output bytes or identity changed")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build ARK V3 preflight authorization packet")
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    output = Path(args.output)
    if output.exists() or output.is_symlink() or not output.parent.is_dir():
        raise ValueError("authorization packet output must be a new file")
    packet = build_preflight_authorization_packet(load_snapshot(args.snapshot))
    _write_new_authorization_packet(output, packet)
    print(f"packet_sha256={packet['packet_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Passive V3 execution-snapshot shape review without model or compute access.

An unapproved snapshot can have zero literal placeholders yet contain fake,
mis-typed or malformed identity strings. This check reports only field names;
even a clean syntax review NEVER proves artifact bytes, human decisions,
billing limits, execution readiness, Candidate or protected V2 permission.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass

from .offline_readiness_inventory import (
    _PLACEHOLDERS,
    _SECTIONS,
    OfflineReadinessInventory,
    OfflineReadinessRejected,
    inventory_unapproved_v3_readiness,
)
from .preflight import _assert_json_tree_epoch, _pin_json_tree

_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_REVISION_PATHS = frozenset((
    "code.git_sha", "base.revision", "export.llama_cpp_revision",
))
_SHA_PATHS = frozenset((
    "code.manifest_sha256", "base.file_sha256_manifest",
    "tokenizer.file_sha256_manifest", "tokenizer.chat_template_probe_sha256",
    "dataset.canonical_sha256", "dataset.provenance_manifest_sha256",
    "dataset.contamination_report_sha256", "hardware.preflight_report_sha256",
    "export.converter_identity", "export.quantizer_identity",
))
_NUMBER_PATHS = frozenset((
    "hardware.vram_gib", "budget.max_cost_jpy",
    "budget.wall_clock_timeout_minutes",
))
_DENIED = (
    "external_compute_authorized", "preflight_authorized",
    "real_training_authorized", "candidate_generation_authorized",
    "v2_opening_authorized", "promotion_authorized",
)


class OfflineShapeRejected(ValueError):
    """Unapproved snapshot shape review could not safely complete."""


@dataclass(frozen=True, slots=True)
class UnapprovedSnapshotShapeReview:
    snapshot_sha256: str
    unresolved_paths: tuple[str, ...]
    invalid_shape_paths: tuple[str, ...]
    checked_path_count: int

    @property
    def external_compute_authorized(self) -> bool:
        return False

    @property
    def preflight_authorized(self) -> bool:
        return False

    @property
    def real_training_authorized(self) -> bool:
        return False

    @property
    def candidate_generation_authorized(self) -> bool:
        return False

    @property
    def v2_opening_authorized(self) -> bool:
        return False

    @property
    def promotion_authorized(self) -> bool:
        return False


def _plausible_shape(path: str, value: object) -> bool:
    if path in _SHA_PATHS:
        return type(value) is str and _HEX64.fullmatch(value) is not None
    if path in _REVISION_PATHS:
        return type(value) is str and _HEX40.fullmatch(value) is not None
    if path == "hardware.vram_gib":
        return (
            type(value) in (int, float) and math.isfinite(value)
            and 0 < value <= 1_000_000
        )
    if path == "budget.max_cost_jpy":
        return (
            type(value) in (int, float) and math.isfinite(value)
            and 0 <= value <= 1_000_000_000
        )
    if path == "budget.wall_clock_timeout_minutes":
        return type(value) is int and 1 <= value <= 525_600
    return type(value) is str and 0 < len(value.strip()) <= 256


def review_unapproved_v3_snapshot_shapes(
    snapshot: dict,
) -> UnapprovedSnapshotShapeReview:
    """Distinguish literal unresolved identities from syntactically invalid ones.

    All authorization flags must be exact False. Values that *look* valid are
    still unverified, and the result is never an approval or executor input.
    """
    if type(snapshot) is not dict:
        raise OfflineShapeRejected("exact unapproved snapshot required")
    try:
        epoch = _pin_json_tree(snapshot)

        def stable() -> None:
            _assert_json_tree_epoch(snapshot, epoch)

        stable()
        inventory = inventory_unapproved_v3_readiness(snapshot)
        stable()
        if (
            type(inventory) is not OfflineReadinessInventory
            or type(inventory.snapshot_sha256) is not str
            or type(inventory.unresolved_paths) is not tuple
            or type(inventory.unresolved_count) is not int
            or inventory.unresolved_count != len(inventory.unresolved_paths)
        ):
            raise OfflineShapeRejected("readiness source changed")
        # Never let an exact-type but replaced inventory callback supply its
        # own path classification.  The source is still unapproved, yet the
        # passive report must at least describe its *actual* placeholder bytes.
        expected_unresolved = {
            f"{section}.{name}"
            for section, names in _SECTIONS.items()
            for name in names
            if (
                type(snapshot[section][name]) is str
                and snapshot[section][name] in _PLACEHOLDERS
            )
        }
        tokenizer_revision = snapshot["tokenizer"]["revision"]
        base_revision = snapshot["base"]["revision"]
        if (
            (type(tokenizer_revision) is str
             and tokenizer_revision in _PLACEHOLDERS)
            or (tokenizer_revision == "SAME_AS_BASE"
                and type(base_revision) is str
                and base_revision in _PLACEHOLDERS)
        ):
            expected_unresolved.add("tokenizer.revision")
        if inventory.unresolved_paths != tuple(sorted(expected_unresolved)):
            raise OfflineShapeRejected("inventory path classification mismatch")
        stable()
        # The inventory's non-authority properties are also checked here,
        # independently of how its replaceable callable constructed it.
        inventory_denials = (
            "external_compute_authorized", "candidate_generation_authorized",
            "protected_evaluation_authorized", "promotion_authorized",
        )
        inventory_epoch = (
            inventory.snapshot_sha256, inventory.unresolved_paths,
            inventory.unresolved_count,
        )
        inventory_descriptors = tuple(
            getattr(OfflineReadinessInventory, key) for key in inventory_denials
        )

        def assert_inventory_epoch() -> None:
            if (
                type(inventory) is not OfflineReadinessInventory
                or any(current is not original for current, original in zip(
                    (inventory.snapshot_sha256, inventory.unresolved_paths,
                     inventory.unresolved_count), inventory_epoch, strict=True,
                ))
                or any(getattr(OfflineReadinessInventory, key) is not descriptor
                       for key, descriptor in zip(
                           inventory_denials, inventory_descriptors, strict=True,
                       ))
            ):
                raise OfflineShapeRejected("inventory source changed after review")
            for key in inventory_denials:
                if getattr(inventory, key) is not False:
                    raise OfflineShapeRejected("inventory gained authority")
            if (
                any(getattr(OfflineReadinessInventory, key) is not descriptor
                    for key, descriptor in zip(
                        inventory_denials, inventory_descriptors, strict=True,
                    ))
                or any(current is not original for current, original in zip(
                    (inventory.snapshot_sha256, inventory.unresolved_paths,
                     inventory.unresolved_count), inventory_epoch, strict=True,
                ))
            ):
                raise OfflineShapeRejected("inventory changed during denial")
            stable()

        assert_inventory_epoch()
        unresolved = set(inventory.unresolved_paths)
        invalid: set[str] = set()
        count = 0
        for section, names in _SECTIONS.items():
            values = snapshot[section]
            if type(values) is not dict:
                raise OfflineShapeRejected("noncanonical identity section")
            for name in names:
                stable()
                path = f"{section}.{name}"
                value = values[name]
                count += 1
                if path not in unresolved and not _plausible_shape(path, value):
                    invalid.add(path)
        stable()
        alias = snapshot["tokenizer"]["revision"]
        base = snapshot["base"]["revision"]
        count += 1
        if alias == "SAME_AS_BASE":
            if type(base) is str and base in _PLACEHOLDERS:
                unresolved.add("tokenizer.revision")
            elif not _plausible_shape("base.revision", base):
                invalid.add("tokenizer.revision")
        elif type(alias) is str and alias in _PLACEHOLDERS:
            unresolved.add("tokenizer.revision")
        elif type(alias) is not str or _HEX40.fullmatch(alias) is None:
            invalid.add("tokenizer.revision")
        stable()
        canonical = json.dumps(
            snapshot, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
        sha256 = hashlib.sha256(canonical).hexdigest()
        if sha256 != inventory.snapshot_sha256:
            raise OfflineShapeRejected("snapshot changed after inventory")
        result = UnapprovedSnapshotShapeReview(
            sha256, tuple(sorted(unresolved)), tuple(sorted(invalid)), count,
        )
        original = (
            result.snapshot_sha256, result.unresolved_paths,
            result.invalid_shape_paths, result.checked_path_count,
        )
        descriptors = tuple(
            getattr(UnapprovedSnapshotShapeReview, name) for name in _DENIED
        )

        def stable_result() -> None:
            if (
                type(result) is not UnapprovedSnapshotShapeReview
                or any(a is not b for a, b in zip(
                    (result.snapshot_sha256, result.unresolved_paths,
                     result.invalid_shape_paths, result.checked_path_count),
                    original, strict=True,
                ))
                or any(getattr(UnapprovedSnapshotShapeReview, name) is not descriptor
                       for name, descriptor in zip(_DENIED, descriptors, strict=True))
            ):
                raise OfflineShapeRejected("shape review result changed")
            stable()

        stable_result()
        for name in _DENIED:
            if getattr(result, name) is not False:
                raise OfflineShapeRejected("shape review gained authority")
            stable_result()
            assert_inventory_epoch()
        assert_inventory_epoch()
        stable_result()
        return result
    except (
        OfflineReadinessRejected, KeyError, TypeError, ValueError,
        OverflowError, RecursionError, UnicodeError,
    ) as exc:
        if type(exc) is OfflineShapeRejected:
            raise
        raise OfflineShapeRejected("unapproved shape review unavailable") from exc

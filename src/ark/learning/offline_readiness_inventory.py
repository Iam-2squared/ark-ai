"""Offline V3 execution-snapshot placeholder inventory; never an approval gate.

This reports only literal unresolved placeholder positions from an unapproved
snapshot. Resolved-looking values are NOT independently verified identities,
reviewer consent, provider billing caps, or permission to run training.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from types import MappingProxyType

from .preflight import _assert_json_tree_epoch, _pin_json_tree

# MappingProxyType plus immutable tuple values prevent in-place field omission.
# These are passive diagnostic field names, never execution authorization.
_SECTIONS = MappingProxyType({
    "code": ("git_sha", "manifest_sha256"),
    "base": ("revision", "file_sha256_manifest"),
    "tokenizer": ("file_sha256_manifest", "chat_template_probe_sha256"),
    "dataset": (
        "canonical_sha256", "provenance_manifest_sha256",
        "contamination_report_sha256",
    ),
    "environment": (
        "os_or_image_digest", "python", "torch", "transformers",
        "peft", "accelerate", "cuda_runtime",
    ),
    "hardware": ("device", "vram_gib", "driver", "preflight_report_sha256"),
    "budget": ("max_cost_jpy", "wall_clock_timeout_minutes"),
    "export": (
        "llama_cpp_revision", "converter_identity", "quantizer_identity",
    ),
})
_PLACEHOLDERS = frozenset(("UNRESOLVED", "USER_APPROVAL_REQUIRED"))
_DENIED = (
    "external_compute_authorized", "preflight_authorized",
    "real_training_authorized", "v2_opening_authorized",
    "promotion_authorized",
)
_AUTHORITY = (
    "external_compute_authorized", "candidate_generation_authorized",
    "protected_evaluation_authorized", "promotion_authorized",
)
_ORIGINAL_SECTIONS = _SECTIONS
_ORIGINAL_PLACEHOLDERS = _PLACEHOLDERS
_ORIGINAL_DENIED = _DENIED
_ORIGINAL_AUTHORITY = _AUTHORITY
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON = json
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_PIN_JSON_TREE = _pin_json_tree
_ORIGINAL_ASSERT_JSON_TREE_EPOCH = _assert_json_tree_epoch


class OfflineReadinessRejected(ValueError):
    """A proposed, unapproved V3 snapshot is not safe for passive inventory."""


@dataclass(frozen=True, slots=True)
class OfflineReadinessInventory:
    snapshot_sha256: str
    unresolved_paths: tuple[str, ...]
    unresolved_count: int

    @property
    def external_compute_authorized(self) -> bool:
        return False

    @property
    def candidate_generation_authorized(self) -> bool:
        return False

    @property
    def protected_evaluation_authorized(self) -> bool:
        return False

    @property
    def promotion_authorized(self) -> bool:
        return False


_ORIGINAL_INVENTORY_TYPE = OfflineReadinessInventory
_INVENTORY_FIELDS = ("snapshot_sha256", "unresolved_paths", "unresolved_count")
_INVENTORY_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_INVENTORY_PINNED_NAMES = _INVENTORY_FIELDS + _AUTHORITY + _INVENTORY_HOOKS
_ORIGINAL_INVENTORY_CARRIERS = tuple(
    vars(_ORIGINAL_INVENTORY_TYPE).get(name) for name in _INVENTORY_PINNED_NAMES
)
_ORIGINAL_INVENTORY_DENIALS = tuple(
    vars(_ORIGINAL_INVENTORY_TYPE)[name] for name in _AUTHORITY
)


def _assert_original_inventory_protocol() -> None:
    """Pin passive inventory fields, denial carriers and digest dependencies."""
    if (
        _SECTIONS is not _ORIGINAL_SECTIONS
        or type(_SECTIONS) is not type(_ORIGINAL_SECTIONS)
        or _PLACEHOLDERS is not _ORIGINAL_PLACEHOLDERS
        or _DENIED is not _ORIGINAL_DENIED
        or _AUTHORITY is not _ORIGINAL_AUTHORITY
        or hashlib is not _ORIGINAL_HASHLIB
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json is not _ORIGINAL_JSON
        or json.dumps is not _ORIGINAL_DUMPS
        or _pin_json_tree is not _ORIGINAL_PIN_JSON_TREE
        or _assert_json_tree_epoch is not _ORIGINAL_ASSERT_JSON_TREE_EPOCH
    ):
        raise OfflineReadinessRejected("readiness inventory protocol changed")
    if OfflineReadinessInventory is not _ORIGINAL_INVENTORY_TYPE:
        raise OfflineReadinessRejected("readiness inventory result descriptor changed")
    field_and_hook_names = _INVENTORY_FIELDS + _INVENTORY_HOOKS
    field_and_hook_originals = (
        _ORIGINAL_INVENTORY_CARRIERS[:len(_INVENTORY_FIELDS)]
        + _ORIGINAL_INVENTORY_CARRIERS[-len(_INVENTORY_HOOKS):]
    )
    if any(
        vars(_ORIGINAL_INVENTORY_TYPE).get(name) is not original
        for name, original in zip(
            field_and_hook_names, field_and_hook_originals, strict=True,
        )
    ):
        raise OfflineReadinessRejected("readiness inventory result descriptor changed")
    if any(
        vars(_ORIGINAL_INVENTORY_TYPE).get(name) is not original
        for name, original in zip(
            _AUTHORITY, _ORIGINAL_INVENTORY_DENIALS, strict=True,
        )
    ):
        raise OfflineReadinessRejected("readiness authority descriptor changed")


def inventory_unapproved_v3_readiness(snapshot: dict) -> OfflineReadinessInventory:
    """List literal unfinished identities/budget fields without opening gates.

    This never interprets the absence of placeholders as execution readiness.
    The five current authorization flags must ALL be exact False. The output
    intentionally exposes field names only, not private path/content values.
    """
    _assert_original_inventory_protocol()
    if type(snapshot) is not dict:
        raise OfflineReadinessRejected("exact snapshot mapping required")
    try:
        epoch = _pin_json_tree(snapshot)

        def stable() -> None:
            _assert_original_inventory_protocol()
            _assert_json_tree_epoch(snapshot, epoch)

        stable()
        authorization = snapshot["authorization"]
        if (
            type(authorization) is not dict
            or set(authorization) != set(_DENIED)
            or any(
                type(authorization[key]) is not bool
                or authorization[key] is not False
                for key in _DENIED
            )
        ):
            raise OfflineReadinessRejected("unapproved authorization flags required")
        stable()
        experiment_id = snapshot.get("experiment_id")
        if (
            type(snapshot.get("schema_version")) is not int
            or snapshot["schema_version"] != 1
            or type(experiment_id) is not str
            or experiment_id != "v3-format-compliance-001"
        ):
            raise OfflineReadinessRejected("frozen experiment identity required")
        unresolved = []
        for section, names in _SECTIONS.items():
            stable()
            values = snapshot[section]
            if type(values) is not dict:
                raise OfflineReadinessRejected("exact identity section required")
            for name in names:
                value = values[name]
                stable()
                if type(value) is str and value in _PLACEHOLDERS:
                    unresolved.append(f"{section}.{name}")
        # Tokenizer revision is a separate identity requirement even though
        # _SECTIONS only enumerates its materialized byte/hash fields.
        # SAME_AS_BASE is a declared relationship, not a verified commit:
        # either unresolved base marker keeps the alias unresolved too.
        tokenizer_revision = snapshot["tokenizer"].get("revision")
        base_revision = snapshot["base"]["revision"]
        if (
            (type(tokenizer_revision) is str and tokenizer_revision in _PLACEHOLDERS)
            or (
                type(tokenizer_revision) is str
                and tokenizer_revision == "SAME_AS_BASE"
                and type(base_revision) is str and base_revision in _PLACEHOLDERS
            )
        ):
            unresolved.append("tokenizer.revision")
        stable()
        fields = tuple(sorted(unresolved))
        canonical = json.dumps(
            snapshot, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
        stable()
        digest = hashlib.sha256(canonical).hexdigest()
        output = OfflineReadinessInventory(digest, fields, len(fields))
        saved = (
            output.snapshot_sha256, output.unresolved_paths,
            output.unresolved_count,
        )

        def stable_output() -> None:
            if (
                type(output) is not OfflineReadinessInventory
                or any(now is not old for now, old in zip(
                    (output.snapshot_sha256, output.unresolved_paths,
                     output.unresolved_count), saved, strict=True,
                ))
                or type(output.unresolved_paths) is not tuple
                or type(output.unresolved_count) is not int
            ):
                raise OfflineReadinessRejected("readiness inventory changed")
            stable()

        stable_output()
        descriptors = _ORIGINAL_INVENTORY_DENIALS
        if any(type(descriptor) is not property for descriptor in descriptors):
            raise OfflineReadinessRejected("readiness denial descriptor invalid")

        def stable_denials() -> None:
            if any(
                getattr(OfflineReadinessInventory, name) is not original
                for name, original in zip(_AUTHORITY, descriptors, strict=True)
            ):
                raise OfflineReadinessRejected("readiness authority descriptor changed")

        stable_denials()
        for name in _AUTHORITY:
            if getattr(output, name) is not False:
                raise OfflineReadinessRejected("readiness inventory gained authority")
            # Any False-returning getter may retarget an EARLIER authority
            # descriptor or replace an equal-valued result carrier.
            stable_denials()
            stable_output()
        stable_denials()
        stable_output()
        return output
    except (KeyError, TypeError, OverflowError, RecursionError, UnicodeError) as exc:
        raise OfflineReadinessRejected("unreadable offline readiness snapshot") from exc

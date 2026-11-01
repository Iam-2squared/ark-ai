"""Offline V3 execution-snapshot placeholder inventory; never an approval gate.

This reports only literal unresolved placeholder positions from an unapproved
snapshot. Resolved-looking values are NOT independently verified identities,
reviewer consent, provider billing caps, or permission to run training.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .preflight import _assert_json_tree_epoch, _pin_json_tree

_SECTIONS = {
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
}
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


def inventory_unapproved_v3_readiness(snapshot: dict) -> OfflineReadinessInventory:
    """List literal unfinished identities/budget fields without opening gates.

    This never interprets the absence of placeholders as execution readiness.
    The five current authorization flags must ALL be exact False. The output
    intentionally exposes field names only, not private path/content values.
    """
    if type(snapshot) is not dict:
        raise OfflineReadinessRejected("exact snapshot mapping required")
    try:
        epoch = _pin_json_tree(snapshot)

        def stable() -> None:
            _assert_json_tree_epoch(snapshot, epoch)

        stable()
        authorization = snapshot["authorization"]
        if type(authorization) is not dict or any(
            type(authorization.get(key)) is not bool
            or authorization[key] is not False
            for key in _DENIED
        ):
            raise OfflineReadinessRejected("unapproved authorization flags required")
        stable()
        if (
            type(snapshot.get("schema_version")) is not int
            or snapshot["schema_version"] != 1
            or snapshot.get("experiment_id") != "v3-format-compliance-001"
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
        # SAME_AS_BASE is a declared relationship, not a verified tokenizer
        # commit. Explicitly report it while the referenced base is missing.
        if (
            snapshot["tokenizer"].get("revision") == "SAME_AS_BASE"
            and snapshot["base"]["revision"] == "UNRESOLVED"
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
                or (output.snapshot_sha256, output.unresolved_paths,
                    output.unresolved_count) != saved
                or type(output.unresolved_paths) is not tuple
                or type(output.unresolved_count) is not int
            ):
                raise OfflineReadinessRejected("readiness inventory changed")
            stable()

        stable_output()
        descriptors = tuple(getattr(OfflineReadinessInventory, key) for key in _AUTHORITY)
        for name, original in zip(_AUTHORITY, descriptors, strict=True):
            if getattr(output, name) is not False:
                raise OfflineReadinessRejected("readiness inventory gained authority")
            stable_output()
            if getattr(OfflineReadinessInventory, name) is not original:
                raise OfflineReadinessRejected("readiness authority descriptor changed")
        stable_output()
        return output
    except (KeyError, TypeError, OverflowError, RecursionError, UnicodeError) as exc:
        raise OfflineReadinessRejected("unreadable offline readiness snapshot") from exc

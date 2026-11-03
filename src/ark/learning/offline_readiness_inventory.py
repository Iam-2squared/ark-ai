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


_ORIGINAL_INVENTORY_DENIALS = tuple(
    getattr(OfflineReadinessInventory, name) for name in _AUTHORITY
)


def inventory_unapproved_v3_readiness(snapshot: dict) -> OfflineReadinessInventory:
    """List literal unfinished identities/budget fields without opening gates.

    This never interprets the absence of placeholders as execution readiness.
    The five current authorization flags must ALL be exact False. The output
    intentionally exposes field names only, not private path/content values.
    """
    if type(snapshot) is not dict:
        raise OfflineReadinessRejected("exact snapshot mapping required")
    # The denial definitions were fixed when this module was imported.
    # A preinstalled False-only property is not an original denial: capturing
    # it as the baseline at call time would launder a replaced callback.
    if any(
        getattr(OfflineReadinessInventory, key, None) is not original
        for key, original in zip(
            _AUTHORITY, _ORIGINAL_INVENTORY_DENIALS, strict=True,
        )
    ):
        raise OfflineReadinessRejected("readiness authority descriptor changed")
    try:
        epoch = _pin_json_tree(snapshot)

        def stable() -> None:
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

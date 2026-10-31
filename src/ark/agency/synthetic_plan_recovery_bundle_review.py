"""Detached, deny-only bundle of plan-wide synthetic WRITE recovery witnesses.

This module serializes independently retained per-WRITE local forensic evidence.
It never opens a store, executes a backend, grants consent, or makes separate
SQLite stores atomic. A SHA-256 digest detects accidental changes, not forgery:
the caller must keep the bundle separately from the databases being reviewed.
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass, fields

from .synthetic_recovery_archive_review import (
    SyntheticRecoveryArchive,
    _restore,
    archive_synthetic_recovery,
)
from .synthetic_write_plan_recovery_review import (
    SyntheticWritePlanReview,
)

_LABEL = b"ARK-synthetic-write-plan-bundle-v1\\0"
_MAX_BYTES = 4_000_000
_MAX_STEPS = 128


class SyntheticWritePlanBundleRejected(RuntimeError):
    """A detached plan-wide forensic bundle cannot be trusted."""


@dataclass(frozen=True, slots=True)
class SyntheticWritePlanBundle:
    canonical_json: bytes
    digest: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_outcome_known(self) -> bool:
        return False


def _digest(data: bytes) -> str:
    return "splanbundle_" + hashlib.sha256(_LABEL + data).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def _sorted_unique(values: object, names: set[str]) -> bool:
    return (
        type(values) is list
        and all(type(name) is str and name in names for name in values)
        and values == sorted(set(values))
    )


def restore_synthetic_write_plan_bundle(
    bundle: SyntheticWritePlanBundle,
) -> tuple[SyntheticRecoveryArchive, ...]:
    """Validate and detach per-WRITE witnesses without DB reads or authority.

    A matching local digest is not authenticated consent or a verified action
    result. Every returned per-step archive needs independent custody before
    it is later used as a retained prefix in a separate restart diagnosis.
    """
    if (
        type(bundle) is not SyntheticWritePlanBundle
        or type(bundle.canonical_json) is not bytes
        or not 0 < len(bundle.canonical_json) <= _MAX_BYTES
        or type(bundle.digest) is not str
    ):
        raise SyntheticWritePlanBundleRejected("invalid bundle bytes")
    original_bytes = bundle.canonical_json
    original_digest = bundle.digest
    if original_digest != _digest(original_bytes):
        raise SyntheticWritePlanBundleRejected("bundle digest mismatch")

    def assert_epoch() -> None:
        if (
            bundle.canonical_json is not original_bytes
            or bundle.digest is not original_digest
        ):
            raise SyntheticWritePlanBundleRejected("bundle changed during decode")

    try:
        payload = json.loads(original_bytes)
        assert_epoch()
        if (
            type(payload) is not dict
            or set(payload) != {
                "version", "topology_digest", "uncertain",
                "downstream_hold", "terminal_hold", "steps",
            }
            or _canonical(payload) != original_bytes
            or type(payload["version"]) is not int
            or payload["version"] != 1
            or type(payload["topology_digest"]) is not str
            or not payload["topology_digest"].startswith("plan_")
            or type(payload["steps"]) is not list
            or not 1 <= len(payload["steps"]) <= _MAX_STEPS
        ):
            raise SyntheticWritePlanBundleRejected("noncanonical bundle shape")
        archives: list[SyntheticRecoveryArchive] = []
        names: list[str] = []
        uncertain: list[str] = []
        common_witnesses = None
        for entry in payload["steps"]:
            assert_epoch()
            if type(entry) is not dict or set(entry) != {"data", "digest"}:
                raise SyntheticWritePlanBundleRejected("invalid step archive shape")
            if type(entry["data"]) is not str or type(entry["digest"]) is not str:
                raise SyntheticWritePlanBundleRejected("invalid step archive carrier")
            data = base64.b64decode(entry["data"], validate=True)
            if base64.b64encode(data).decode("ascii") != entry["data"]:
                raise SyntheticWritePlanBundleRejected("noncanonical step encoding")
            archive = SyntheticRecoveryArchive(data, entry["digest"])
            identity, plan, ledger, audit, link, occurrences, links = _restore(
                archive
            )
            if plan.topology_digest != payload["topology_digest"]:
                raise SyntheticWritePlanBundleRejected("step topology mismatch")
            witnesses = (plan, ledger, audit, link)
            if common_witnesses is None:
                common_witnesses = witnesses
            elif witnesses != common_witnesses:
                raise SyntheticWritePlanBundleRejected("cross-step witness mismatch")
            names.append(identity["step_id"])
            if identity["ambiguous_write"] or occurrences or links:
                uncertain.append(identity["step_id"])
            archives.append(archive)
            assert_epoch()
        if names != sorted(set(names)):
            raise SyntheticWritePlanBundleRejected("duplicate or unordered steps")
        valid_names = set(names)
        if (
            not _sorted_unique(payload["uncertain"], valid_names)
            or not _sorted_unique(payload["downstream_hold"], valid_names)
            or not _sorted_unique(payload["terminal_hold"], valid_names)
            or payload["uncertain"] != sorted(uncertain)
        ):
            raise SyntheticWritePlanBundleRejected("inconsistent plan holds")
        assert_epoch()
        result = tuple(archives)
        assert_epoch()
        return result
    except SyntheticWritePlanBundleRejected:
        raise
    except (
        ValueError, TypeError, KeyError, AttributeError, UnicodeError,
        OverflowError, RecursionError, RuntimeError,
    ) as exc:
        raise SyntheticWritePlanBundleRejected("malformed recovery bundle") from exc


def bundle_synthetic_write_plan(
    review: SyntheticWritePlanReview,
) -> SyntheticWritePlanBundle:
    """Capture each independently validated WRITE review in a bounded bundle."""
    if (
        type(review) is not SyntheticWritePlanReview
        or type(review.steps) is not tuple
        or not 1 <= len(review.steps) <= _MAX_STEPS
    ):
        raise SyntheticWritePlanBundleRejected("exact bounded plan review required")
    try:
        entities = [review, *review.steps]
        for step in review.steps:
            entities.extend((
                step.plan_tail, step.ledger_witness,
                step.audit_witness, step.link_witness,
            ))
        original = tuple(
            (
                entity,
                tuple((field.name, getattr(entity, field.name))
                      for field in fields(entity)),
            )
            for entity in entities if entity is not None
        )

        def assert_epoch() -> None:
            if any(
                getattr(entity, name) is not prior
                for entity, values in original
                for name, prior in values
            ):
                raise SyntheticWritePlanBundleRejected(
                    "plan review changed during bundle capture"
                )

        assert_epoch()
        payload_steps = []
        for step in review.steps:
            assert_epoch()
            archived = archive_synthetic_recovery(step)
            assert_epoch()
            payload_steps.append({
                "data": base64.b64encode(archived.canonical_json).decode("ascii"),
                "digest": archived.digest,
            })
        payload = {
            "version": 1,
            "topology_digest": review.plan_topology_digest,
            "uncertain": list(review.uncertain_step_ids),
            "downstream_hold": list(review.downstream_write_hold_step_ids),
            "terminal_hold": list(review.terminally_blocked_write_step_ids),
            "steps": payload_steps,
        }
        assert_epoch()
        data = _canonical(payload)
        if not 0 < len(data) <= _MAX_BYTES:
            raise SyntheticWritePlanBundleRejected("plan bundle budget exceeded")
        digest = _digest(data)
        assert_epoch()
        result = SyntheticWritePlanBundle(data, digest)
        restore_synthetic_write_plan_bundle(result)
        assert_epoch()
        if (
            type(result) is not SyntheticWritePlanBundle
            or result.canonical_json is not data
            or result.digest is not digest
        ):
            raise SyntheticWritePlanBundleRejected("constructed bundle changed")
        return result
    except SyntheticWritePlanBundleRejected:
        raise
    except (
        ValueError, TypeError, KeyError, AttributeError,
        OverflowError, RecursionError, RuntimeError,
    ) as exc:
        raise SyntheticWritePlanBundleRejected(
            "cannot capture synthetic recovery bundle"
        ) from exc

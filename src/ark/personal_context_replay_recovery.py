"""Read-only restart triage for synthetic Personal Context replay reservations.

A same-count local history change or rollback is refused. New append history is
UNVERIFIED: a local SQLite hash chain does not authenticate its writer or prove
retention, consent, revocation, deletion, external effect or historical prefix.
No real content is read, disclosed, deleted, scheduled or dispatched.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass

from . import personal_context_replay_ledger as _ledger_module
from .personal_context_replay_ledger import (
    DisconnectedContextReplayLedger,
    OfflineContextReplayRejected,
    OfflineContextReplayWitness,
    _check_witness,
    _inspect,
)

_DOMAIN = b"ARK-offline-context-replay-restart-review-v1\0"
# Identity-only, local diagnostic hashing must not call substituted modules,
# serializers or digest code on retained Personal Context replay metadata.
# Keep these import-time witnesses before the first ledger/witness read.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON = json
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN
_LEDGER_TYPE = DisconnectedContextReplayLedger
# A hostile replacement lookup hook could run before the first local path
# read, even with an exact ledger type. Pin these hooks at import time.
_LEDGER_ACCESS_HOOKS = ("__getattribute__", "__getattr__")
_ORIGINAL_LEDGER_ACCESS_HOOKS = tuple(
    vars(_LEDGER_TYPE).get(name) for name in _LEDGER_ACCESS_HOOKS
)
_WITNESS_TYPE = OfflineContextReplayWitness
# A restart review must not call newly rebound ledger row inspectors or
# witness validators on private, linkable local identifiers. Recheck both
# local bindings and the defining module before EVERY synthetic read.
# The recovery-local _inspect binding is a deliberate synthetic fault-injection
# seam for existing later-epoch tests; only the defining ledger implementation
# is pinned before a potentially private ledger.witness() callback.
_ORIGINAL_LEDGER_INSPECT = _ledger_module._inspect
_ORIGINAL_LEDGER_CHECK_WITNESS = _check_witness
_ORIGINAL_LEDGER_OPEN = vars(_LEDGER_TYPE)["_open"]
_ORIGINAL_LEDGER_WITNESS = vars(_LEDGER_TYPE)["witness"]


class OfflineContextRecoveryRejected(OfflineContextReplayRejected):
    """Local replay-recovery evidence cannot be interpreted safely."""


@dataclass(frozen=True, slots=True)
class OfflineContextRecoveryReview:
    retained_count: int
    observed_count: int
    status: str
    comparison_sha256: str

    @property
    def historical_prefix_proven(self) -> bool:
        return False

    @property
    def independent_custody_proven(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def revocation_freshness_verified(self) -> bool:
        return False

    @property
    def context_disclosure_authorized(self) -> bool:
        return False

    @property
    def tool_dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


_RESULT_TYPE = OfflineContextRecoveryReview
_ORIGINAL_RESULT_INIT = vars(_RESULT_TYPE)["__init__"]
# Persisted recovery evidence is an exact slotted carrier. A patched field
# descriptor, allocation or lookup hook can execute code before type/value
# checks on report fields. Capture original class descriptors at import time.
_RESULT_FIELDS = (
    "retained_count", "observed_count", "status", "comparison_sha256",
)
_ORIGINAL_RESULT_FIELDS = tuple(
    vars(_RESULT_TYPE)[name] for name in _RESULT_FIELDS
)
_RESULT_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_RESULT_HOOKS = tuple(
    vars(_RESULT_TYPE).get(name) for name in _RESULT_HOOKS
)
_RESULT_DENIALS = (
    "historical_prefix_proven", "independent_custody_proven",
    "consent_verified", "revocation_freshness_verified",
    "context_disclosure_authorized", "tool_dispatch_authorized",
    "automatic_replay_authorized",
)
_ORIGINAL_RESULT_DENIALS = tuple(
    vars(_RESULT_TYPE)[name] for name in _RESULT_DENIALS
)


def _assert_result_denials() -> None:
    # The codec receives private, locally retained replay identifiers. Check
    # it before any caller ledger read and after every overridable callback.
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json is not _ORIGINAL_JSON
        or json.dumps is not _ORIGINAL_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
    ):
        raise OfflineContextRecoveryRejected(
            "context replay digest implementation changed"
        )
    # No False-looking replacement may establish a new authority baseline.
    if (
        OfflineContextRecoveryReview is not _RESULT_TYPE
        or vars(_RESULT_TYPE).get("__init__") is not _ORIGINAL_RESULT_INIT
        or any(
            vars(_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                _RESULT_FIELDS, _ORIGINAL_RESULT_FIELDS, strict=True,
            )
        )
        or any(
            vars(_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                _RESULT_HOOKS, _ORIGINAL_RESULT_HOOKS, strict=True,
            )
        )
        or any(
            vars(_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                _RESULT_DENIALS, _ORIGINAL_RESULT_DENIALS, strict=True,
            )
        )
    ):
        raise OfflineContextRecoveryRejected(
            "context replay review result gained authority"
        )


def _assert_ledger_access_hooks() -> None:
    if (
        DisconnectedContextReplayLedger is not _LEDGER_TYPE
        or _check_witness is not _ORIGINAL_LEDGER_CHECK_WITNESS
        or _ledger_module._inspect is not _ORIGINAL_LEDGER_INSPECT
        or _ledger_module._check_witness is not _ORIGINAL_LEDGER_CHECK_WITNESS
        or vars(_LEDGER_TYPE).get("_open") is not _ORIGINAL_LEDGER_OPEN
        or vars(_LEDGER_TYPE).get("witness") is not _ORIGINAL_LEDGER_WITNESS
        or any(
            vars(_LEDGER_TYPE).get(name) is not original
            for name, original in zip(
                _LEDGER_ACCESS_HOOKS, _ORIGINAL_LEDGER_ACCESS_HOOKS, strict=True,
            )
        )
    ):
        raise OfflineContextRecoveryRejected("context replay ledger access hook changed")


def _witness_fields(value: object) -> tuple[int, str]:
    # The ledger already pins witness field, constructor and lookup hooks at
    # import time, before any possibly hostile descriptor gets executed.
    # Recovery must never validate the denial getter alone while reading
    # externally retained synthetic identity metadata.
    try:
        return _check_witness(value)
    except OfflineContextReplayRejected as exc:
        raise OfflineContextRecoveryRejected(
            "invalid exact context replay witness"
        ) from exc

def review_restarted_context_replay(
    ledger: DisconnectedContextReplayLedger,
    retained: OfflineContextReplayWitness,
) -> OfflineContextRecoveryReview:
    """Compare a locally retained witness with a fresh read-only SQLite view.

    The caller must store retained separately from the DB. An advancing history
    remains unverified even when both local objects pass structural checks.
    The result never authorizes replay or use of Personal Context.
    """
    if type(ledger) is not _LEDGER_TYPE:
        raise OfflineContextRecoveryRejected("exact disconnected context ledger required")
    _assert_result_denials()
    # Existing witness-descriptor preaccess denials take precedence over a
    # separately patched _open method used to assert no SQLite was reached.
    # Guard the locally callable validator before reading retained fields.
    if _check_witness is not _ORIGINAL_LEDGER_CHECK_WITNESS:
        raise OfflineContextRecoveryRejected("context replay ledger access hook changed")
    pinned = _witness_fields(retained)
    _assert_ledger_access_hooks()
    pinned_path = ledger._path
    pinned_carrier = retained
    pinned_count, pinned_digest = retained.count, retained.chain_sha256

    def stable() -> None:
        _assert_result_denials()
        _assert_ledger_access_hooks()
        if (
            type(ledger) is not _LEDGER_TYPE
            or ledger._path is not pinned_path
            or retained is not pinned_carrier
            or _witness_fields(retained) != pinned
            or retained.count is not pinned_count
            or retained.chain_sha256 is not pinned_digest
        ):
            raise OfflineContextRecoveryRejected("retained context replay witness changed")

    stable()
    observed = ledger.witness()
    stable()
    current = _witness_fields(observed)
    observed_count, observed_digest = observed.count, observed.chain_sha256

    def stable_observed() -> None:
        stable()
        if (
            type(observed) is not _WITNESS_TYPE
            or _witness_fields(observed) != current
            or observed.count is not observed_count
            or observed.chain_sha256 is not observed_digest
        ):
            raise OfflineContextRecoveryRejected("observed context replay witness changed")

    def verify_durable_tip() -> None:
        # witness() is a public, overridable callback. It can return a forged
        # or stale but exact-type result, including after an intervening SQLite
        # append. Read the real rows in a separate read-only transaction.
        stable_observed()
        try:
            with closing(ledger._open(read_only=True)) as conn:
                conn.execute("BEGIN")
                try:
                    durable = _inspect(conn)
                    stable_observed()
                    if _witness_fields(durable) != current:
                        raise OfflineContextRecoveryRejected(
                            "context replay durable tip differs from callback"
                        )
                    conn.commit()
                except BaseException:
                    conn.rollback()
                    raise
        except (sqlite3.Error, OfflineContextReplayRejected) as exc:
            if type(exc) is OfflineContextRecoveryRejected:
                raise
            raise OfflineContextRecoveryRejected(
                "context replay durable tip cannot be verified"
            ) from exc
        stable_observed()

    verify_durable_tip()
    if current[0] < pinned[0]:
        raise OfflineContextRecoveryRejected("context replay history count regressed")
    if current[0] == pinned[0] and current[1] != pinned[1]:
        raise OfflineContextRecoveryRejected("context replay history rewritten at same count")
    status = (
        "ADVANCED_HISTORY_UNVERIFIED"
        if current[0] > pinned[0]
        else "UNCHANGED_LOCAL_HISTORY"
    )
    payload = json.dumps(
        (pinned, current, status),
        separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    stable_observed()
    digest = hashlib.sha256(_DOMAIN + payload).hexdigest()
    stable_observed()
    # Durable inspection and digest callbacks can replace a class initializer.
    # Never invoke a newly installed constructor on sensitive local metadata.
    _assert_result_denials()
    result = _RESULT_TYPE(pinned[0], current[0], status, digest)
    _assert_result_denials()

    def verify_result() -> None:
        # Denial-only properties are arbitrary Python callbacks in synthetic
        # fixtures: a False getter can still rewrite an earlier checked result
        # or silently tamper with the local SQLite source. Check the original
        # carriers after EACH getter and re-read the durable tip once more
        # after the LAST callback. None of this attests an external actor.
        def stable_result_carriers() -> None:
            _assert_result_denials()
            stable_observed()
            if (
                type(result) is not _RESULT_TYPE
                or type(result.retained_count) is not int
                or result.retained_count != pinned[0]
                or type(result.observed_count) is not int
                or result.observed_count != current[0]
                or type(result.status) is not str
                or result.status is not status
                or type(result.comparison_sha256) is not str
                or result.comparison_sha256 is not digest
            ):
                raise OfflineContextRecoveryRejected(
                    "context replay review result changed"
                )

        stable_result_carriers()
        for name in _RESULT_DENIALS:
            _assert_result_denials()
            if getattr(result, name) is not False:
                raise OfflineContextRecoveryRejected(
                    "context replay review result gained authority"
                )
            stable_result_carriers()
        verify_durable_tip()
        stable_result_carriers()

    verify_result()
    verify_durable_tip()
    verify_result()
    return result

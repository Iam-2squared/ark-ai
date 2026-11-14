"""Manual-only dual-observer Memory COMMIT ambiguity reconciliation.

The two independent local SQLite review paths must agree on the same retained
and observed event prefixes. Two passes detect some concurrent history drift,
not cross-process atomicity, writer identity, or exactly-once effects. No write.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from . import generation_cas_outcome_review as outcome_module
from . import postcommit_uncertainty_review as triage_module
from .contracts import MemoryScope, MemoryWrite
from .generation_fenced_cas import (
    MemoryGenerationCASRejected,
    MemoryGenerationCASToken,
    _require_original_generation_inputs,
    _token_fields,
)
from .sqlite_store import SQLiteMemoryStore

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-memory-ambiguous-dual-review-v1\0"
# Reconciliation has its own hash boundary after two read-only reviews.
# Bind its actual digest implementation and domain before accessing SQLite.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN
_TRIAGE_FN = triage_module.review_uncertain_memory_commit
_OUTCOME_FN = outcome_module.review_memory_generation_cas_outcome
_TRIAGE = triage_module.MemoryCommitTriage
_OUTCOME = outcome_module.MemoryCASOutcomeReview
_TRIAGE_DENIALS = (
    "automatic_retry_authorized", "write_authorized",
    "caller_attribution_proven", "trusted_clock_proven",
)
_OUTCOME_DENIALS = (
    "commit_attributed_to_caller", "automatic_retry_authorized",
    "consent_authenticated", "trusted_clock_verified",
    "external_action_authorized",
)
_TRIAGE_ORIGINALS = tuple(vars(_TRIAGE)[name] for name in _TRIAGE_DENIALS)
_OUTCOME_ORIGINALS = tuple(vars(_OUTCOME)[name] for name in _OUTCOME_DENIALS)
_DISPOSITIONS = {
    ("LOCAL_UNCHANGED", "UNCHANGED_OBSERVED"): "LOCAL_UNCHANGED_REVIEW",
    ("ONE_MATCHING_UPDATE_VISIBLE", "ONE_MATCHING_UPDATE_OBSERVED"):
        "MATCHING_ROW_MANUAL_REVIEW",
    ("INDETERMINATE", "DIVERGED_OBSERVED"): "DIVERGED_MANUAL_REVIEW",
}


class MemoryAmbiguityPairRejected(ValueError):
    """Two local read-only CAS reviewers cannot agree on one safe snapshot."""


@dataclass(frozen=True, slots=True)
class MemoryAmbiguityPair:
    disposition: str
    retained_prefix_sha256: str
    observed_prefix_sha256: str
    observed_row_sha256: str
    triage_receipt_sha256: str
    outcome_receipt_sha256: str
    reconciliation_sha256: str

    @property
    def caller_commit_authenticated(self) -> bool:
        return False

    @property
    def automatic_retry_authorized(self) -> bool:
        return False

    @property
    def write_authorized(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False


_RESULT = MemoryAmbiguityPair
_ORIGINAL_RESULT_INIT = vars(_RESULT)["__init__"]
_DENIALS = (
    "caller_commit_authenticated", "automatic_retry_authorized",
    "write_authorized", "trusted_clock_verified",
)
_ORIGINALS = tuple(vars(_RESULT)[name] for name in _DENIALS)

# Each supposedly frozen, slotted receipt remains reflectively patchable at
# class level. Check the original field descriptors and lookup/constructor
# hooks without accessing them: forged descriptors can execute on first read,
# before downstream digest and False-only authority checks.
_RESULT_FIELDS = (
    "disposition", "retained_prefix_sha256", "observed_prefix_sha256",
    "observed_row_sha256", "triage_receipt_sha256",
    "outcome_receipt_sha256", "reconciliation_sha256",
)
_TRIAGE_FIELDS = (
    "memory_id", "retained_event_id", "observed_event_id",
    "retained_prefix_sha256", "observed_prefix_sha256",
    "disposition", "report_sha256",
)
_OUTCOME_FIELDS = (
    "observation", "retained_prefix_sha256", "observed_prefix_sha256",
    "observed_row_sha256", "expected_content_sha256", "review_sha256",
)
_CARRIER_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_RESULT_FIELDS = tuple(vars(_RESULT)[name] for name in _RESULT_FIELDS)
_ORIGINAL_TRIAGE_FIELDS = tuple(vars(_TRIAGE)[name] for name in _TRIAGE_FIELDS)
_ORIGINAL_OUTCOME_FIELDS = tuple(vars(_OUTCOME)[name] for name in _OUTCOME_FIELDS)
_ORIGINAL_RESULT_HOOKS = tuple(vars(_RESULT).get(name) for name in _CARRIER_HOOKS)
_ORIGINAL_TRIAGE_HOOKS = tuple(vars(_TRIAGE).get(name) for name in _CARRIER_HOOKS)
_ORIGINAL_OUTCOME_HOOKS = tuple(vars(_OUTCOME).get(name) for name in _CARRIER_HOOKS)


def _require_original_review_carriers() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
    ):
        raise MemoryAmbiguityPairRejected(
            "Memory reconciliation digest implementation or domain changed"
        )
    # Class descriptors are executable code when accessed through getattr.
    # Inspect the original class dicts without executing a forged __get__.
    if (
        triage_module.MemoryCommitTriage is not _TRIAGE
        or outcome_module.MemoryCASOutcomeReview is not _OUTCOME
        or MemoryAmbiguityPair is not _RESULT
        or vars(_RESULT).get("__init__") is not _ORIGINAL_RESULT_INIT
        or any(
            vars(cls).get(name) is not original
            for cls, names, originals in (
                (_RESULT, _RESULT_FIELDS, _ORIGINAL_RESULT_FIELDS),
                (_TRIAGE, _TRIAGE_FIELDS, _ORIGINAL_TRIAGE_FIELDS),
                (_OUTCOME, _OUTCOME_FIELDS, _ORIGINAL_OUTCOME_FIELDS),
            )
            for name, original in zip(names, originals, strict=True)
        )
        or any(
            vars(cls).get(name) is not original
            for cls, originals in (
                (_RESULT, _ORIGINAL_RESULT_HOOKS),
                (_TRIAGE, _ORIGINAL_TRIAGE_HOOKS),
                (_OUTCOME, _ORIGINAL_OUTCOME_HOOKS),
            )
            for name, original in zip(_CARRIER_HOOKS, originals, strict=True)
        )
        or any(
            vars(_TRIAGE).get(name) is not old
            for name, old in zip(_TRIAGE_DENIALS, _TRIAGE_ORIGINALS, strict=True)
        )
        or any(
            vars(_OUTCOME).get(name) is not old
            for name, old in zip(_OUTCOME_DENIALS, _OUTCOME_ORIGINALS, strict=True)
        )
        or any(
            vars(_RESULT).get(name) is not old
            for name, old in zip(_DENIALS, _ORIGINALS, strict=True)
        )
    ):
        raise MemoryAmbiguityPairRejected("Memory review authority changed")


def review_memory_ambiguous_commit_pair(
    store: SQLiteMemoryStore,
    proposed: MemoryWrite,
    *,
    retained: MemoryGenerationCASToken,
) -> MemoryAmbiguityPair:
    """Return a detached no-retry diagnostic only on dual-view agreement."""
    # Reject class-level getters/constructors before reading even proposed.scope.
    try:
        _require_original_generation_inputs()
    except MemoryGenerationCASRejected as exc:
        raise MemoryAmbiguityPairRejected("Memory triage input carrier changed") from exc
    if (
        type(store) is not SQLiteMemoryStore
        or type(proposed) is not MemoryWrite
        or type(proposed.scope) is not MemoryScope
        or type(retained) is not MemoryGenerationCASToken
    ):
        raise MemoryAmbiguityPairRejected("exact Memory triage inputs required")
    _require_original_review_carriers()
    source_fields = (
        proposed.scope, proposed.scope.owner_id, proposed.scope.namespace,
        proposed.source_id, proposed.content, proposed.metadata,
        proposed.expires_at_ms, store.path,
    )
    metadata = dict(proposed.metadata)
    try:
        token_fields = _token_fields(retained)
    except (TypeError, ValueError) as exc:
        raise MemoryAmbiguityPairRejected("invalid retained generation token") from exc

    def stable() -> None:
        _require_original_review_carriers()
        try:
            _require_original_generation_inputs()
        except MemoryGenerationCASRejected as exc:
            raise MemoryAmbiguityPairRejected("Memory triage input carrier changed") from exc
        if (
            triage_module.review_uncertain_memory_commit is not _TRIAGE_FN
            or outcome_module.review_memory_generation_cas_outcome is not _OUTCOME_FN
        ):
            raise MemoryAmbiguityPairRejected("Memory review authority changed")
        if (
            type(store) is not SQLiteMemoryStore
            or type(proposed) is not MemoryWrite
            or type(proposed.scope) is not MemoryScope
            or any(current is not before for current, before in zip(
                (
                    proposed.scope, proposed.scope.owner_id,
                    proposed.scope.namespace, proposed.source_id,
                    proposed.content, proposed.metadata, proposed.expires_at_ms,
                    store.path,
                ),
                source_fields, strict=True,
            ))
            or dict(proposed.metadata) != metadata
            or _token_fields(retained) != token_fields
            or any(
                current is not original
                for current, original in zip(
                    _token_fields(retained), token_fields, strict=True,
                )
            )
        ):
            raise MemoryAmbiguityPairRejected("Memory triage input epoch changed")

    def read_once() -> tuple[str, str, str, str, str, str]:
        stable()
        try:
            first = _TRIAGE_FN(store, proposed, retained_before=retained)
            stable()
            if type(first) is not _TRIAGE:
                raise MemoryAmbiguityPairRejected("invalid Memory triage result type")
            # The second reviewer is a callback boundary. Retain the first
            # child BEFORE invoking it, not after it may have rewritten the
            # first (reflectively mutable) frozen dataclass.
            triage_epoch = (
                first.memory_id, first.retained_event_id, first.observed_event_id,
                first.retained_prefix_sha256, first.observed_prefix_sha256,
                first.disposition, first.report_sha256,
            )
            second = _OUTCOME_FN(store, proposed, retained=retained)
            stable()
        except (
            triage_module.MemoryCommitTriageRejected,
            outcome_module.MemoryCASOutcomeRejected,
        ) as exc:
            raise MemoryAmbiguityPairRejected(
                "read-only Memory reviewers rejected an ambiguous generation"
            ) from exc
        if type(second) is not _OUTCOME:
            raise MemoryAmbiguityPairRejected("invalid Memory outcome result type")
        outcome_epoch = (
            second.observation, second.retained_prefix_sha256,
            second.observed_prefix_sha256, second.observed_row_sha256,
            second.expected_content_sha256, second.review_sha256,
        )

        def stable_children() -> None:
            if (
                type(first) is not _TRIAGE or type(second) is not _OUTCOME
                or any(current is not original for current, original in zip(
                    (
                        first.memory_id, first.retained_event_id,
                        first.observed_event_id, first.retained_prefix_sha256,
                        first.observed_prefix_sha256, first.disposition,
                        first.report_sha256,
                    ), triage_epoch, strict=True,
                ))
                or any(current is not original for current, original in zip(
                    (
                        second.observation, second.retained_prefix_sha256,
                        second.observed_prefix_sha256, second.observed_row_sha256,
                        second.expected_content_sha256, second.review_sha256,
                    ), outcome_epoch, strict=True,
                ))
            ):
                raise MemoryAmbiguityPairRejected(
                    "Memory child receipt changed across review callbacks"
                )
            stable()

        stable_children()
        # Independent receipt recomputation rejects a syntactically valid
        # but invented child SHA, even if a wrapper replaced it BEFORE return.
        # These are untrusted local hashes, NOT authenticated writer receipts.
        triage_payload = triage_epoch[:-1]
        if (
            triage_epoch[0] != token_fields[0]
            or type(triage_epoch[1]) is not int
            or type(triage_epoch[2]) is not int
            or triage_epoch[1] != token_fields[2]
            or triage_epoch[2] < triage_epoch[1]
            or triage_epoch[-1] != triage_module._digest(
                triage_module._DOMAIN, triage_payload,
            )
        ):
            raise MemoryAmbiguityPairRejected("Memory triage child digest mismatch")
        outcome_payload = outcome_epoch[:-1]
        expected_outcome_sha = hashlib.sha256(
            outcome_module._DOMAIN + json.dumps(
                outcome_payload, separators=(",", ":"),
                ensure_ascii=True, allow_nan=False,
            ).encode("ascii")
        ).hexdigest()
        if outcome_epoch[-1] != expected_outcome_sha:
            raise MemoryAmbiguityPairRejected("Memory outcome child digest mismatch")
        stable_children()
        for report, names in (
            (first, _TRIAGE_DENIALS), (second, _OUTCOME_DENIALS),
        ):
            for name in names:
                if getattr(report, name) is not False:
                    raise MemoryAmbiguityPairRejected("Memory reviewer gained authority")
                stable_children()
        pair = (first.disposition, second.observation)
        if pair not in _DISPOSITIONS:
            raise MemoryAmbiguityPairRejected(
                "Memory reviewers disagree; manual investigation required"
            )
        if (
            first.retained_prefix_sha256 != token_fields[4]
            or second.retained_prefix_sha256 != token_fields[4]
            or first.observed_prefix_sha256 != second.observed_prefix_sha256
        ):
            raise MemoryAmbiguityPairRejected("Memory event prefixes disagree")
        # Both local reviewers have distinct receipt fingerprints. A second
        # pass must bind *both* receipts; otherwise the Outcome receipt could
        # change without affecting the pair's final reconciliation digest.
        values = (
            _DISPOSITIONS[pair], first.retained_prefix_sha256,
            first.observed_prefix_sha256, second.observed_row_sha256,
            first.report_sha256, second.review_sha256,
        )
        if any(
            type(value) is not str or _SHA.fullmatch(value) is None
            for value in values[1:]
        ):
            raise MemoryAmbiguityPairRejected("invalid Memory evidence digest")
        stable_children()
        return values

    first = read_once()
    if read_once() != first:
        raise MemoryAmbiguityPairRejected("Memory reviewers drifted between reads")
    payload = json.dumps(first, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    digest = hashlib.sha256(_DOMAIN + payload).hexdigest()
    stable()
    # Expose both local reviewers' digests so a read-only investigator can
    # reconstruct the reconciliation hash without guessing hidden inputs.
    # These are not authenticated writer receipts or retry permission.
    # The read-only result is not authority, but its constructor is executable
    # Python and may have been swapped during either child review or hashing.
    # Refuse that code before invocation rather than relying on False getters.
    _require_original_review_carriers()
    result = _RESULT(*first, digest)
    expected = (*first, digest)

    def assert_result_epoch() -> None:
        stable()
        if (
            type(result) is not _RESULT
            or any(now is not previous for now, previous in zip(
                (
                    result.disposition, result.retained_prefix_sha256,
                    result.observed_prefix_sha256, result.observed_row_sha256,
                    result.triage_receipt_sha256, result.outcome_receipt_sha256,
                    result.reconciliation_sha256,
                ), expected, strict=True,
            ))
        ):
            raise MemoryAmbiguityPairRejected(
                "Memory reconciliation result changed during denial review"
            )

    assert_result_epoch()
    for name in _DENIALS:
        if getattr(result, name) is not False:
            raise MemoryAmbiguityPairRejected("Memory reconciliation gained authority")
        # A False-only getter is another synthetic callback boundary. In
        # particular the LAST getter must not retarget a detached receipt
        # after its final precheck and silently return an invented witness.
        assert_result_epoch()
    return result

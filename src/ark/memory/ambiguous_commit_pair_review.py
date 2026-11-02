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
from .generation_fenced_cas import MemoryGenerationCASToken, _token_fields
from .sqlite_store import SQLiteMemoryStore

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-memory-ambiguous-dual-review-v1\0"
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
_TRIAGE_ORIGINALS = tuple(getattr(_TRIAGE, name) for name in _TRIAGE_DENIALS)
_OUTCOME_ORIGINALS = tuple(getattr(_OUTCOME, name) for name in _OUTCOME_DENIALS)
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
_DENIALS = (
    "caller_commit_authenticated", "automatic_retry_authorized",
    "write_authorized", "trusted_clock_verified",
)
_ORIGINALS = tuple(getattr(_RESULT, name) for name in _DENIALS)


def review_memory_ambiguous_commit_pair(
    store: SQLiteMemoryStore,
    proposed: MemoryWrite,
    *,
    retained: MemoryGenerationCASToken,
) -> MemoryAmbiguityPair:
    """Return a detached no-retry diagnostic only on dual-view agreement."""
    if (
        type(store) is not SQLiteMemoryStore
        or type(proposed) is not MemoryWrite
        or type(proposed.scope) is not MemoryScope
        or type(retained) is not MemoryGenerationCASToken
    ):
        raise MemoryAmbiguityPairRejected("exact Memory triage inputs required")
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
        if (
            triage_module.review_uncertain_memory_commit is not _TRIAGE_FN
            or outcome_module.review_memory_generation_cas_outcome is not _OUTCOME_FN
            or any(getattr(_TRIAGE, name) is not before
                   for name, before in zip(
                       _TRIAGE_DENIALS, _TRIAGE_ORIGINALS, strict=True,
                   ))
            or any(getattr(_OUTCOME, name) is not before
                   for name, before in zip(
                       _OUTCOME_DENIALS, _OUTCOME_ORIGINALS, strict=True,
                   ))
            or any(getattr(_RESULT, name) is not before
                   for name, before in zip(_DENIALS, _ORIGINALS, strict=True))
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
        ):
            raise MemoryAmbiguityPairRejected("Memory triage input epoch changed")

    def read_once() -> tuple[str, str, str, str, str]:
        stable()
        try:
            first = _TRIAGE_FN(store, proposed, retained_before=retained)
            stable()
            second = _OUTCOME_FN(store, proposed, retained=retained)
            stable()
        except (
            triage_module.MemoryCommitTriageRejected,
            outcome_module.MemoryCASOutcomeRejected,
        ) as exc:
            raise MemoryAmbiguityPairRejected(
                "read-only Memory reviewers rejected an ambiguous generation"
            ) from exc
        if type(first) is not _TRIAGE or type(second) is not _OUTCOME:
            raise MemoryAmbiguityPairRejected("invalid Memory reviewer result type")
        for report, names in (
            (first, _TRIAGE_DENIALS), (second, _OUTCOME_DENIALS),
        ):
            for name in names:
                if getattr(report, name) is not False:
                    raise MemoryAmbiguityPairRejected("Memory reviewer gained authority")
                stable()
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
        values = (
            _DISPOSITIONS[pair], first.retained_prefix_sha256,
            first.observed_prefix_sha256, second.observed_row_sha256,
            first.report_sha256,
        )
        if any(
            type(value) is not str or _SHA.fullmatch(value) is None
            for value in values[1:]
        ):
            raise MemoryAmbiguityPairRejected("invalid Memory evidence digest")
        stable()
        return values

    first = read_once()
    if read_once() != first:
        raise MemoryAmbiguityPairRejected("Memory reviewers drifted between reads")
    payload = json.dumps(first, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    digest = hashlib.sha256(_DOMAIN + payload).hexdigest()
    stable()
    result = _RESULT(*first[:4], digest)
    expected = (*first[:4], digest)
    for name in _DENIALS:
        if (
            type(result) is not _RESULT
            or any(now is not previous for now, previous in zip(
                (
                    result.disposition, result.retained_prefix_sha256,
                    result.observed_prefix_sha256, result.observed_row_sha256,
                    result.reconciliation_sha256,
                ), expected, strict=True,
            ))
            or getattr(result, name) is not False
        ):
            raise MemoryAmbiguityPairRejected("Memory reconciliation gained authority")
        stable()
    return result

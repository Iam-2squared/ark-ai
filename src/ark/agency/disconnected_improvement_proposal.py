"""Proposal-only deterministic evidence identity for future local ARK improvement.

This is a memory-only synthetic review, not a persistent proposal lifecycle.
No code modification, training, protected evaluation, Candidate generation,
credential access, ToolBackend or paid service can be reached from this API.
Digest-only references can remain linkable; they are not privacy guarantees.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

_NAME = re.compile(r"[a-z][a-z0-9_.-]{0,63}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-disconnected-improvement-proposal-v1\0"
_MAX_PROPOSALS = 256
_MAX_SOURCES = 32
_KINDS = frozenset((
    "TEST_HARDENING", "FAILURE_INVESTIGATION", "RETRIEVAL_ADJUSTMENT",
    "PLANNER_CONTRACT_REVIEW", "FUTURE_EXPERIMENT_REVIEW",
))


class DisconnectedImprovementRejected(ValueError):
    """Unsafe, noncanonical or unbounded proposal-only fixture."""


@dataclass(frozen=True, slots=True)
class ImprovementProposalInput:
    issue_id: str
    affected_component: str
    change_class: str
    policy_revision: int
    owner_digest: str
    namespace_digest: str
    source_digests: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ImprovementProposalDraft:
    proposal_id: str
    evidence_count: int
    occurrences: int

    @property
    def code_change_authorized(self) -> bool:
        return False

    @property
    def training_authorized(self) -> bool:
        return False

    @property
    def candidate_promotion_authorized(self) -> bool:
        return False

    @property
    def protected_evaluation_opened(self) -> bool:
        return False


_INPUT = ImprovementProposalInput
_OUTPUT = ImprovementProposalDraft
_INPUT_FIELDS = (
    "issue_id", "affected_component", "change_class", "policy_revision",
    "owner_digest", "namespace_digest", "source_digests",
)
_OUTPUT_FIELDS = ("proposal_id", "evidence_count", "occurrences")
_DENIALS = (
    "code_change_authorized", "training_authorized",
    "candidate_promotion_authorized", "protected_evaluation_opened",
)
_ORIGINAL_INPUT = tuple(vars(_INPUT).get(name) for name in _INPUT_FIELDS)
_ORIGINAL_OUTPUT = tuple(vars(_OUTPUT).get(name) for name in _OUTPUT_FIELDS)
_ORIGINAL_DENIALS = tuple(vars(_OUTPUT).get(name) for name in _DENIALS)
_ORIGINAL_HASH = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_NAME = _NAME
_ORIGINAL_SHA = _SHA
_ORIGINAL_KINDS = _KINDS
_ORIGINAL_LIMITS = (_MAX_PROPOSALS, _MAX_SOURCES)
_ORIGINAL_INPUT_NAMES = _INPUT_FIELDS
_ORIGINAL_OUTPUT_NAMES = _OUTPUT_FIELDS
_ORIGINAL_DENIAL_NAMES = _DENIALS
_CARRIER_HOOK_NAMES = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_HOOKS = {
    cls: tuple(vars(cls).get(name) for name in _CARRIER_HOOK_NAMES)
    for cls in (_INPUT, _OUTPUT)
}


def _protocol() -> None:
    if (
        ImprovementProposalInput is not _INPUT
        or ImprovementProposalDraft is not _OUTPUT
        or _NAME is not _ORIGINAL_NAME or _SHA is not _ORIGINAL_SHA
        # Validators handle private owner/namespace/source digests. A
        # substituted local callback must not learn them or forge a proposal.
        or _name is not _ORIGINAL_NAME_HELPER
        or _sha is not _ORIGINAL_SHA_HELPER
        or _DOMAIN is not _ORIGINAL_DOMAIN or _KINDS is not _ORIGINAL_KINDS
        or hashlib.sha256 is not _ORIGINAL_HASH
        or json.dumps is not _ORIGINAL_DUMPS
        or type(_MAX_PROPOSALS) is not int
        or type(_MAX_SOURCES) is not int
        or (_MAX_PROPOSALS, _MAX_SOURCES) != _ORIGINAL_LIMITS
        or _INPUT_FIELDS is not _ORIGINAL_INPUT_NAMES
        or _OUTPUT_FIELDS is not _ORIGINAL_OUTPUT_NAMES
        or _DENIALS is not _ORIGINAL_DENIAL_NAMES
        or any(
            tuple(vars(cls).get(name) for name in _CARRIER_HOOK_NAMES)
            != original
            for cls, original in _ORIGINAL_HOOKS.items()
        )
        or any(
            vars(_INPUT).get(name) is not original
            for name, original in zip(_INPUT_FIELDS, _ORIGINAL_INPUT, strict=True)
        )
        or any(
            vars(_OUTPUT).get(name) is not original
            for name, original in zip(_OUTPUT_FIELDS, _ORIGINAL_OUTPUT, strict=True)
        )
        or any(
            vars(_OUTPUT).get(name) is not original
            for name, original in zip(_DENIALS, _ORIGINAL_DENIALS, strict=True)
        )
    ):
        raise DisconnectedImprovementRejected("proposal-only protocol changed")


def _name(value: object) -> str:
    if type(value) is not str or not 1 <= len(value) <= 64 or _NAME.fullmatch(value) is None:
        raise DisconnectedImprovementRejected("invalid proposal category/component")
    return value


def _sha(value: object) -> str:
    if type(value) is not str or len(value) != 64 or _SHA.fullmatch(value) is None:
        raise DisconnectedImprovementRejected("invalid content-free source digest")
    return value


_ORIGINAL_NAME_HELPER = _name
_ORIGINAL_SHA_HELPER = _sha


def draft_disconnected_improvements(
    proposals: tuple[ImprovementProposalInput, ...],
) -> tuple[ImprovementProposalDraft, ...]:
    """Deterministic scope-isolated, input-order-independent proposal dedup."""
    _protocol()
    if (
        type(proposals) is not tuple
        or not 1 <= len(proposals) <= _MAX_PROPOSALS
        or any(type(value) is not _INPUT for value in proposals)
    ):
        raise DisconnectedImprovementRejected("invalid bounded proposal inputs")
    carrier_epoch = tuple(
        (input_value, tuple(getattr(input_value, name) for name in _INPUT_FIELDS))
        for input_value in proposals
    )

    def stable() -> None:
        _protocol()
        if len(carrier_epoch) != len(proposals) or any(
            input_value is not original
            or any(
                getattr(input_value, name) is not value
                for name, value in zip(_INPUT_FIELDS, fields, strict=True)
            )
            for input_value, (original, fields) in zip(
                proposals, carrier_epoch, strict=True,
            )
        ):
            raise DisconnectedImprovementRejected("proposal inputs changed in review")

    counts: dict[str, tuple[int, int]] = {}
    for _, fields in carrier_epoch:
        stable()
        issue, component, kind, revision, owner, namespace, sources = fields
        _name(issue)
        _name(component)
        if type(kind) is not str or kind not in _KINDS:
            raise DisconnectedImprovementRejected("unsupported proposal change class")
        if type(revision) is not int or not 1 <= revision <= 2**31 - 1:
            raise DisconnectedImprovementRejected("invalid proposal policy revision")
        _sha(owner)
        _sha(namespace)
        if (
            type(sources) is not tuple
            or not 1 <= len(sources) <= _MAX_SOURCES
        ):
            raise DisconnectedImprovementRejected("invalid bounded source references")
        normalized = tuple(sorted({_sha(item) for item in sources}))
        if len(normalized) != len(sources):
            raise DisconnectedImprovementRejected("duplicate source evidence")
        payload = (1, issue, component, kind, revision, owner, namespace, normalized)
        encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
        stable()
        digest = hashlib.sha256(_DOMAIN + encoded.encode("ascii")).hexdigest()
        stable()
        key = "proposal_" + digest
        seen = counts.get(key)
        counts[key] = (
            len(normalized), (seen[1] + 1 if seen is not None else 1),
        )
    stable()
    result = tuple(
        _OUTPUT(key, evidence_count, occurrences)
        for key, (evidence_count, occurrences) in sorted(counts.items())
    )
    stable()
    for draft in result:
        if (
            type(draft) is not _OUTPUT
            or type(draft.proposal_id) is not str
            or not draft.proposal_id.startswith("proposal_")
            or type(draft.evidence_count) is not int
            or type(draft.occurrences) is not int
        ):
            raise DisconnectedImprovementRejected("proposal result carrier changed")
        for denial in _DENIALS:
            stable()
            if getattr(draft, denial) is not False:
                raise DisconnectedImprovementRejected("proposal gained authority")
    stable()
    return result

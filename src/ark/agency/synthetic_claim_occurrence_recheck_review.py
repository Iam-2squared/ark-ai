"""Read-only re-attestation of disconnected claim↔occurrence sidecar rows.

This is *local, unauthenticated* evidence. A matching persisted association
does not prove consent, an issuer, a trusted clock, an external WRITE outcome,
or permission to dispatch/replay. Cross-database reads are not atomic.
"""

from __future__ import annotations

import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .durable_occurrence_review import _validate as _validate_reservations
from .synthetic_claim_occurrence_link_review import (
    SyntheticClaimLinkRejected,
    SyntheticClaimLinkWitness,
    SyntheticClaimOccurrenceLinkStore,
    _check_retained,
    _replay,
    _retained_shape,
)
from .synthetic_occurrence_continuity_review import (
    SyntheticLedgerWitness,
    assert_synthetic_history_continues,
    read_synthetic_ledger_witness,
)

_APPROVAL = re.compile(r"approval_[0-9a-f]{64}\Z")
_OCCURRENCE = re.compile(r"occ_[0-9a-f]{64}\Z")
_ROWS = """SELECT approval_id,occurrence_id,registry_revision,
                  bound_action_id,request_id,linked_at_ms
           FROM synthetic_claim_occurrence_links ORDER BY seq"""
_SOURCE_ROW = """SELECT occurrence_id,registry_revision,bound_action_id,
                        request_id,reserved_at_ms
                 FROM synthetic_occurrence_reservations WHERE occurrence_id=?"""


class SyntheticClaimSourceRejected(SyntheticClaimLinkRejected):
    """Local source and claimed association no longer agree."""


@dataclass(frozen=True, slots=True)
class SyntheticClaimSourceReview:
    link_event_count: int
    link_tail_hash: str
    reservation_row_count: int
    reservation_digest: str
    expected_pair_found: bool

    @property
    def human_consent_verified(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_outcome_known(self) -> bool:
        return False


def _open_ro(path: Path) -> sqlite3.Connection:
    # URI mode=ro refuses a missing DB, including paths containing #, ? or %.
    return sqlite3.connect(
        path.resolve().as_uri() + "?mode=ro",
        uri=True, isolation_level=None, timeout=10,
    )


def review_synthetic_claim_occurrence_sources(
    links: SyntheticClaimOccurrenceLinkStore,
    reservation_path: Path,
    *,
    retained_links: SyntheticClaimLinkWitness | None = None,
    retained_reservations: SyntheticLedgerWitness | None = None,
    expected_pair: tuple[str, str] | None = None,
) -> SyntheticClaimSourceReview:
    """Recheck every saved link against a real source row without execution.

    A before/after ledger comparison detects observed drift, but it is not a
    global atomic SQLite snapshot and cannot close races after final review.
    Independently retained witnesses are optional, NOT created here.
    """
    if (
        type(links) is not SyntheticClaimOccurrenceLinkStore
        or not isinstance(reservation_path, Path)
        or expected_pair is not None
        and (
            type(expected_pair) is not tuple
            or len(expected_pair) != 2
            or type(expected_pair[0]) is not str
            or type(expected_pair[1]) is not str
            or not _APPROVAL.fullmatch(expected_pair[0])
            or not _OCCURRENCE.fullmatch(expected_pair[1])
        )
    ):
        raise SyntheticClaimSourceRejected("exact synthetic source review inputs required")
    _retained_shape(retained_links)
    if retained_reservations is not None:
        if type(retained_reservations) is not SyntheticLedgerWitness:
            raise SyntheticClaimSourceRejected("exact retained reservation witness required")
        retained_reservations.assert_integrity()

    # A reflected change to a frozen retained witness can otherwise select a
    # different *valid* earlier history during later reads. Preserve scalar
    # values before callbacks and pin the link-store source identity.
    link_path_epoch = links.path
    retained_link_epoch = (
        None if retained_links is None else (
            retained_links.event_count, retained_links.tail_hash,
            retained_links.last_linked_at_ms,
        )
    )
    retained_source_epoch = (
        None if retained_reservations is None else (
            retained_reservations.row_hashes, retained_reservations.digest,
        )
    )
    before_links = links.read_witness(retained=retained_links)
    before_link_epoch = (
        before_links.event_count, before_links.tail_hash,
        before_links.last_linked_at_ms,
    )
    before_source = read_synthetic_ledger_witness(reservation_path)
    before_source_epoch = (before_source.row_hashes, before_source.digest)
    if links.path is not link_path_epoch:
        raise SyntheticClaimSourceRejected("claim link source changed during review")
    if retained_reservations is not None:
        assert_synthetic_history_continues(retained_reservations, before_source)

    with closing(_open_ro(link_path_epoch)) as sidecar:
        with closing(_open_ro(reservation_path)) as source:
            sidecar.execute("BEGIN")
            source.execute("BEGIN")
            try:
                prefixes = _replay(sidecar)
                _check_retained(prefixes, retained_links)
                _validate_reservations(source)
                rows = sidecar.execute(_ROWS).fetchall()
                found = False
                for approval, occurrence, revision, action, request, at_ms in rows:
                    saved = source.execute(_SOURCE_ROW, (occurrence,)).fetchone()
                    if (
                        saved is None
                        or saved[:4] != (occurrence, revision, action, request)
                        or saved[4] > at_ms
                    ):
                        raise SyntheticClaimSourceRejected(
                            "linked reservation missing or changed in source"
                        )
                    if expected_pair == (approval, occurrence):
                        found = True
                if expected_pair is not None and not found:
                    raise SyntheticClaimSourceRejected(
                        "expected claim and occurrence association is missing"
                    )
                if prefixes[-1] != before_links:
                    raise SyntheticClaimSourceRejected(
                        "linked history changed before pinned source read"
                    )
                source.commit()
                sidecar.commit()
            except BaseException:
                source.rollback()
                sidecar.rollback()
                raise

    after_source = read_synthetic_ledger_witness(reservation_path)
    after_links = links.read_witness(retained=before_links)
    if (
        links.path is not link_path_epoch
        or before_link_epoch != (
            before_links.event_count, before_links.tail_hash,
            before_links.last_linked_at_ms,
        )
        or before_source_epoch != (
            before_source.row_hashes, before_source.digest,
        )
        or retained_link_epoch != (
            None if retained_links is None else (
                retained_links.event_count, retained_links.tail_hash,
                retained_links.last_linked_at_ms,
            )
        )
        or retained_source_epoch != (
            None if retained_reservations is None else (
                retained_reservations.row_hashes, retained_reservations.digest,
            )
        )
        or after_source != before_source or after_links != before_links
    ):
        raise SyntheticClaimSourceRejected(
            "linked history, retained witness or source changed during review"
        )
    return SyntheticClaimSourceReview(
        before_links.event_count, before_links.tail_hash,
        len(before_source.row_hashes), before_source.digest, found,
    )

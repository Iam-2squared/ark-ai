"""Disconnected privacy-scoped observation-window review (no media capture).

This isolated fixture does not validate a source's authenticity, grant consent,
trigger a notification, or authorize execution. A witness is only a digest of
validated observation metadata, not external attestation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from .observations import ObservationEnvelope


@dataclass(frozen=True, slots=True)
class ObservationWindowReview:
    privacy_scope: str
    observed_at_ms: int
    max_age_ms: int
    envelopes: tuple[ObservationEnvelope, ...]
    _epoch: tuple[tuple[ObservationEnvelope, str], ...] = field(
        init=False, repr=False, compare=False
    )
    _header_epoch: tuple[str, int, int] = field(
        init=False, repr=False, compare=False
    )
    _carrier_epoch: tuple[ObservationEnvelope, ...] = field(
        init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        self._validate_header()
        if type(self.envelopes) is not tuple or not 1 <= len(self.envelopes) <= 256:
            raise ValueError("envelopes must be an exact nonempty tuple (max 256)")
        # Keep the original input tuple, not merely its member objects. A
        # value-equal replacement during hydration is a different local
        # observation epoch even if the same envelopes are reused.
        carrier = self.envelopes
        epoch: list[tuple[ObservationEnvelope, str]] = []
        identities: set[str] = set()
        for envelope in carrier:
            identity = self._check_envelope(envelope)
            if identity in identities:
                raise ValueError("duplicate observation identity in window")
            identities.add(identity)
            epoch.append((envelope, identity))
        object.__setattr__(self, "_epoch", tuple(epoch))
        object.__setattr__(
            self, "_header_epoch",
            (self.privacy_scope, self.observed_at_ms, self.max_age_ms),
        )
        object.__setattr__(self, "_carrier_epoch", carrier)
        self.assert_consistent()

    def _validate_header(self) -> None:
        if type(self.privacy_scope) is not str or not self.privacy_scope.strip():
            raise ValueError("privacy_scope must be a nonempty exact string")
        if (
            type(self.observed_at_ms) is not int
            or not 0 <= self.observed_at_ms <= 2**63 - 1
        ):
            raise ValueError("observed_at_ms must be a nonnegative exact integer in SQLite range")
        if (
            type(self.max_age_ms) is not int
            or not 0 <= self.max_age_ms <= 2**63 - 1
        ):
            raise ValueError("max_age_ms must be a nonnegative exact integer in SQLite range")

    def _check_envelope(self, envelope: ObservationEnvelope) -> str:
        if type(envelope) is not ObservationEnvelope:
            raise TypeError("window requires exact ObservationEnvelope values")
        # Reconstruct validation rather than trusting dataclass frozen fields;
        # reflected field mutation can bypass frozen's ordinary assignment gate.
        checked = ObservationEnvelope(
            envelope.kind,
            envelope.source_id,
            envelope.adapter_id,
            envelope.privacy_scope,
            envelope.ingested_at_ms,
            envelope.content_sha256,
            envelope.parent_sha256,
            envelope.schema_version,
        )
        if checked.privacy_scope != self.privacy_scope:
            raise ValueError("observation scope does not match window scope")
        if checked.ingested_at_ms > self.observed_at_ms:
            raise ValueError("future observation cannot enter reviewed window")
        if self.observed_at_ms - checked.ingested_at_ms > self.max_age_ms:
            raise ValueError("observation exceeds window age budget")
        return checked.observation_id

    def assert_consistent(self) -> None:
        """Reject stale or reflected input changes before reuse after review."""
        self._validate_header()
        if (
            self.privacy_scope, self.observed_at_ms, self.max_age_ms
        ) != self._header_epoch:
            raise ValueError("observation window header changed after construction")
        if type(self.envelopes) is not tuple or len(self.envelopes) != len(self._epoch):
            raise ValueError("observation window tuple changed after construction")
        if self.envelopes is not self._carrier_epoch:
            # A substituted member preserves the original identity diagnostic;
            # a copied tuple holding the SAME members has its own drift code.
            if any(
                supplied is not original
                for supplied, (original, _identity) in zip(
                    self.envelopes, self._epoch, strict=True,
                )
            ):
                raise ValueError("observation identity changed after construction")
            raise ValueError("observation window tuple changed after construction")
        for supplied, (original, identity) in zip(
            self.envelopes, self._epoch, strict=True
        ):
            if supplied is not original or self._check_envelope(supplied) != identity:
                raise ValueError("observation identity changed after construction")

    def assert_fresh_at(self, now_ms: int) -> None:
        """Re-check cached synthetic observations against an explicit later time.

        Caller-provided time is not trusted-clock evidence, consent or capture
        authority. This opt-in check never updates the original window witness.
        """
        if type(now_ms) is not int or not 0 <= now_ms <= 2**63 - 1:
            raise ValueError("retention check time must be an exact SQLite-range integer")
        self.assert_consistent()
        if now_ms < self.observed_at_ms:
            raise ValueError("observation retention clock moved backwards")
        if any(
            now_ms - envelope.ingested_at_ms > self.max_age_ms
            for envelope in self.envelopes
        ):
            raise ValueError("observation window no longer meets age budget")
        self.assert_consistent()

    @property
    def witness(self) -> str:
        self.assert_consistent()
        payload = {
            "schema_version": 1,
            "privacy_scope": self.privacy_scope,
            "observed_at_ms": self.observed_at_ms,
            "max_age_ms": self.max_age_ms,
            "observation_ids": [identity for _, identity in self._epoch],
        }
        canonical = json.dumps(
            payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
        # Serialization and hashing are reentrant callback boundaries in
        # isolated fault fixtures. Never return an old observation witness if
        # an input was rewritten after the initial consistency check.
        self.assert_consistent()
        digest = "window_" + hashlib.sha256(canonical).hexdigest()
        self.assert_consistent()
        return digest

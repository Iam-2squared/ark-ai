"""Disconnected wake-cue parsing on explicitly supplied untrusted transcript text.

This is NOT an acoustic wake-word detector, speaker authentication, consent,
command authorization, or tool dispatch. A cue match is only a text pattern;
even an apparently valid command must never cause an external action here.
The optional command_text is sensitive and must not be logged or transmitted.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_CUE = re.compile(r"cue_[0-9a-f]{8}\Z")
_DOMAIN = b"ARK-disconnected-transcript-cues-v1\0"
_SEPARATORS = " ,、:;.!?！？；："
_MAX_CUES = 8
_MAX_INPUT = 4096
_MAX_PHRASE = 96


class OfflineCueRejected(ValueError):
    """A transcript or local wake-cue set fails bounded exact review."""


@dataclass(frozen=True, slots=True)
class OfflineWakeCue:
    cue_id: str
    phrase: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class OfflineCueRequest:
    owner_sha256: str
    privacy_sha256: str
    transcript_sha256: str
    transcript_text: str = field(repr=False)
    cues: tuple[OfflineWakeCue, ...] = ()
    expected_cue_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OfflineCueResult:
    matched_cue_id: str | None
    command_sha256: str | None
    command_text: str | None = field(repr=False)
    cue_inventory_sha256: str = ""
    result_sha256: str = ""

    @property
    def speaker_authenticated(self) -> bool:
        return False

    @property
    def microphone_provenance_verified(self) -> bool:
        return False

    @property
    def action_authorized(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False


_RESULT_TYPE = OfflineCueResult


def _sha(value: object) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def _text(value: object, maximum: int) -> str:
    if type(value) is not str or not value:
        raise OfflineCueRejected("nonempty exact transcript text required")
    if any(unicodedata.category(char).startswith("C") for char in value):
        raise OfflineCueRejected("transcript contains control or invisible Unicode")
    try:
        raw = value.encode("utf-8", "strict")
        normalized = unicodedata.normalize("NFKC", value).casefold()
        norm_raw = normalized.encode("utf-8", "strict")
    except UnicodeError as exc:
        raise OfflineCueRejected("invalid transcript Unicode") from exc
    if len(raw) > maximum or len(norm_raw) > maximum:
        raise OfflineCueRejected("text byte budget exceeded")
    return normalized


def _digest(label: str, value: object) -> str:
    canonical = json.dumps(
        value, sort_keys=True, ensure_ascii=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(_DOMAIN + label.encode("ascii") + b"\0" + canonical).hexdigest()


def review_offline_transcript_cues(request: OfflineCueRequest) -> OfflineCueResult:
    """Detect one unambiguous exact-prefix cue; return only detached preview.

    After a phrase, a boundary separator must precede any command. Japanese
    phrases are supported through NFKC but concatenated text is *not* treated
    as an instruction; cue ambiguity is rejected, not guessed. Cue declarations
    and source digest are caller assertions, not proof of authentic speech.
    """
    if type(request) is not OfflineCueRequest:
        raise OfflineCueRejected("exact cue request required")
    original = (
        request.owner_sha256, request.privacy_sha256,
        request.transcript_sha256, request.transcript_text,
        request.cues, request.expected_cue_ids,
    )
    if (
        type(request.cues) is not tuple or not 1 <= len(request.cues) <= _MAX_CUES
        or type(request.expected_cue_ids) is not tuple
        or len(request.expected_cue_ids) != len(request.cues)
    ):
        raise OfflineCueRejected("cue membership budget exceeded")
    rows = tuple(request.cues)
    fields = tuple((row.cue_id, row.phrase) if type(row) is OfflineWakeCue else None
                   for row in rows)

    def epoch() -> None:
        current = (
            request.owner_sha256, request.privacy_sha256,
            request.transcript_sha256, request.transcript_text,
            request.cues, request.expected_cue_ids,
        )
        if (
            any(a is not b for a, b in zip(current, original, strict=True))
            or len(request.cues) != len(rows)
            or any(row is not request.cues[index] for index, row in enumerate(rows))
            or any(
                type(row) is not OfflineWakeCue
                or row.cue_id is not saved[0]
                or row.phrase is not saved[1]
                for row, saved in zip(rows, fields, strict=True)
            )
        ):
            raise OfflineCueRejected("cue carriers mutated during review")

    epoch()
    owner, privacy, transcript_sha, source, _, expected = original
    if not all(_sha(x) for x in (owner, privacy, transcript_sha)):
        raise OfflineCueRejected("invalid owner/privacy/transcript checksum")
    normalized = _text(source, _MAX_INPUT)
    if hashlib.sha256(source.encode("utf-8")).hexdigest() != transcript_sha:
        raise OfflineCueRejected("transcript checksum mismatch")
    epoch()
    ids: set[str] = set()
    normalized_phrases: set[str] = set()
    matches: list[tuple[str, str]] = []
    manifest: list[tuple[str, str]] = []
    for entry in fields:
        epoch()
        if entry is None:
            raise OfflineCueRejected("invalid cue carrier")
        cue_id, phrase = entry
        if type(cue_id) is not str or _CUE.fullmatch(cue_id) is None or cue_id in ids:
            raise OfflineCueRejected("duplicate or malformed cue ID")
        checked_phrase = _text(phrase, _MAX_PHRASE)
        if (
            phrase != phrase.strip() or checked_phrase != checked_phrase.strip()
            or checked_phrase.strip(_SEPARATORS) != checked_phrase
            or checked_phrase in normalized_phrases
        ):
            raise OfflineCueRejected("ambiguous, padded or duplicate normalized cue")
        ids.add(cue_id)
        normalized_phrases.add(checked_phrase)
        manifest.append((cue_id, checked_phrase))
        if normalized == checked_phrase:
            matches.append((cue_id, ""))
        elif normalized.startswith(checked_phrase):
            next_char = normalized[len(checked_phrase):len(checked_phrase) + 1]
            if next_char in _SEPARATORS and next_char:
                remainder = normalized[len(checked_phrase):].lstrip(_SEPARATORS)
                matches.append((cue_id, remainder))
        epoch()
    if (
        any(type(x) is not str or _CUE.fullmatch(x) is None for x in expected)
        or tuple(sorted(ids)) != expected
    ):
        raise OfflineCueRejected("complete ordered cue membership mismatch")
    if len(matches) > 1:
        raise OfflineCueRejected("multiple overlapping wake cues are ambiguous")
    match_id, command = matches[0] if matches else (None, None)
    if command is not None and not command:
        command = None
    command_sha = hashlib.sha256(command.encode("utf-8")).hexdigest() if command else None
    inventory_sha = _digest("inventory", (owner, privacy, sorted(manifest)))
    result_sha = _digest(
        "result", (inventory_sha, transcript_sha, match_id, command_sha),
    )
    epoch()
    result = OfflineCueResult(match_id, command_sha, command, inventory_sha, result_sha)
    expected_result = (match_id, command_sha, command, inventory_sha, result_sha)

    def result_epoch() -> None:
        if (
            type(result) is not _RESULT_TYPE
            or any(now is not old for now, old in zip(
                (
                    result.matched_cue_id, result.command_sha256,
                    result.command_text, result.cue_inventory_sha256,
                    result.result_sha256,
                ),
                expected_result, strict=True,
            ))
        ):
            raise OfflineCueRejected("cue result carrier changed")

    epoch()
    result_epoch()
    # A transcript cue is not speaker verification, recorded consent, or an
    # execution capability. Denial-only getters are checked *before* output;
    # they are callback boundaries, so pin the result again afterwards.
    if (
        result.speaker_authenticated is not False
        or result.microphone_provenance_verified is not False
        or result.action_authorized is not False
        or result.consent_verified is not False
    ):
        raise OfflineCueRejected("cue result claims unauthenticated authority")
    epoch()
    result_epoch()
    return result

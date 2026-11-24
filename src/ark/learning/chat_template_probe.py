"""Free-only binding between a local tokenizer and its rendered probe artifact.

The probe uses fixed synthetic messages and local tokenizer code only. It does
not download models, load weights, use an accelerator, approve compute, or
authenticate a Hub revision. File checks are best-effort local custody checks,
not an atomic hostile-writer-safe descriptor seal.
"""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path

from .execution import canonical_json, sha256_bytes

_MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"
_MAX_TEMPLATE_BYTES = 65_536
_MAX_RENDERED_BYTES = 65_536
_MAX_PROBE_FILE_BYTES = 262_144
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")

_USER_TEXT = "ARK V3 chat-template identity probe"
_ASSISTANT_TEXT = "Probe response; no training data."
_CASES = (
    (
        "generation_prompt_v1",
        ({"role": "user", "content": _USER_TEXT},),
        True,
    ),
    (
        "assistant_turn_v1",
        (
            {"role": "user", "content": _USER_TEXT},
            {"role": "assistant", "content": _ASSISTANT_TEXT},
        ),
        False,
    ),
)


class ChatTemplateProbeRejected(ValueError):
    """A runtime tokenizer does not match the retained rendered probe."""


def _bounded_utf8(value: object, label: str, limit: int) -> bytes:
    if type(value) is not str or len(value) > limit:
        raise ChatTemplateProbeRejected(f"{label} must be bounded exact text")
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ChatTemplateProbeRejected(f"{label} is not valid UTF-8") from exc
    if len(encoded) > limit:
        raise ChatTemplateProbeRejected(f"{label} byte budget exceeded")
    return encoded


def build_chat_template_probe(tokenizer: object) -> dict:
    """Render fixed user/assistant cases with the supplied local tokenizer."""
    template = getattr(tokenizer, "chat_template", None)
    template_bytes = _bounded_utf8(
        template, "tokenizer chat_template", _MAX_TEMPLATE_BYTES,
    )
    render = getattr(tokenizer, "apply_chat_template", None)
    if not callable(render):
        raise ChatTemplateProbeRejected("tokenizer apply_chat_template is required")

    cases = []
    for case_id, source_messages, generation_prompt in _CASES:
        messages = [dict(message) for message in source_messages]
        before = canonical_json(messages)
        rendered = render(
            messages,
            tokenize=False,
            add_generation_prompt=generation_prompt,
        )
        if canonical_json(messages) != before:
            raise ChatTemplateProbeRejected("tokenizer mutated probe messages")
        rendered_bytes = _bounded_utf8(
            rendered, f"{case_id} rendering", _MAX_RENDERED_BYTES,
        )
        cases.append({
            "case_id": case_id,
            "messages": messages,
            "add_generation_prompt": generation_prompt,
            "rendered": rendered,
            "rendered_sha256": sha256_bytes(rendered_bytes),
        })

    return {
        "schema_version": 1,
        "model_id": _MODEL_ID,
        "tokenizer_chat_template_sha256": sha256_bytes(template_bytes),
        "cases": cases,
    }


def _stat_epoch(info: os.stat_result) -> tuple[int, ...]:
    return (
        info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
        info.st_size, info.st_mtime_ns, info.st_ctime_ns,
    )


def _read_probe_file(path: Path) -> bytes:
    """Read one bounded regular file and reject observed path/handle drift."""
    path = Path(path)
    if (
        ".." in path.parts
        or len(str(path)) > 4096
        or path.is_symlink()
        or not path.is_file()
        or any(parent.is_symlink() for parent in path.parents)
    ):
        raise ChatTemplateProbeRejected("chat-template probe must be a regular non-aliased file")
    try:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ChatTemplateProbeRejected("chat-template probe must have one regular-file link")
        if not 1 <= before.st_size <= _MAX_PROBE_FILE_BYTES:
            raise ChatTemplateProbeRejected("chat-template probe file budget exceeded")
        with path.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_nlink != 1
                or not os.path.samestat(before, opened)
                or _stat_epoch(opened) != _stat_epoch(before)
            ):
                raise ChatTemplateProbeRejected("chat-template probe changed before read")
            payload = handle.read(_MAX_PROBE_FILE_BYTES + 1)
            after = os.fstat(handle.fileno())
        if (
            len(payload) > _MAX_PROBE_FILE_BYTES
            or len(payload) != opened.st_size
            or _stat_epoch(after) != _stat_epoch(opened)
            or _stat_epoch(path.lstat()) != _stat_epoch(before)
            or path.is_symlink()
        ):
            raise ChatTemplateProbeRejected("chat-template probe changed during read")
        return payload
    except OSError as exc:
        raise ChatTemplateProbeRejected("chat-template probe became unavailable") from exc


def verify_chat_template_probe(
    tokenizer: object,
    probe_path: Path,
    expected_sha256: str,
) -> str:
    """Require the actual runtime renderer to reproduce the exact local probe."""
    if (
        type(expected_sha256) is not str
        or _SHA256.fullmatch(expected_sha256) is None
    ):
        raise ChatTemplateProbeRejected("frozen chat-template probe SHA-256 is invalid")
    retained = _read_probe_file(Path(probe_path))
    observed_sha256 = sha256_bytes(retained)
    if observed_sha256 != expected_sha256:
        raise ChatTemplateProbeRejected("chat-template probe file digest mismatch")
    rendered = canonical_json(build_chat_template_probe(tokenizer))
    if rendered != retained:
        raise ChatTemplateProbeRejected(
            "runtime tokenizer rendering differs from frozen chat-template probe"
        )
    if sha256_bytes(rendered) != expected_sha256:
        raise ChatTemplateProbeRejected("runtime chat-template probe digest mismatch")
    return expected_sha256

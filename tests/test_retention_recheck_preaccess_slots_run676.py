"""Retention recheck refuses executable result slots before personal SQLite access.

No physical erasure or genuine consent occurs. The private projection is a
deliberately forbidden spy after valid fixture setup.
"""

from __future__ import annotations

import pytest

import ark.personal_context_retention_recheck_review as retention
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_retention_review import review_synthetic_retention_inventory
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def _fixture(tmp_path):
    memory = SQLiteMemoryStore(tmp_path / "context.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("owner", "private")
    memory.put(MemoryWrite(
        scope, "source", "SECRET FIXTURE CONTENT", expires_at_ms=101,
    ))
    revocations = SyntheticContextRevocationLedger(tmp_path / "revocations.sqlite")
    cached = review_synthetic_retention_inventory(
        memory, scope, revocations, now_ms=100,
    )
    return memory, scope, revocations, cached


@pytest.mark.parametrize(
    "field",
    (*retention._RESULT_FIELDS, "__getattribute__", "__getattr__"),
)
def test_rebound_result_field_or_lookup_hook_denied_before_private_read(
    tmp_path, monkeypatch, field,
):
    state = _fixture(tmp_path)
    attempted = []

    def forbidden_projection(*_args, **_kwargs):
        attempted.append("private SQLite projection")
        raise AssertionError("private retention data was read after hook substitution")

    def hostile(*_args, **_kwargs):
        attempted.append("malicious result accessor")
        raise AssertionError("replaced retention result accessor was invoked")

    with monkeypatch.context() as patch:
        patch.setattr(retention, "review_synthetic_retention_inventory", forbidden_projection)
        patch.setattr(
            retention.SyntheticRetentionRecheck,
            field, hostile if field.startswith("__") else property(hostile),
            raising=False,
        )
        with pytest.raises(
            retention.SyntheticRetentionRecheckRejected,
            match="original denial implementation",
        ):
            retention.review_synthetic_retention_recheck(
                *state, now_ms=101, max_age_ms=10,
            )
    assert attempted == []


def test_original_result_fields_still_return_a_non_authorizing_review(tmp_path):
    result = retention.review_synthetic_retention_recheck(
        *_fixture(tmp_path), now_ms=101, max_age_ms=10,
    )
    assert len(result.expired_memory_ids) == 1
    assert result.deletion_authorized is False
    assert result.erasure_completed is False
    assert result.context_use_authorized is False
    assert result.external_disclosure_authorized is False
    assert "SECRET FIXTURE CONTENT" not in repr(result)

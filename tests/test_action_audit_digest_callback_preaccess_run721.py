"""Audit argument digest callbacks remain fixed before SQLite or private data.

No real tool dispatch, trusted clock, approval or authenticated action occurs.
"""

from __future__ import annotations

import pytest

from ark.agency import audit as audit_module
from ark.agency import contracts as contracts_module

DEPENDENCIES = (
    "sha256",
    "canonical_audit",
    "canonical_call",
    "freeze_call",
    "json_dumps",
)


def _fixture(tmp_path):
    audit = audit_module.SQLiteActionAudit(
        tmp_path / "audit.db", clock_ms=lambda: 100,
    )
    call = contracts_module.ToolCall(
        "fixture.read", "fixture.read", "synthetic:scope",
        {"private": "fixture-only sensitive argument"},
    )
    return audit, call


def _replace(patch, key, rogue):
    if key == "sha256":
        patch.setattr(audit_module.hashlib, "sha256", rogue)
    elif key == "canonical_audit":
        patch.setattr(audit_module, "_canonical_json", rogue)
    elif key == "canonical_call":
        patch.setattr(contracts_module, "_canonical_json", rogue)
    elif key == "freeze_call":
        patch.setattr(contracts_module, "_freeze_json", rogue)
    else:
        patch.setattr(contracts_module.json, "dumps", rogue)


@pytest.mark.parametrize("dependency", DEPENDENCIES)
@pytest.mark.parametrize("operation", ("append", "events"))
def test_original_digest_dependency_checked_before_private_data_or_sqlite(
    tmp_path, monkeypatch, dependency, operation,
):
    audit, call = _fixture(tmp_path)
    if operation == "events":
        audit.append(call, outcome="synthetic")
    invoked = []

    def rogue(*_args, **_kwargs):
        invoked.append("callback")
        pytest.fail("unreviewed digest callback was invoked")

    def no_sqlite(*_args, **_kwargs):
        pytest.fail("digest denial must precede SQLite access")

    with monkeypatch.context() as patch:
        _replace(patch, dependency, rogue)
        patch.setattr(
            audit,
            "_connect" if operation == "append" else "_connect_readonly",
            no_sqlite,
        )
        with pytest.raises(
            contracts_module.ActionAuditSchemaError, match="digest callback",
        ):
            if operation == "append":
                audit.append(call, outcome="synthetic")
            else:
                audit.events()
    assert invoked == []
    assert len(audit.events()) == (0 if operation == "append" else 1)


@pytest.mark.parametrize("dependency", ("sha256", "json_dumps"))
def test_clock_reentry_cannot_redirect_argument_digest_before_commit(
    tmp_path, monkeypatch, dependency,
):
    audit, call = _fixture(tmp_path)
    invoked = []

    def rogue(*_args, **_kwargs):
        invoked.append("callback")
        pytest.fail("unreviewed callback must not inspect private arguments")

    with monkeypatch.context() as patch:
        def clock():
            _replace(patch, dependency, rogue)
            return 100

        patch.setattr(audit, "_clock_ms", clock)
        with pytest.raises(
            contracts_module.ActionAuditSchemaError, match="digest callback",
        ):
            audit.append(call, outcome="synthetic")
    assert invoked == []
    assert audit.events() == []

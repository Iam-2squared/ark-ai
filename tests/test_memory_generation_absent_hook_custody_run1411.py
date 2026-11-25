"""Run1411: Memory generation CAS distinguishes absent class hooks from None."""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_fenced_cas as cas


def _case(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "generation-absent-hook.sqlite3",
        clock_ms=lambda: 1000,
    )
    scope = MemoryScope("synthetic-owner", "private")
    store.put(MemoryWrite(scope, "fixture", "original"), expected_revision=0)
    retained = cas.observe_memory_generation_for_cas(store, scope, "fixture")
    proposed = MemoryWrite(scope, "fixture", "proposed")
    return store, scope, retained, proposed


def _forbid_sqlite(*_args, **_kwargs):
    raise AssertionError("SQLite opened before generation class-guard denial")


@pytest.mark.parametrize(
    ("component", "hook"),
    [
        ("token", "__new__"),
        ("token", "__getattribute__"),
        ("token", "__getattr__"),
        ("scope", "__new__"),
        ("scope", "__getattribute__"),
        ("scope", "__getattr__"),
        ("write", "__new__"),
        ("write", "__getattribute__"),
        ("write", "__getattr__"),
    ],
)
@pytest.mark.parametrize("replacement_kind", ["explicit-none", "sentinel-installed"])
def test_absent_generation_class_hook_requires_namespace_absence(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    component: str,
    hook: str,
    replacement_kind: str,
) -> None:
    store, scope, retained, proposed = _case(tmp_path)
    component_types = {
        "token": cas.MemoryGenerationCASToken,
        "scope": MemoryScope,
        "write": MemoryWrite,
    }
    replacement = (
        None
        if replacement_kind == "explicit-none"
        else cas._ABSENT_CLASS_HOOK
    )
    expected = (
        "generation token or denial epoch changed"
        if component == "token"
        else "generation input carrier descriptor changed"
    )

    with monkeypatch.context() as patch:
        patch.setattr(
            component_types[component], hook, replacement, raising=False,
        )
        patch.setattr(store, "_connect", _forbid_sqlite)
        with pytest.raises(cas.MemoryGenerationCASRejected, match=expected):
            cas.generation_fenced_memory_update(
                store, proposed, retained=retained,
            )

    memory_id = object.__getattribute__(retained, "memory_id")
    assert store.get(memory_id, scope).content == "original"
    assert len(store.events(scope)) == 1


def test_absence_sentinel_rebinding_is_denied_before_sqlite(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, scope, retained, proposed = _case(tmp_path)
    with monkeypatch.context() as patch:
        patch.setattr(cas, "_ABSENT_CLASS_HOOK", object())
        patch.setattr(store, "_connect", _forbid_sqlite)
        with pytest.raises(
            cas.MemoryGenerationCASRejected,
            match="generation input carrier descriptor changed",
        ):
            cas.generation_fenced_memory_update(
                store, proposed, retained=retained,
            )

    memory_id = object.__getattribute__(retained, "memory_id")
    assert store.get(memory_id, scope).content == "original"
    assert len(store.events(scope)) == 1


def test_joint_token_hook_vector_replacement_is_denied_before_sqlite(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, scope, retained, proposed = _case(tmp_path)
    empty: tuple[object, ...] = ()
    with monkeypatch.context() as patch:
        patch.setattr(cas, "_TOKEN_HOOKS", empty)
        patch.setattr(cas, "_ORIGINAL_TOKEN_HOOKS", empty)
        patch.setattr(store, "_connect", _forbid_sqlite)
        with pytest.raises(
            cas.MemoryGenerationCASRejected,
            match="generation token or denial epoch changed",
        ):
            cas.generation_fenced_memory_update(
                store, proposed, retained=retained,
            )

    memory_id = object.__getattribute__(retained, "memory_id")
    assert store.get(memory_id, scope).content == "original"
    assert len(store.events(scope)) == 1


def test_joint_input_hook_vector_replacement_is_denied_before_sqlite(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, scope, retained, proposed = _case(tmp_path)
    empty: tuple[object, ...] = ()
    with monkeypatch.context() as patch:
        patch.setattr(cas, "_INPUT_HOOKS", empty)
        patch.setattr(cas, "_ORIGINAL_SCOPE_HOOKS", empty)
        patch.setattr(cas, "_ORIGINAL_WRITE_HOOKS", empty)
        patch.setattr(store, "_connect", _forbid_sqlite)
        with pytest.raises(
            cas.MemoryGenerationCASRejected,
            match="generation input carrier descriptor changed",
        ):
            cas.generation_fenced_memory_update(
                store, proposed, retained=retained,
            )

    memory_id = object.__getattribute__(retained, "memory_id")
    assert store.get(memory_id, scope).content == "original"
    assert len(store.events(scope)) == 1


def test_joint_token_type_alias_replacement_is_denied_before_sqlite(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, scope, retained, proposed = _case(tmp_path)
    replacement = type("ReplacementGenerationToken", (), {})
    with monkeypatch.context() as patch:
        patch.setattr(cas, "MemoryGenerationCASToken", replacement)
        patch.setattr(cas, "_TOKEN_TYPE", replacement)
        patch.setattr(store, "_connect", _forbid_sqlite)
        with pytest.raises(
            cas.MemoryGenerationCASRejected,
            match="generation token or denial epoch changed",
        ):
            cas.generation_fenced_memory_update(
                store, proposed, retained=retained,
            )

    memory_id = object.__getattribute__(retained, "memory_id")
    assert store.get(memory_id, scope).content == "original"
    assert len(store.events(scope)) == 1


def test_joint_input_type_alias_replacement_is_denied_before_sqlite(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, scope, retained, proposed = _case(tmp_path)
    replacement = type("ReplacementMemoryScope", (), {})
    with monkeypatch.context() as patch:
        patch.setattr(cas, "MemoryScope", replacement)
        patch.setattr(cas, "_SCOPE_TYPE", replacement)
        patch.setattr(store, "_connect", _forbid_sqlite)
        with pytest.raises(
            cas.MemoryGenerationCASRejected,
            match="generation input carrier descriptor changed",
        ):
            cas.generation_fenced_memory_update(
                store, proposed, retained=retained,
            )

    memory_id = object.__getattribute__(retained, "memory_id")
    assert store.get(memory_id, scope).content == "original"
    assert len(store.events(scope)) == 1

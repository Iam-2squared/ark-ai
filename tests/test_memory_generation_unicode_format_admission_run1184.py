"""Run1184: complete Unicode format-control admission for Memory generation CAS."""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, generation_fenced_cas as generation


@pytest.mark.parametrize("control", ("\\u0600", "\\ufff9", "\\U000e0001"))
def test_generation_source_rejects_every_unicode_format_control(control: str) -> None:
    with pytest.raises(
        generation.MemoryGenerationCASRejected,
        match="generation source contains a formatting control",
    ):
        generation._require_bounded_source_id("private" + control + "source")


@pytest.mark.parametrize("control", ("\\u0600", "\\ufff9", "\\U000e0001"))
@pytest.mark.parametrize("field", ("owner_id", "namespace"))
def test_generation_scope_rejects_every_unicode_format_control(
    control: str, field: str,
) -> None:
    scope = MemoryScope("owner", "namespace")
    object.__setattr__(scope, field, "private" + control + "scope")

    with pytest.raises(
        generation.MemoryGenerationCASRejected,
        match="generation scope contains a formatting control",
    ):
        generation._require_bounded_scope(scope)


def test_generation_identity_admission_keeps_japanese_text_valid() -> None:
    scope = MemoryScope("所有者", "個人")

    generation._require_bounded_scope(scope)
    generation._require_bounded_source_id("資料")


@pytest.mark.parametrize("dependency", ("module", "category"))
def test_replaced_unicode_dependency_is_denied_before_callback(
    monkeypatch: pytest.MonkeyPatch, dependency: str,
) -> None:
    called: list[str] = []

    def forbidden(_character: str) -> str:
        called.append("category")
        raise AssertionError("unreviewed Unicode classifier received private identity")

    if dependency == "module":
        class PoisonedUnicodeDependency:
            @property
            def category(self) -> str:
                called.append("category")
                raise AssertionError("replaced Unicode module was inspected")

        monkeypatch.setattr(
            generation, "unicodedata", PoisonedUnicodeDependency(),
        )
    else:
        # Avoid mutating the process-global unicodedata module used by pytest.
        monkeypatch.setattr(
            generation, "_ORIGINAL_UNICODE_CATEGORY", forbidden,
        )

    with pytest.raises(
        generation.MemoryGenerationCASRejected,
        match="generation CAS Unicode policy changed",
    ):
        generation._require_bounded_source_id("private-source")

    assert called == []

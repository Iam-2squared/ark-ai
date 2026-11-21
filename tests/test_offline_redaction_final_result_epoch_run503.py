"""The last denial-only descriptor must not corrupt a returned private preview."""

import hashlib

import pytest

import ark.offline_context_redaction as mod


def _redact():
    text = "synthetic-private-data"
    return mod.preview_offline_redaction(
        text,
        owner_digest="a" * 64,
        scope_digest="b" * 64,
        retained_source_sha256=hashlib.sha256(text.encode()).hexdigest(),
        spans=(mod.OfflineRedactionSpan(0, len(text), "SECRET"),),
    )


@pytest.mark.parametrize(
    "field,forged",
    [
        ("owner_digest", "f" * 64),
        ("scope_digest", "f" * 64),
        ("source_sha256", "f" * 64),
        ("masked_text", "synthetic-private-data"),
        ("masked_characters", True),
        ("complete_masking", False),
        ("local_digest", "f" * 64),
    ],
)
def test_last_authority_callback_cannot_change_redacted_receipt(
    monkeypatch, field, forged,
):
    def mutate(self):
        object.__setattr__(self, field, forged)
        return False

    monkeypatch.setattr(
        mod.RedactedOfflinePreview,
        "tool_dispatch_authorized",
        property(mutate),
    )
    with pytest.raises(mod.OfflineRedactionRejected, match="authority definition changed"):
        _redact()


def test_denial_only_callback_without_mutation_is_not_the_original(monkeypatch):
    monkeypatch.setattr(
        mod.RedactedOfflinePreview,
        "tool_dispatch_authorized",
        property(lambda _self: False),
    )
    with pytest.raises(mod.OfflineRedactionRejected, match="authority definition changed"):
        _redact()

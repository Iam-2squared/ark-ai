"""Private fixture data must not appear in implicit dataclass diagnostics.

repr=False is a defense against accidental log/exception disclosure, not
encryption, redaction of explicit serialization, or disclosure authorization.
"""

from dataclasses import asdict, fields

import pytest

from ark.local_text_chunking import (
    LocalChunkRequest,
    LocalTextChunk,
    LocalTextChunkBundle,
)
from ark.offline_context_redaction import RedactedOfflinePreview
from ark.offline_context_search import (
    OfflineContextSearchHit,
    OfflineContextSearchPreview,
    OfflineContextSearchRecord,
)
from ark.offline_pcm_wav import OfflineWaveRequest
from ark.offline_text_index import OfflineIndexDocument, OfflineIndexQuery
from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    OfflineContextPreview,
)

_SECRET = "private_payload_DO_NOT_LOG_run452"
_A = "a" * 64
_B = "b" * 64
_C = "c" * 64


@pytest.mark.parametrize(
    ("cls", "field_name"),
    [
        (OfflineContextFixture, "content"),
        (OfflineContextPreview, "canonical_local_json"),
        (OfflineContextSearchRecord, "content"),
        (OfflineContextSearchHit, "excerpt"),
        (OfflineContextSearchPreview, "query"),
        (OfflineIndexDocument, "text"),
        (OfflineIndexQuery, "query"),
        (LocalChunkRequest, "text"),
        (LocalTextChunk, "text"),
        (OfflineWaveRequest, "wav_bytes"),
        (RedactedOfflinePreview, "masked_text"),
    ],
)
def test_sensitive_dataclass_field_disallows_implicit_repr(cls, field_name):
    descriptor = next(f for f in fields(cls) if f.name == field_name)
    assert descriptor.repr is False


def test_personal_context_nested_preview_keeps_plaintext_out_of_repr():
    row = OfflineContextFixture("rec_" + "0" * 32, _A, _B, _SECRET, _C, 2000)
    preview = OfflineContextPreview(_A, (row.record_id,), _SECRET, _B)
    assert _SECRET not in repr(row)
    assert _SECRET not in repr(preview)
    assert row.content == _SECRET
    assert preview.canonical_local_json == _SECRET
    # This defense intentionally does not make explicit serialization safe.
    assert asdict(row)["content"] == _SECRET
    assert asdict(preview)["canonical_local_json"] == _SECRET
    assert preview.external_export_authorized is False


def test_local_search_and_index_containers_do_not_reexpose_nested_text():
    row = OfflineContextSearchRecord("rec_" + "0" * 32, _A, _B, _SECRET, _C, 2000)
    hit = OfflineContextSearchHit(row.record_id, 1, _SECRET)
    preview = OfflineContextSearchPreview(_A, _SECRET, (hit,), _B)
    document = OfflineIndexDocument("doc1", _A, _B, _C, _SECRET)
    index = OfflineIndexQuery(_A, _B, _C, _SECRET, (document,), ("doc1",))
    for item in (row, hit, preview, document, index):
        assert _SECRET not in repr(item)
    assert hit.excerpt == _SECRET
    assert document.text == _SECRET
    assert preview.external_export_authorized is False


def test_local_chunk_containers_hide_original_and_derived_text():
    source = LocalChunkRequest(_SECRET, _A, _B, _C)
    chunk = LocalTextChunk(0, 0, len(_SECRET), _SECRET, _A)
    bundle = LocalTextChunkBundle(_B, _C, _A, 1024, (chunk,), _A)
    for item in (source, chunk, bundle):
        assert _SECRET not in repr(item)
    assert chunk.text == _SECRET
    assert bundle.disclosure_authorized is False


def test_raw_wave_and_partially_redacted_preview_remain_hidden():
    wave = OfflineWaveRequest(_A, _B, _C, _SECRET.encode("ascii"))
    redaction = RedactedOfflinePreview(_A, _B, _C, _SECRET, 0, False, _A)
    assert _SECRET not in repr(wave)
    assert _SECRET not in repr(redaction)
    assert wave.wav_bytes == _SECRET.encode("ascii")
    assert redaction.masked_text == _SECRET
    assert redaction.external_export_authorized is False

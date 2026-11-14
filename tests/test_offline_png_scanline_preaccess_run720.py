"""PNG scanline codec swaps must fail before private compressed bytes are read."""

from __future__ import annotations

import hashlib
import zlib

import pytest

import ark.offline_png_scanlines as png


def _fixture():
    encoded = zlib.compress(b"\x00\x10\x20")
    request = png.OfflineScanlineRequest(
        "a" * 64, "b" * 64, hashlib.sha256(encoded).hexdigest(),
        encoded, 2, 1, 0, 8, 0,
    )
    return request, png.inspect_offline_png_scanlines(request)


@pytest.mark.parametrize("primitive", ("sha256", "decompressobj"))
@pytest.mark.parametrize("review", ("inspect", "verify"))
def test_untrusted_private_idat_never_reaches_swapped_codec(
    monkeypatch, primitive, review,
):
    request, audit = _fixture()
    called = []

    def adversary(*args, **kwargs):
        called.append((args, kwargs))
        raise AssertionError("untrusted compressed data reached an injected callback")

    module = png.hashlib if primitive == "sha256" else png.zlib
    monkeypatch.setattr(module, primitive, adversary)
    with pytest.raises(png.OfflineScanlineRejected, match="codec"):
        if review == "inspect":
            png.inspect_offline_png_scanlines(request)
        else:
            png.verify_offline_png_scanlines(audit, request)
    assert called == []


@pytest.mark.parametrize("field", ("idat_bytes", "privacy_sha256", "__getattribute__"))
def test_swapped_request_descriptor_denied_without_invoking_getter(
    monkeypatch, field,
):
    request, _audit = _fixture()
    invoked = []

    def adversary(*args):
        invoked.append(args)
        raise AssertionError("hostile request descriptor invoked")

    if field == "__getattribute__":
        monkeypatch.setattr(png.OfflineScanlineRequest, field, adversary)
    else:
        monkeypatch.setattr(png.OfflineScanlineRequest, field, property(adversary))
    with pytest.raises(png.OfflineScanlineRejected, match="request"):
        png.inspect_offline_png_scanlines(request)
    assert invoked == []

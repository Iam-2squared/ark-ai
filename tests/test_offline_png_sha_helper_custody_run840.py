"""PNG private digest labels must never reach a replaced validation callback."""

import pytest

import ark.offline_png_inventory as png


def _fixture() -> png.OfflinePngRequest:
    return png.OfflinePngRequest(
        "a" * 64,
        "b" * 64,
        "c" * 64,
        b"private synthetic bytes, not a PNG",
    )


def test_private_png_digest_refuses_swapped_helper_before_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[object] = []

    def hostile_sha(value: object) -> bool:
        observed.append(value)
        return True

    monkeypatch.setattr(png, "_sha", hostile_sha)
    with pytest.raises(png.OfflinePngRejected, match="framing limits"):
        png.inspect_disconnected_png(_fixture())
    assert observed == []


@pytest.mark.parametrize("invalid", ["a" * 65, "a" * 100_000, "g" * 64, "\ud800" * 64])
def test_digest_helper_rejects_noncanonical_fixed_width_labels(invalid: str) -> None:
    assert png._sha(invalid) is False


def test_digest_helper_accepts_canonical_lowercase_sha256() -> None:
    assert png._sha("a" * 64) is True

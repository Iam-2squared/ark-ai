"""Offline PNG request/result carriers reject executable substitutions preaccess.

Disposable synthetic PNG bytes only. Isolated Python interpreters prevent
special-method mutations from affecting unrelated regression tests.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

_SCRIPT = """
import hashlib
import struct
import sys
import zlib

import ark.offline_png_inventory as png

def chunk(kind, body):
    return (
        struct.pack(">I", len(body)) + kind + body
        + struct.pack(">I", zlib.crc32(kind + body))
    )

data = (
    b"\\x89PNG\\r\\n\\x1a\\n"
    + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
    + chunk(b"IDAT", b"fixture-not-decoded")
    + chunk(b"IEND", b"")
)
request = png.OfflinePngRequest(
    "a" * 64, "b" * 64, hashlib.sha256(data).hexdigest(), data,
)
first = png.inspect_disconnected_png(request)
assert first.width == first.height == 1
assert first.consent_verified is False
assert first.decoded_pixels_verified is False

visited = []

def hostile(*args, **kwargs):
    visited.append("hostile descriptor invoked")
    raise AssertionError("private PNG bytes reached substituted code")

kind = sys.argv[1]
if kind == "request_bytes":
    png.OfflinePngRequest.png_bytes = property(hostile)
elif kind == "request_lookup":
    png.OfflinePngRequest.__getattribute__ = hostile
elif kind == "request_new":
    png.OfflinePngRequest.__new__ = staticmethod(hostile)
elif kind == "result_init":
    png.OfflinePngInventory.__init__ = hostile
elif kind == "result_slot":
    png.OfflinePngInventory.idat_sha256 = property(hostile)
elif kind == "result_lookup":
    png.OfflinePngInventory.__getattribute__ = hostile
elif kind == "crc_injected_request_bytes":
    crc = png.zlib.crc32
    def mutate_after_crc(payload):
        value = crc(payload)
        png.OfflinePngRequest.png_bytes = property(hostile)
        return value
    png.zlib.crc32 = mutate_after_crc
else:
    raise AssertionError("unknown fixture")

try:
    png.inspect_disconnected_png(request)
except png.OfflinePngRejected as exc:
    expected = (
        "PNG framing implementation changed"
        if kind.startswith("crc_")
        else (
            "PNG request identity descriptor changed"
            if kind.startswith("request_") else "constructed PNG inventory"
        )
    )
    assert expected in str(exc), str(exc)
else:
    raise AssertionError("modified PNG carrier was accepted")
assert visited == []
"""


@pytest.mark.parametrize(
    "kind",
    (
        "request_bytes", "request_lookup", "request_new",
        "result_init", "result_slot", "result_lookup",
        "crc_injected_request_bytes",
    ),
)
def test_synthetic_png_carrier_rejected_before_private_getter(kind):
    process = subprocess.run(
        [sys.executable, "-c", _SCRIPT, kind],
        capture_output=True, text=True, check=False, timeout=30,
    )
    assert process.returncode == 0, process.stderr

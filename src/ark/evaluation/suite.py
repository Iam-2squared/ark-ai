"""Load immutable packaged evaluation data and verify its content hash."""

import hashlib
import json
from importlib.resources import files

# Pinned independently of suite.sha256 so changing both files cannot silently replace v1.
SUITE_SHA256 = "bbf8556266fc473cf6be8039b0e40656cb06086958b3d6a98d4d338c11908c1b"


def load_suite() -> dict:
    root = files("ark.evaluation").joinpath("data")
    raw = root.joinpath("suite.json").read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SUITE_SHA256 or root.joinpath("suite.sha256").read_text().strip() != digest:
        raise ValueError("frozen evaluation suite hash mismatch")
    suite = json.loads(raw)
    ids = [c["id"] for c in suite["cases"]]
    if len(ids) != len(set(ids)) or not ids:
        raise ValueError("task IDs must be unique and nonempty")
    return suite

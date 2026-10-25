"""Memory v1 write metadata bounded copy; no I/O or schema changes."""

from collections.abc import Mapping
from itertools import count

import pytest

from ark.memory.contracts import MemoryScope, MemoryWrite


SCOPE = MemoryScope("owner", "namespace")


class FakeLengthInfinite(Mapping):
    def __init__(self):
        self.yielded = 0

    def __len__(self):
        return 0

    def __iter__(self):
        return iter(())

    def __getitem__(self, key):
        raise KeyError(key)

    def items(self):
        for number in count():
            self.yielded += 1
            yield f"key{number}", str(number)


class DuplicateYield(Mapping):
    def __len__(self):
        return 1

    def __iter__(self):
        return iter(("key",))

    def __getitem__(self, key):
        return "new"

    def items(self):
        yield "key", "old"
        yield "key", "new"


def _write(meta):
    return MemoryWrite(SCOPE, "fixture", "offline text", meta)


def test_infinite_mapping_items_has_bounded_materialization():
    hostile = FakeLengthInfinite()
    with pytest.raises(ValueError, match="metadata exceeds 64 entries"):
        _write(hostile)
    assert hostile.yielded == 65


def test_duplicate_mapping_items_cannot_silently_replace_value():
    with pytest.raises(ValueError, match="duplicate key"):
        _write(DuplicateYield())


def test_exact_metadata_entry_budget_accepts_64():
    fields = {f"key{i}": str(i) for i in range(64)}
    result = _write(fields)
    assert dict(result.metadata) == fields


def test_regular_mapping_rejects_65_entries_before_copy():
    with pytest.raises(ValueError, match="metadata exceeds 64 entries"):
        _write({f"key{i}": str(i) for i in range(65)})


def test_metadata_copy_is_detached_from_mutable_caller_map():
    fields = {"key": "original"}
    result = _write(fields)
    fields["key"] = "changed"
    assert dict(result.metadata) == {"key": "original"}
    with pytest.raises(TypeError):
        result.metadata["key"] = "changed"


def test_existing_metadata_key_and_value_length_guards_stay_active():
    with pytest.raises(ValueError, match="metadata key"):
        _write({"k" * 4097: "value"})
    with pytest.raises(ValueError, match="metadata value exceeds"):
        _write({"key": "x" * 4097})

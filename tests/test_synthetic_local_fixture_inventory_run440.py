"""Free-only artifact provenance diagnostics cannot authorize computing."""

import hashlib
from dataclasses import FrozenInstanceError

import pytest

from ark.synthetic_local_fixture_inventory_review import (
    SyntheticFixtureFile,
    SyntheticFixtureInventory,
    SyntheticFixtureInventoryRejected,
    assert_fixture_inventory_integrity,
    review_local_fixture_inventory,
)


def _file(root, name, data=b"fixture"):
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return target


def test_deterministic_readonly_inventory_and_retained_review(tmp_path):
    _file(tmp_path, "a.json", b'{"x": 1}')
    _file(tmp_path, "nested/b.txt", b"\xff\x00\x01")
    paths = ("a.json", "nested/b.txt")
    first = review_local_fixture_inventory(tmp_path, paths)
    assert first == review_local_fixture_inventory(tmp_path, paths, retained=first)
    assert len(first.files) == 2
    assert first.files[1].sha256 == hashlib.sha256(b"\xff\x00\x01").hexdigest()
    assert not first.training_authorized
    assert not first.dispatch_authorized
    assert not first.external_provenance_verified
    assert_fixture_inventory_integrity(first)
    with pytest.raises(FrozenInstanceError):
        first.files = ()


def test_nonexistent_files_do_not_get_created(tmp_path):
    with pytest.raises(SyntheticFixtureInventoryRejected, match="unavailable"):
        review_local_fixture_inventory(tmp_path, ("missing.txt",))
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("bad", [
    "/etc/passwd", "../up.txt", "x/../y.txt", "x/./y.txt",
    "x//y.txt", "x\\y.txt", "C:/data.txt", "a:stream.txt",
    ".env", "secret/.private.json", "CON.txt", "LPT1.txt",
    "leading /x.txt", "space .txt", "a.json/", "other.bin",
    "x\x00y.txt", "x\ny.txt", "x\ud800.txt", "e\u0301.txt",
])
def test_unsafe_paths_rejected_without_io(tmp_path, bad):
    with pytest.raises(SyntheticFixtureInventoryRejected):
        review_local_fixture_inventory(tmp_path, (bad,))
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("paths", [
    ("b.txt", "a.txt"), ("a.txt", "a.txt"),
    ("Case.txt", "case.txt"), (), tuple(f"x{i:03}.txt" for i in range(65)),
    ("a.txt", "b.txt", "a.txt"),
])
def test_duplicate_budget_or_unsorted_paths_rejected(tmp_path, paths):
    with pytest.raises(SyntheticFixtureInventoryRejected):
        review_local_fixture_inventory(tmp_path, paths)


def test_symlink_files_and_parents_fail_closed(tmp_path):
    outside = tmp_path.parent / "external_fixture.txt"
    outside.write_bytes(b"do not read")
    try:
        (tmp_path / "linked.txt").symlink_to(outside)
        with pytest.raises(SyntheticFixtureInventoryRejected):
            review_local_fixture_inventory(tmp_path, ("linked.txt",))
        (tmp_path / "alias").symlink_to(tmp_path, target_is_directory=True)
        with pytest.raises(SyntheticFixtureInventoryRejected):
            review_local_fixture_inventory(tmp_path, ("alias/linked.txt",))
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")


def test_retain_detects_equal_length_payload_substitution(tmp_path):
    target = _file(tmp_path, "proof.fixture", b"aaaa")
    retained = review_local_fixture_inventory(tmp_path, ("proof.fixture",))
    target.write_bytes(b"bbbb")
    with pytest.raises(SyntheticFixtureInventoryRejected, match="retained"):
        review_local_fixture_inventory(tmp_path, ("proof.fixture",), retained=retained)


def test_reflective_witness_corruption_is_rejected(tmp_path):
    _file(tmp_path, "a.txt")
    witness = review_local_fixture_inventory(tmp_path, ("a.txt",))
    object.__setattr__(witness.files[0], "sha256", "f" * 64)
    with pytest.raises(SyntheticFixtureInventoryRejected, match="witness"):
        assert_fixture_inventory_integrity(witness)
    with pytest.raises(SyntheticFixtureInventoryRejected):
        review_local_fixture_inventory(tmp_path, ("a.txt",), retained=witness)


def test_bad_independent_witness_cannot_attest_local_origin(tmp_path):
    _file(tmp_path, "a.txt", b"a")
    witness = SyntheticFixtureInventory((
        SyntheticFixtureFile("a.txt", 1, hashlib.sha256(b"a").hexdigest()),
    ), "fixtureinventory_" + "0" * 64)
    with pytest.raises(SyntheticFixtureInventoryRejected, match="witness"):
        review_local_fixture_inventory(tmp_path, ("a.txt",), retained=witness)
    with pytest.raises(SyntheticFixtureInventoryRejected):
        assert_fixture_inventory_integrity(object())


def test_non_regular_file_rejected(tmp_path):
    (tmp_path / "dir.txt").mkdir()
    with pytest.raises(SyntheticFixtureInventoryRejected, match="unsafe fixture file"):
        review_local_fixture_inventory(tmp_path, ("dir.txt",))


def test_exact_types_for_size_and_digest_rejected():
    row = SyntheticFixtureFile("x.txt", True, "f" * 64)
    witness = SyntheticFixtureInventory((row,), "fixtureinventory_" + "0" * 64)
    with pytest.raises(SyntheticFixtureInventoryRejected, match="row"):
        assert_fixture_inventory_integrity(witness)


def test_file_budget_checked_before_open(tmp_path, monkeypatch):
    from ark import synthetic_local_fixture_inventory_review as inventory

    _file(tmp_path, "large.json", b"123456")
    monkeypatch.setattr(inventory, "_MAX_FILE_BYTES", 4)
    with pytest.raises(SyntheticFixtureInventoryRejected, match="size"):
        review_local_fixture_inventory(tmp_path, ("large.json",))


def test_root_symlink_refused(tmp_path):
    link = tmp_path.parent / "link_to_synthetic_root"
    try:
        link.symlink_to(tmp_path, target_is_directory=True)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")
    _file(tmp_path, "x.json")
    with pytest.raises(SyntheticFixtureInventoryRejected, match="unsafe fixture root"):
        review_local_fixture_inventory(link, ("x.json",))

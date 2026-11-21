"""Offline authorization packet output custody; no GPU, training or approval."""

from pathlib import Path

import pytest

from ark.learning import authorization as mod
from ark.learning.execution import canonical_json


def test_new_packet_is_canonical_and_review_only(tmp_path):
    packet = {
        "schema_version": 1,
        "candidate_created": False,
        "full_training_authorized": False,
    }
    target = tmp_path / "authorization_review.json"
    mod._write_new_authorization_packet(target, packet)
    assert target.read_bytes() == canonical_json(packet)
    assert packet["full_training_authorized"] is False
    with pytest.raises(ValueError, match="non-aliased"):
        mod._write_new_authorization_packet(target, packet)


@pytest.mark.parametrize(
    "kind",
    [
        "existing", "directory", "missing_parent", "dotdot",
        "overlong", "symlink", "dangling_symlink", "linked_parent",
    ],
)
def test_output_aliases_are_denied_before_writing(tmp_path, kind):
    target = tmp_path / "packet.json"
    protected = tmp_path / "protected.json"
    protected.write_bytes(b"leave-unchanged")
    if kind == "existing":
        target.write_bytes(b"leave-unchanged")
    elif kind == "directory":
        target.mkdir()
    elif kind == "missing_parent":
        target = tmp_path / "absent" / "packet.json"
    elif kind == "dotdot":
        (tmp_path / "staging").mkdir()
        target = tmp_path / "staging" / ".." / "packet.json"
    elif kind == "overlong":
        target = tmp_path / ("x" * 4100)
    elif kind == "symlink":
        try:
            target.symlink_to(protected)
        except (OSError, NotImplementedError):
            pytest.skip("filesystem cannot create symlinks")
    elif kind == "dangling_symlink":
        try:
            target.symlink_to(tmp_path / "missing.json")
        except (OSError, NotImplementedError):
            pytest.skip("filesystem cannot create symlinks")
    else:
        folder = tmp_path / "destination"
        folder.mkdir()
        linked = tmp_path / "linked"
        try:
            linked.symlink_to(folder, target_is_directory=True)
        except (OSError, NotImplementedError):
            pytest.skip("filesystem cannot create directory symlinks")
        target = linked / "packet.json"
    with pytest.raises(ValueError, match="non-aliased"):
        mod._write_new_authorization_packet(
            target, {"full_training_authorized": False},
        )
    assert protected.read_bytes() == b"leave-unchanged"
    if kind == "existing":
        assert target.read_bytes() == b"leave-unchanged"


def test_packet_cli_uses_aliased_path_guard(tmp_path, monkeypatch):
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(mod, "load_snapshot", lambda _: {})
    monkeypatch.setattr(
        mod, "build_preflight_authorization_packet",
        lambda _: {"candidate_created": False},
    )
    (tmp_path / "staging").mkdir()
    target = tmp_path / "staging" / ".." / "packet.json"
    with pytest.raises(ValueError, match="non-aliased"):
        mod.main(["--snapshot", str(snapshot), "--output", str(target)])
    assert not (tmp_path / "packet.json").exists()


def test_new_packet_path_type_is_exact(tmp_path):
    class OtherPath(type(Path())):
        pass

    target = OtherPath(tmp_path / "packet.json")
    with pytest.raises(ValueError, match="non-aliased"):
        mod._write_new_authorization_packet(target, {"candidate_created": False})

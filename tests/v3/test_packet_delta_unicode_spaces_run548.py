"""Review packet paths must not hide non-printing Unicode space characters."""

import pytest

from ark.learning.authorization_packet_delta_review import _leaf_bytes
from ark.learning.execution import canonical_json


@pytest.mark.parametrize(
    "codepoint",
    [
        0x00A0,  # no-break space
        0x1680,  # ogham space mark
        0x2002,  # en space
        0x2003,  # em space
        0x2009,  # thin space
        0x202F,  # narrow no-break space
        0x205F,  # medium mathematical space
        0x3000,  # ideographic space
    ],
)
def test_nonprinting_space_paths_have_unambiguous_printable_escape(codepoint):
    key = "before" + chr(codepoint) + "after"
    expected = f"before~u{{{codepoint:X}}}after"
    paths = _leaf_bytes({key: 1})
    assert paths == {expected: canonical_json(1)}
    assert expected.isprintable()


def test_plain_ascii_space_remains_readable():
    assert _leaf_bytes({"before after": 1}) == {
        "before after": canonical_json(1),
    }


def test_nonbreaking_space_does_not_alias_ascii_space_or_literal_escape():
    paths = _leaf_bytes({
        "a\u00a0b": 1,
        "a b": 2,
        "a~u{A0}b": 3,
    })
    assert paths == {
        "a~u{A0}b": canonical_json(1),
        "a b": canonical_json(2),
        "a~0u{A0}b": canonical_json(3),
    }


def test_nested_nonprinting_space_path_does_not_alias_literal_marker():
    paths = _leaf_bytes({
        "outer": {
            "\u202f": 1,
            "~u{202F}": 2,
        },
    })
    assert paths == {
        "outer.~u{202F}": canonical_json(1),
        "outer.~0u{202F}": canonical_json(2),
    }

"""Run1230: strict V3 JSON parser rejects caller-controlled input subclasses."""

from __future__ import annotations

import pytest

from ark.learning.dataset import loads_unique_json


def test_exact_builtin_text_and_bytes_remain_supported() -> None:
    assert loads_unique_json('{"value": 1}') == {"value": 1}
    assert loads_unique_json(b'{"value": 1}') == {"value": 1}


def test_text_subclass_is_rejected_before_decoder_methods_run() -> None:
    class CallbackText(str):
        def lstrip(self, *args, **kwargs):
            raise AssertionError("str subclass decoder callback must not run")

    with pytest.raises(TypeError, match="exact str or bytes"):
        loads_unique_json(CallbackText('{"value": 1}'))


def test_bytes_subclass_is_rejected_before_decode_method_runs() -> None:
    class CallbackBytes(bytes):
        def decode(self, *args, **kwargs):
            raise AssertionError("bytes subclass decode callback must not run")

    with pytest.raises(TypeError, match="exact str or bytes"):
        loads_unique_json(CallbackBytes(b'{"value": 1}'))


def test_bytearray_is_outside_the_exact_parser_contract() -> None:
    with pytest.raises(TypeError, match="exact str or bytes"):
        loads_unique_json(bytearray(b'{"value": 1}'))

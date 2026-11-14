"""Isolate CPython inherited __new__ attacks on detached READ carriers.

A restored class dictionary is not enough to repair CPython's changed tp_new
slot in the running pytest interpreter. Test these fail-closed guards in a
fresh local process so no later tests inherit interpreter-wide damage.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest


@pytest.mark.parametrize("carrier", ("SyntheticReadResult", "SyntheticBoundArguments"))
def test_read_carrier_new_hook_is_rejected_in_child_python(carrier):
    script = textwrap.dedent(
        """
        import json
        import ark.agency.disconnected_reference_binding as binding

        step = 'step_' + '1' * 16
        raw = '{"value":4}'
        row = binding.SyntheticReadResult(
            step, raw, binding.read_result_digest(step, raw),
        )
        template = json.dumps(
            {'n': {'$from': {'pointer': '/value', 'step_id': step}}},
            sort_keys=True, separators=(',', ':'),
        )
        called = []

        def bad(*_args, **_kwargs):
            called.append('new')
            raise AssertionError('substituted constructor executed')

        cls = getattr(binding, 'TARGET_CARRIER')
        cls.__new__ = staticmethod(bad)
        try:
            binding.bind_synthetic_read_arguments(
                'req_' + 'a' * 32, template, (step,), (row,),
            )
        except binding.ReadBindingRejected as exc:
            assert 'carrier definition changed' in str(exc)
        else:
            raise AssertionError('substituted allocation hook not rejected')
        assert called == []
        """
    ).replace("TARGET_CARRIER", carrier)
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, check=False, timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr

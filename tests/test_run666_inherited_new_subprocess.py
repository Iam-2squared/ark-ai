"""Isolate inherited __new__ poisoning from the shared Python test process.

CPython may leave tp_new altered even after monkeypatch restores the class
dictionary. Execute these deny-only carrier checks in disposable interpreters.
No real backend, notification, consent or external service is used.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest


@pytest.mark.parametrize("carrier", ("registered_read", "revocation"))
def test_inherited_new_rejected_in_disposable_process(carrier):
    script = textwrap.dedent(
        """
        import pathlib
        import sys
        import tempfile

        sys.path.insert(0, str(pathlib.Path.cwd() / "tests"))
        called = []

        def forged_new(*args, **kwargs):
            called.append("new")
            raise AssertionError("forged allocator must never execute")

        with tempfile.TemporaryDirectory() as root:
            path = pathlib.Path(root)
            if "TARGET" == "registered_read":
                from test_recovered_registered_read_join_run550 import invoke, make_case
                import ark.agency.disconnected_recovered_registered_read_join as module

                case = make_case(path)
                module.RecoveredRegisteredReadReview.__new__ = staticmethod(forged_new)
                try:
                    invoke(case)
                except module.RecoveredRegisteredReadRejected as exc:
                    assert "recovery carrier changed" in str(exc)
                else:
                    raise AssertionError("malformed report constructor accepted")
                finally:
                    case["journal"].close()
                assert case["backend"].calls == 0
                assert not case["gate"]._consumed_tokens
            else:
                import ark.personal_context_revocation_continuity_review as module
                from ark.memory.contracts import MemoryScope
                from ark.personal_context_revocation_review import (
                    SyntheticContextRevocationLedger, SyntheticContextRevocationRejected,
                )

                ledger = SyntheticContextRevocationLedger(path / "veto.sqlite")
                ledger.revoke(MemoryScope("owner", "private"), at_ms=100)
                retained = module.review_revocation_continuity(ledger)
                module.SyntheticRevocationWitness.__new__ = staticmethod(forged_new)
                try:
                    module.review_revocation_continuity(ledger, retained=retained)
                except SyntheticContextRevocationRejected as exc:
                    assert "revocation integrity validator changed" in str(exc)
                else:
                    raise AssertionError("malformed revocation allocator accepted")
            assert called == []
        """
    ).replace("TARGET", carrier)
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, check=False, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr

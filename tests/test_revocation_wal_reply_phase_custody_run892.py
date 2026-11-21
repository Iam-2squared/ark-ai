"""Do not promote impossible subprocess status/phase combinations.

The WAL diagnostic uses synthetic replies; none is authority to replay a
revocation, reopen private data, or authorize an external side effect.
"""

from importlib import util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "diagnose_revocation_wal_processes.py"
_SPEC = util.spec_from_file_location("revocation_wal_reply_phase_run892", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


@pytest.mark.parametrize("claimed_success", ("REVOKED", "ALREADY"))
def test_success_claim_during_bootstrap_is_invalid(claimed_success):
    reply = '{"status":"' + claimed_success + '","phase":"BOOTSTRAP"}'
    assert _MODULE._parse_reply(reply) == {
        "status": "INVALID_REPLY", "phase": "UNKNOWN",
    }


@pytest.mark.parametrize("claimed_success", ("REVOKED", "ALREADY"))
def test_success_claim_in_revoke_phase_stays_classified_only(claimed_success):
    reply = '{"status":"' + claimed_success + '","phase":"REVOKE"}'
    assert _MODULE._parse_reply(reply) == {
        "status": claimed_success, "phase": "REVOKE",
    }

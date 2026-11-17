"""Run946: COMMIT-UNKNOWN local triage is restart-stable and deny-only.

Separate interpreters observe an inert local two-commit ledger. This neither
dispatches a ToolBackend nor identifies any real external effect.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict

import pytest

from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
from ark.agency.disconnected_atomic_unknown_outcome_review import (
    review_atomic_unknown_outcome,
)

_CHILD = """
import json
import sys
from pathlib import Path
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim, AtomicPreactionWitness, DisconnectedAtomicPreactionLedger,
)
from ark.agency.disconnected_atomic_unknown_outcome_review import (
    review_atomic_unknown_outcome,
)
before = AtomicPreactionWitness(**json.loads(sys.argv[2]))
claim = AtomicIntentClaim(**json.loads(sys.argv[3]))
observed = review_atomic_unknown_outcome(
    DisconnectedAtomicPreactionLedger(Path(sys.argv[1])), before, claim,
)
print(json.dumps({
    "occurrence_id": observed.occurrence_id,
    "state": observed.local_state,
    "counts": [observed.before_count, observed.observed_count],
    "present": observed.locally_present,
    "denials": [
        observed.dispatch_authorized, observed.automatic_replay_authorized,
        observed.external_effect_verified, observed.independent_custody_verified,
        observed.manual_review_required,
    ],
}, sort_keys=True))
"""


def _claim(letter: str) -> AtomicIntentClaim:
    return AtomicIntentClaim(
        "occ_" + letter * 64, "bound_" + letter * 64, letter * 64,
    )


@pytest.mark.parametrize(("prefix", "target", "state"), (
    ("genesis", "a", "LOCALLY_RECORDED"),
    ("first", "a", "PREEXISTING"),
    ("first", "c", "ADVANCED_OTHER"),
    ("second", "c", "UNCHANGED"),
))
def test_cold_review_retains_manual_unknown_outcome_after_two_local_commits(
    tmp_path, prefix: str, target: str, state: str,
) -> None:
    path = tmp_path / "synthetic-unknown-outcome.sqlite3"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    genesis = genesis_atomic_preaction_witness()
    first = ledger.reserve(_claim("a"), retained=genesis)
    second = ledger.reserve(_claim("b"), retained=first)
    before = {"genesis": genesis, "first": first, "second": second}[prefix]
    claim = _claim(target)

    local = review_atomic_unknown_outcome(
        DisconnectedAtomicPreactionLedger(path), before, claim,
    )
    assert local.local_state == state
    expected = {
        "occurrence_id": claim.occurrence_id,
        "state": state,
        "counts": [before.count, 2],
        "present": target in ("a", "b"),
        "denials": [False, False, False, False, True],
    }
    remote = subprocess.run(
        [sys.executable, "-c", _CHILD, str(path),
         json.dumps(asdict(before), sort_keys=True),
         json.dumps(asdict(claim), sort_keys=True)],
        text=True, capture_output=True, check=True, timeout=20,
    )
    assert json.loads(remote.stdout) == expected
    assert local.dispatch_authorized is False
    assert local.automatic_replay_authorized is False
    assert local.external_effect_verified is False
    assert local.independent_custody_verified is False
    assert local.manual_review_required is True
    assert ledger.inspect(second).witness == second

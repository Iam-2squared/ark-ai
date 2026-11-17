"""Run947: retained prefixes across four local commits remain manual-only.

All claims, audit rows and subprocesses are synthetic, disconnected and local.
No external side effect or independent provenance is inferred.
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

_COLD = """
import json
import sys
from pathlib import Path
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim, AtomicPreactionWitness, DisconnectedAtomicPreactionLedger,
)
from ark.agency.disconnected_atomic_unknown_outcome_review import (
    review_atomic_unknown_outcome,
)
prior = AtomicPreactionWitness(**json.loads(sys.argv[2]))
claim = AtomicIntentClaim(**json.loads(sys.argv[3]))
result = review_atomic_unknown_outcome(
    DisconnectedAtomicPreactionLedger(Path(sys.argv[1])), prior, claim,
)
print(json.dumps([
    result.local_state, result.before_count, result.observed_count,
    result.locally_present, result.dispatch_authorized,
    result.automatic_replay_authorized, result.external_effect_verified,
    result.independent_custody_verified, result.manual_review_required,
]))
"""


def _claim(letter: str) -> AtomicIntentClaim:
    return AtomicIntentClaim(
        "occ_" + letter * 64, "bound_" + letter * 64, letter * 64,
    )


@pytest.mark.parametrize(("prefix_count", "target", "expected"), (
    (0, "a", "LOCALLY_RECORDED"),
    (0, "z", "ADVANCED_OTHER"),
    (1, "a", "PREEXISTING"),
    (1, "d", "LOCALLY_RECORDED"),
    (3, "b", "PREEXISTING"),
    (3, "d", "LOCALLY_RECORDED"),
    (3, "z", "ADVANCED_OTHER"),
    (4, "d", "PREEXISTING"),
    (4, "z", "UNCHANGED"),
))
def test_four_commit_local_prefix_classification_is_cold_and_denied(
    tmp_path, prefix_count: int, target: str, expected: str,
) -> None:
    path = tmp_path / "synthetic-four-commit-unknown.sqlite3"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    generations = [genesis_atomic_preaction_witness()]
    for letter in "abcd":
        generations.append(ledger.reserve(_claim(letter), retained=generations[-1]))
    prior = generations[prefix_count]
    claim = _claim(target)
    observed = review_atomic_unknown_outcome(
        DisconnectedAtomicPreactionLedger(path), prior, claim,
    )
    assert observed.local_state == expected
    assert observed.before_count == prefix_count
    assert observed.observed_count == 4
    assert observed.locally_present is (target in "abcd")
    expected_cold = [
        expected, prefix_count, 4, target in "abcd",
        False, False, False, False, True,
    ]
    cold = subprocess.run(
        [sys.executable, "-c", _COLD, str(path),
         json.dumps(asdict(prior), sort_keys=True),
         json.dumps(asdict(claim), sort_keys=True)],
        capture_output=True, text=True, check=True, timeout=20,
    )
    assert json.loads(cold.stdout) == expected_cold
    assert ledger.inspect(generations[-1]).witness == generations[-1]

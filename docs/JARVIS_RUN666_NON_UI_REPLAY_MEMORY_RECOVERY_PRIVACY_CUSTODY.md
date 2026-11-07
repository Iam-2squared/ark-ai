# ARK AI — Run666: non-UI replay, Memory attribution, recovered READ and privacy custody

Scope: disconnected, local-first, **free-only** non-UI foundations on
`research/jarvis-foundations` / [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8).
This note records incremental synthetic implementations and regressions,
**not** an independent security audit or authorization for live effects.

## Baseline and inherited CI blocker

- Initial work-basis HEAD: `95503e7ea2b059c09220c7eb21ef9b04c382b0d6`;
  preceding Run665 [CI #42256960404](https://github.com/Iam-2squared/ark-ai/actions/runs/42256960404)
  completed **FAIL in all six jobs**. Ubuntu Python 3.11 log:
  `test_post_commit_descriptor_drift_is_reported_without_erasing_marker`
  expected `duplicate` but encountered `minimum preparation interval`.
  The SQLite marker had committed; the fixture's second `now_ms=100` was
  simply too soon to reach the duplicate primary-key fence.
- The test-only correction `ebdea45e300e1a6416256cc473c6e62b122cc86b`
  retries the **same content-addressed occurrence** at `now_ms=105`
  (minimum interval 5), retaining `observed_at_ms=100`. It checks durable
  duplicate refusal without relaxing rate-limit or pre-COMMIT guards.
  [CI #42263932941](https://github.com/Iam-2squared/ark-ai/actions/runs/42263932941)
  was **Ubuntu 3/3 GREEN, Windows 3 IN PROGRESS** at the sampled job review.

## New independent work packages

1. **Memory ambiguous writer attribution —**
   `0512f618f5fbd5bd053e320b0cb23c3c192f5a8f`,
   `tests/test_memory_ambiguity_independent_writer_run666.py`:
   three synthetic multi-connection cases: a second SQLite writer's
   exactly matching update is only `MATCHING_ROW_MANUAL_REVIEW`, two
   identical updates become `DIVERGED_MANUAL_REVIEW`, and a concurrent
   unrelated-owner write does not confer target-row caller attribution.
   Read-only reviews preserve local event/row data, while all consent,
   replay, write and trusted-clock flags remain False.
   [CI #42264119180](https://github.com/Iam-2squared/ark-ai/actions/runs/42264119180)
   was **Ubuntu 3/3 GREEN, Windows IN PROGRESS** at the sampled review.
2. **Recovered registered READ carrier integrity —**
   `045bcdc4fcb6cb328b881f5ae912c57566505f61` adds import-time
   exact field-slot / constructor / lookup-hook / deny-only descriptor
   checks to `disconnected_recovered_registered_read_join.py`, enforced
   at ingress, across callbacks and before constructing a return receipt.
   `a73d542fc3106c8e5619929a9c0e51d32056943a` adds
   `tests/test_recovered_registered_report_preaccess_run666.py` covering
   malicious preinstalled/reentrant carriers plus original inert receipts.
   [CI #42264423608](https://github.com/Iam-2squared/ark-ai/actions/runs/42264423608)
   was Ubuntu 3/3 GREEN on the source-only HEAD.
3. **Privacy revocation witness custody —**
   `070483ae5448f42e2949cb3fd157fcaf94857927` hardens
   `personal_context_revocation_continuity_review.py` against substituted
   `SyntheticRevocationWitness` slots, constructors and lookup hooks
   **before** reading retained evidence, and rechecks after the hash callback
   **before** new witness construction.
   `31c7965f3c9e136f611ae0cbab410e9c295a750c` adds
   `tests/test_revocation_witness_preaccess_run666.py`, covering
   forged preaccess, reentrant constructor replacement and retained-veto
   continuity. No actual personal data erasure/consent is asserted.

## CI-detected regression and semantics-preserving repair

- [CI #42264539838](https://github.com/Iam-2squared/ark-ai/actions/runs/42264539838)
  on the registered-READ test HEAD produced **Ubuntu Python 3.11 FAIL
  (1 failed, 9911 passed, 1 skipped)**. The new parametrized test
  monkeypatched the report's inherited `__new__` in the **shared pytest
  interpreter**, and Python's allocation slot remained poisoned after
  monkeypatch cleanup: a later valid report failed with
  `object.__new__() takes exactly one argument`.
  Same earlier fixture hazard could affect the privacy test.
- `777522d1c433714d30a3458cd4584791e337be67` and
  `e076531c6fc1e53eae0b1ee5b10e216c503d38bb` remove
  inherited `__new__` mutation from the two in-process parametrizations.
  `d8b1d389f7f565f013333f046a2bb239c6ead461` adds
  `tests/test_run666_inherited_new_subprocess.py`: both malicious
  allocation paths are still tested in **isolated Python child processes**,
  checking static rejection before executing poisoned allocators. No
  production fail-closed validation was removed.
- This test repair was not yet exact-head six-job GREEN at document
  creation. Follow CI [#42265421119](https://github.com/Iam-2squared/ark-ai/actions/runs/42265421119)
  and its six individual jobs; do not infer later HEAD validation from
  earlier Ubuntu passes or a run in progress. No manual duplicate runs.

## Preserved boundaries and limitations

- `main` initially observed at
  `7a843f17eb96ed13d66f23b58b06406b3002e405`;
  neither main nor frozen V1/V2, Local UI or Launcher contracts/evidence
  were modified. PR #5 remains Draft and full training/paid compute/
  Candidate promotion/protected V2 final evaluation are blocked.
- PR #9 remains Draft, unmerged and entirely **untouched**. All new
  UI/frontend implementation and test development remains PAUSED.
- Synthetic local hashes, SQLite and mock process crashes do **not**
  prove writer identity, independent custody, authenticated approval,
  trusted time, real external exactly-once effects or safe retry of an
  ambiguous WRITE. No live ToolBackend, notification, microphone,
  camera, model training, GPU purchase, paid API, new account,
  irreversible operation or unauthorized merge was invoked.
- ARK JARVIS/V3 overall state: **NOT_PASSED**.

## Next plan / 今後の方針

1. Confirm corrected exact HEAD six-job CI; repair any new CI failure
   via the ordinary GitHub Contents path, in a single minimal semantic
   correction, while advancing other independent offline work.
2. Extend independently retained Memory CAS/expiry/ABA/manual
   COMMIT-UNKNOWN evidence without turning local matching content
   into authentication or retry permission.
3. Bind Planner independently verified SUCCEEDED result receipts before
   connecting recovery to registry-bound mock READ execution and
   deny-only, restart-safe WRITE occurrences.
4. Continue Personal Context revocation/retention, proactive recurrence,
   Observation provenance and no-paid V3 approvals in separate reversible
   lanes; retain frozen evaluation, irreversible actions and main merge
   as explicit gates.

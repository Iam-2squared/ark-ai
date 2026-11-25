# Run1437 — local-only V3 attempt and finalization ledger

## Exact basis

- Parent: gated Draft PR #5, branch \`research/v3-learning-evaluation\`.
- Exact parent work-basis HEAD: \`ea373c3496d06e2789cee5bb58836054ef35ed28\`.
- Child branch: \`research/run1437-v3-attempt-finalization-ledger-20261126\`.
- Source: \`src/ark/learning/attempt_ledger.py\`.
- Regression tests: \`tests/v3/test_attempt_ledger_run1437.py\`.

## Work

Adds an isolated SQLite ledger for a future orchestration layer to record one attempt reservation per exact execution-snapshot digest and one optional finalization event.

- A STARTED reservation is committed before any caller-owned work.
- The execution snapshot digest is unique for the lifetime of the ledger; a second attempt cannot silently retry the same snapshot.
- FINALIZED is a one-way append-only event bound to the original execution and authorization-packet digests plus caller-supplied artifact-manifest and evidence-bundle digests.
- Event sequence, hash chain, reservation/event correspondence, schema, foreign keys and SQLite integrity are checked before recovery or state transitions.
- SQLite COMMIT acknowledgement loss raises an explicit unknown-outcome error. A fresh recovery read determines whether STARTED or FINALIZED was committed; the ledger never retries automatically.
- An incomplete STARTED attempt is returned as manual-review-required. No automatic retry, external compute, Candidate generation, protected V2 evaluation or promotion authority is represented.

The module is intentionally **not wired into** \`training_cli\`, \`training.py\`, the HF runtime, or any model/compute path. It is a local persistence primitive only.

## Regression coverage

Synthetic tests cover cold STARTED recovery, duplicate snapshot reservation, one-way finalization, lost COMMIT acknowledgements after both transitions, two-handle reservation races, and event-hash corruption.

## Boundaries and limitations

- Only synthetic local SQLite state and digest strings are used; no model, tokenizer, dataset, GPU, preflight, training, export, Candidate, or V2 evaluation is touched.
- The caller-supplied timestamps are untrusted metadata, not trusted time or chronology proof.
- Supplied authorization, manifest and evidence digests are recorded, not independently authenticated or re-read from their source files by this ledger.
- A successful SQLite COMMIT is not proof of fsync/power-loss durability, independent custody, cross-store atomicity, human approval, or exactly-once external effects.
- Path checks are repeated local metadata preflights, not atomic dirfd custody or protection against a hostile concurrent filesystem writer.
- The one-attempt-per-snapshot rule is intentionally conservative. An interrupted attempt requires manual review; this module exposes no resume/retry API.
- No local pytest/Ruff result is claimed. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.

No frozen Contract 1, dataset, provenance, contamination, experiment recipe, authorization scope, V2 scorer/policy, main branch, PR #8 foundation branch, or UI/frontend work is changed. PR #5 remains Draft/unmerged. PR #9 and Local UI freezes remain untouched. No paid/external compute, credentials, hardware, destructive operation, or potentially billable action occurred.

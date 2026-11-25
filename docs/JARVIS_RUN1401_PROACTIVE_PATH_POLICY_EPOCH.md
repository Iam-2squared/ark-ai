# Run1401 — Proactive SQLite path-policy epoch and reparse-point custody

## Exact basis

- Parent: Draft PR #8, branch \`research/jarvis-foundations\`.
- Exact parent work-basis HEAD when this child branch was created: \`a1bff14b0ca731ee1d094d6611caf76c08640398\`.
- Child branch: \`research/run1421-proactive-path-epoch-20261126\`.
- Child HEAD before this evidence document: \`fde26f9f47beb2f6660e241f8fddff26b62fd2d8\`.
- Source blob: \`66b5da62fc553ba1eb514df57d5b0b3cf9509fd5\`.
- Regression-test blob: \`41dc07696e90c5b4ed8984eb4405bb547c9d2920\`.

## Finding and correction

The shared proactive SQLite path preflight used live \`stat\` predicates, did not reject Windows reparse-point metadata, and did not retain the SQLite sidecar suffix vector as part of one import-time policy epoch. Path callbacks and metadata accessors were not consistently followed by a policy recheck.

The preflight now pins the original \`os.fsencode\`, stat module and mode predicates, path budget, reparse attribute/classifier and exact sidecar suffix tuple in a keyword-only verifier default. It uses retained predicates and rechecks the epoch after \`lstat\`, metadata access, path encoding and sidecar construction. Reparse-point parents, database files and sidecars are denied before SQLite open. The existing one-retry rule for an already-unlinked regular sidecar is preserved.

Both the synthetic trigger ledger and proactive state ledger continue to use this shared path preflight.

## Regression coverage

- Joint replacement of stat aliases, reparse helper and sidecar vector is rejected before \`Path.lstat\`.
- Equal-valued but newly allocated sidecar suffix tuples are rejected.
- A reentrant \`lstat\` replacement is rejected before \`st_mode\` access.
- Synthetic reparse-point metadata is rejected for parent, main database and sidecar paths.
- A reentrant \`st_file_attributes\` accessor cannot restore a changed path policy.
- An already-unlinked regular sidecar receives only its existing single bounded recheck.
- Healthy synthetic trigger and proactive state ledgers still create and read empty local stores.

## Scope and evidence limits

This changes only local path-admission checks. Trigger/state DDL, row formats, policy digests, occurrence identity, CAS semantics, retention, scheduler decisions and public APIs are unchanged. The ledgers remain synthetic and deny-only: no timer, notification, consent, trusted clock, tool dispatch or external action is authorized.

Pathname preflight is not atomic \`dirfd\` custody, process isolation, authenticated storage identity or protection against owner-controlled concurrent rename/current-directory changes. No real user data, notification, hardware, credentials, paid/external compute, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, main write/merge or UI/frontend work occurred. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. Fresh exact-head CI is required; no PASS is claimed.

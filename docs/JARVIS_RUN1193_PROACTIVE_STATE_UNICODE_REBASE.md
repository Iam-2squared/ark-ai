# Run1193 — Proactive state Unicode format-control admission rebase

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD at branch creation: `2df6b261554428cd01871f2723ce87c4dd05e4b4`.
- Reconciled source: Draft PR #372 exact child HEAD `289b1a0757f61cbb090b77b522f05a908dc8560c`.
- New child branch: `research/run1193-proactive-state-unicode-rebase`.

## Change

The durable proactive eligibility-state policy identity validator pins the import-time `unicodedata` module and exact category function, checks dependency identity before scanning and after scanning, and rejects every Unicode General Category `Cf` character in owner, namespace, definition ID and policy revision. Existing C0/C1, NUL, bidi, separator/default-ignorable, exact-string and UTF-8 byte-budget behavior remains unchanged.

This rebase intentionally retains the stronger post-scan dependency check from PR #372. The overlapping proactive-state hunk in PR #362 is not copied; PR #376 separately retains its Personal Context and Observation fixture changes.

## Regression coverage

Synthetic tests cover all four identity fields × U+0600/U+FFF9/U+E0001, positive Japanese identity text, and module-substitution denial before the replacement category callback receives caller text during construction and later identity derivation.

## Limits

No real scheduler, notification, consent, trusted clock, Tool, dispatch, replay or external-action authority is added. Proactive SQLite schema/state transitions/CAS and frozen contracts remain unchanged. No live personal data, paid/external compute, paid service, Candidate, protected V2 evaluation, UI/frontend work, credentials, physical hardware, destructive action or main merge is involved.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. ARK/JARVIS remains NOT_PASSED.

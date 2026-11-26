# Run1188 — Proactive state Unicode format-control admission

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `c1b7b3d2dfe38242fcbe3d6d4930c3bbf53e9390`.
- New isolated child branch: `research/run1188-proactive-state-unicode-controls`.

## Finding and change

The durable proactive eligibility-state policy validator used a manually enumerated Unicode formatting-control list. It rejected several known C0/C1, bidi, separator and default-ignorable characters but did not reject every Unicode General Category `Cf` scalar. The owner, namespace, definition ID and policy revision therefore had an incomplete identity-admission boundary.

The validator now pins the import-time `unicodedata` module and exact `category` function in the existing protocol-integrity guard. It checks that dependency before scanning and again after scanning, rejects every `Cf` character, and preserves all existing NUL/control checks, exact-string rules and UTF-8 byte limits.

## Regression coverage

- All four policy identity fields are tested against U+0600, U+FFF9 and U+E0001.
- Ordinary Japanese identity text remains accepted.
- Module substitution is denied before the replacement category callback receives caller text, both during construction and later identity derivation.

## Limits

This is local synthetic policy-identity validation only. It adds no real scheduler, notification, consent, trusted-clock, Tool, dispatch, replay or external-action authority. The proactive state SQLite schema, state transitions, CAS behavior and frozen contracts are unchanged. No live personal data, paid/external compute, paid service, Candidate, protected V2 evaluation, UI/frontend work, credentials, physical hardware, destructive action or main merge is involved.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff result is claimed. ARK/JARVIS remains NOT_PASSED.

# Run1178 — Complete Unicode format-control admission

**Status:** implementation saved on an isolated Draft branch; exact-head CI is pending. No PASS is claimed.

## Exact basis and scope

- Parent work-basis HEAD: `a27344061d5abc5304c44c03f7457005deb4c89d` (Draft PR #8, `research/jarvis-foundations`).
- Child branch: `research/run1178-complete-unicode-format-admission`.
- This package is limited to optional, local-only privacy metadata boundaries. It does not change Memory v1, Observation Envelope v1, ToolCall v1, or any frozen evaluation contract.

## Finding

Three opt-in boundaries used manually enumerated Unicode formatting code points:

- Personal Context `ContextSelectionPolicy.policy_revision`;
- proactive policy owner / namespace / definition / revision identifiers;
- disconnected Observation fixture adapter source and privacy labels.

The lists covered common bidi, zero-width and C1 controls but did not cover every character whose Unicode General Category is `Cf`. In particular, Arabic Number Sign (`U+0600`), Interlinear Annotation Anchor (`U+FFF9`) and Language Tag (`U+E0001`) were not admitted by those lists.

## Change

- Pin the import-time `unicodedata` module and exact `category` function at each boundary.
- Reject every character for which the pinned classifier returns `Cf`, while preserving the existing C0/C1, bidi, separator, NUL, UTF-8 and size checks.
- Recheck classifier identity after admission in Personal Context and Observation; include it in the proactive protocol identity guard.
- Keep Observation Envelope v1 itself unchanged; only the disconnected fixture adapter is tightened.
- Add synthetic tests for all three omitted `Cf` examples, each applicable identity field, dependency substitution, and denial before private fixture hashing.

## Validation and evidence limits

- Local pytest/Ruff has not been run in this environment.
- Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required after the Draft PR is created.
- Tests use synthetic strings and in-memory fixture values only. No live observation capture, private Memory snapshot, external disclosure, consent, notification, Tool dispatch, trusted clock, or authenticated provenance is exercised.
- Unicode category pinning is an in-process dependency-integrity check, not a Python sandbox or a claim of independent runtime custody.
- No paid/external compute, paid API/service, Candidate, protected V2 evaluation, credentials, physical hardware, destructive operation, frozen-contract change, UI work or main merge is involved.

**ARK/JARVIS remains NOT_PASSED.**

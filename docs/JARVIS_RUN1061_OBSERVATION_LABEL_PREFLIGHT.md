# Run1061 — disconnected observation label preflight budget

## Exact work basis

- Parent: Draft PR #8, branch research/jarvis-foundations.
- Exact parent HEAD: 3a143ed8ccc6b128829a9958493eae2d9462c392 (after the Run1059 revocation assertion integration).
- Child branch: research/run1061-observation-label-preflight.
- Scope: the opt-in disconnected synthetic fixture adapter only.

## Gap

The adapter checked NUL, ASCII controls and Unicode formatting controls before the frozen envelope constructor enforced its identifier byte budget. A very large exact string could therefore trigger multiple full scans before the bounded envelope preflight rejected it. A 257-code-point emoji label also exceeded the 1,024-byte UTF-8 budget while remaining below 1,024 code points, so the byte limit was not established before those scans.

## Change

- Require exact built-in strings at the fixture boundary.
- Reject labels over 1,024 code points before any control scan.
- Strictly encode the now-bounded label and reject UTF-8 representations over 1,024 bytes before any control scan or payload hashing.
- Preserve the later NUL/control/formatting checks and the frozen public ObservationEnvelope v1 constructor unchanged.

## Regression coverage

Synthetic tests cover oversized ASCII and UTF-8 labels in both source and privacy fields. The test replaces the adapter's control-scan lookup with a failing sentinel to prove the over-budget path exits before scanning. A 1,024-byte multilingual label remains accepted and the returned envelope remains digest-only.

## Limits and safety

Only synthetic in-memory bytes and labels are used. No real camera, microphone, screen, file, network, live personal data, consent, trusted clock, ToolBackend or external effect is involved. This is bounded local fixture admission, not provenance authentication or a production capture adapter. No frozen contract, paid service, external compute, Candidate, protected V2 evaluation, main branch or UI is changed.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed.

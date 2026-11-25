# Run990 — Action Audit outcome boundary

**Exact work basis:** Draft PR #8 branch `research/jarvis-foundations`, HEAD `af7beebaf8246ec03b5e311aac34befac91c26a4`.

**Rebased child branch:** `research/run1347-action-audit-outcome-regressions-20261125`, proposed as a Draft child of PR #8. The production outcome-bound implementation is already present in the exact parent source; this package adds only the missing synthetic regression module and its evidence note.

## Change

The v1 Action Audit accepted any non-empty outcome string and hydrated persisted TEXT without a byte ceiling. This package keeps the existing open outcome vocabulary but bounds labels to 256 code points and 256 UTF-8 bytes, and rejects C0/C1, bidi, line/paragraph separators, and every Unicode `Cf` format character (not only a hand-picked subset). The Unicode category dependency is identity-pinned before caller text is processed.

- Caller-provided invalid outcomes retain the existing `ValueError` surface and are rejected before opening SQLite or sampling the audit clock.
- Persisted oversized outcome TEXT is rejected in SQLite-side byte preflight before Python row hydration.
- Persisted control/format characters fail closed during historical-prefix and event-read validation.
- Corrupt rows are never repaired; append is refused before clock sampling.
- A valid 256-byte UTF-8 label round-trips.

## Synthetic regression coverage

The new test module covers empty/whitespace, code-point and UTF-8 byte overflow, newline/C1/bidi controls, Arabic format marks, interlinear annotation controls, supplementary-plane language tags, a substituted Unicode category dependency, lone surrogate, wrong exact types, pre-SQLite/pre-clock rejection, valid UTF-8 boundary, and persisted-row rejection without mutation.

All cases use temporary SQLite and synthetic ToolCalls. No real backend, tool dispatch, personal data, paid service, external compute, or Candidate operation is involved.

## Scope and limitations

The Action Audit v1 schema and public event fields remain unchanged. This is local input/resource-integrity hardening only; it does not add an authenticated event chain, independent custody, trusted time, consent, cross-store atomicity, or proof of an external effect. The separate v1-to-v2 migration plan remains unimplemented and unchanged.

**Rebased validation:** the predecessor source branch's exact-head CI run `44518002802` was GREEN 6/6, but its old-base result does not transfer. This rebased test-only child requires fresh exact-head CI; no PASS claim is made.

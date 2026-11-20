# Run990 — Action Audit outcome boundary

**Work basis:** Draft PR #8 checkpoint HEAD `dda7c191546a348a606b31f7f0f4287de8f64183`.

**Isolated branch:** `research/action-audit-outcome-bounds-run990`, proposed as a Draft child of `research/jarvis-foundations`. This package does not modify PR #8, PR #5, or the paused UI branch.

## Change

The v1 Action Audit accepted any non-empty outcome string and hydrated persisted TEXT without a byte ceiling. This package keeps the existing open outcome vocabulary but bounds labels to 256 code points and 256 UTF-8 bytes, and rejects C0/C1, bidi, and Unicode formatting controls.

- Caller-provided invalid outcomes retain the existing `ValueError` surface and are rejected before opening SQLite or sampling the audit clock.
- Persisted oversized outcome TEXT is rejected in SQLite-side byte preflight before Python row hydration.
- Persisted control/format characters fail closed during historical-prefix and event-read validation.
- Corrupt rows are never repaired; append is refused before clock sampling.
- A valid 256-byte UTF-8 label round-trips.

## Synthetic regression coverage

The new test module covers empty/whitespace, code-point and UTF-8 byte overflow, newline/C1/bidi controls, lone surrogate, wrong exact types, pre-SQLite/pre-clock rejection, valid UTF-8 boundary, and persisted-row rejection without mutation.

All cases use temporary SQLite and synthetic ToolCalls. No real backend, tool dispatch, personal data, paid service, external compute, or Candidate operation is involved.

## Scope and limitations

The Action Audit v1 schema and public event fields remain unchanged. This is local input/resource-integrity hardening only; it does not add an authenticated event chain, independent custody, trusted time, consent, cross-store atomicity, or proof of an external effect. The separate v1-to-v2 migration plan remains unimplemented and unchanged.

**CI status:** pending the new Draft PR's exact-head workflow; no PASS claim is made in this report.

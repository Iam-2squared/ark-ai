# Run1300 — core guard-custody regression bundle

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent basis at branch creation: `8f3b7c528a63110d9085ac9dfefcacd4c405a9f4`.
- The parent basis differs from the preceding tested foundation `467cfbd1d0f21bc9d70c99d0cb5ccc6ecd042573` by one documentation-only update to `docs/PROJECT_STATUS_CURRENT.md`; no production source changed in that interval.
- This branch is a test/documentation-only consolidation of the four previously isolated regression children #476–#479. Their prior exact-head CI runs were GREEN, but those results do not transfer to this new parent basis.

## Regression coverage

1. **Disconnected mock executor / ActionAudit COMMIT hard exit** — after the native pre-action audit transaction commits, a spawned process exits before append returns. Cold recovery must retain one occurrence reservation and one `mock_pre_action` event, show no completion event, deny same-token/different-occurrence retry before token consumption, and never call the mock backend.
2. **ToolRegistry assignment seal** — ordinary writes to sealed state slots are refused; a substituted class-level `__setattr__` guard is rejected before registry reads or backend dispatch.
3. **PermissionGate assignment seal** — ordinary writes to sealed state slots are refused; a substituted class-level `__setattr__` guard is rejected before authorization input inspection or token consumption.
4. **ActionAudit assignment-guard identity** — a substituted class-level `__setattr__` guard is rejected before SQLite connection or caller-clock access.

## Scope and evidence boundary

- Test-only; no production source, schema, DDL, public API, ToolCall/PermissionGate contract, or frozen contract changes.
- Synthetic ToolCalls, temporary local SQLite databases, and inert/disconnected mock backends only. No real backend dispatch, credentials, personal data, device capture, or physical hardware.
- These tests do not establish trusted time, authenticated consent, process isolation, independent audit custody, fsync/power-loss durability, cross-store atomicity, or exactly-once external effects.
- Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required before this package can be integrated into Draft PR #8. No PASS is claimed here.
- No paid/external compute, Candidate adapter/weight generation or promotion, protected V2 evaluation, frozen-contract change, main merge, or UI/frontend work. PR #5 remains gated; PR #8 remains Draft/unmerged; PR #9 remains untouched; main remains read-only under the existing recovery boundary.

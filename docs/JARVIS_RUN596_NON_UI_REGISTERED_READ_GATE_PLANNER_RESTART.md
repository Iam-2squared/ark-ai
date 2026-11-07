# ARK AI — Run596: registered READ policy custody and mixed Planner restart

Scope: **Draft PR #8, non-UI, free-only, disconnected fixtures**. This is
implementation evidence and a future integration gate, **not** a modification
of frozen contracts, an approval to run tools, or a JARVIS/V3 PASS.

## Package A — gate identity in registered READ preflight

- Code: `src/ark/agency/disconnected_registered_read_preflight.py`
  (first implementation commit `3193b3d9187d6461a375c5c2734eb8a0ab7b0711`;
  import-order-only repair `4ad07224c31b37dc71573aa12b1775e422f8a1b7`).
- The READ-only preflight previously called `gate.authorize_registered`
  through mutable instance/class lookup, accepting a forged `BoundAction` with
  matching values even when grants were not checked. Its disconnected report
  was not itself execution authority, but this invalidated the asserted
  policy-decision provenance.
- The import-time `PermissionGate.authorize_registered` descriptor is now
  pinned. Class-level and instance-level replacements are rejected using
  `inspect.getattr_static` before registry binding, immediately after the
  binding callback, before/after policy evaluation and at the end of report
  verification. False-looking return objects are not sufficient evidence of
  a real policy check.
- Regression: `tests/test_registered_read_gate_original_method_run596.py`
  (7 parameter-expanded cases; authored, not claimed locally passing).
  Tests cover class/instance forged and delegated results, mutation through
  registry callback, and normal non-dispatch READ behavior.
- This is **process-local implementation custody**, not signed code,
  restart-safe permission, independent grant provenance, or an authentication
  mechanism. No `ToolBackend.execute` call is added.

## Package B — mixed durable Planner restart invariant

- Regression: `tests/test_planner_mixed_terminal_restart_run596.py`
  (4 parameter-expanded cases; authored, not locally verified).
- A failing/cancelled/blocked branch must preserve descendant `BLOCKED`
  states; an unrelated `RUNNING` branch remains an ambiguous outstanding
  execution. Reopening the SQLite journal with a retained exact tail must
  preserve both distinctions and keep dispatch/replay flags False.
- Independent completion must not resolve an unrelated RUNNING state. The
  test suite exercises a non-retryable second RUNNING transition, without
  ever executing a backend.
- A retained tail is caller-held local evidence; neither it nor SQLite
  authenticates a prior external effect or proves cross-store atomicity.

## CI and integration ordering

- Before these edits, PR #8 checkpoint
  `b78f7c928d04af88a8f6c56c2ba85cd00a5c0136`
  had **all six Python 3.11–3.13 Ubuntu/Windows jobs GREEN** in
  [CI #41757258526](https://github.com/Iam-2squared/ark-ai/actions/runs/41757258526).
- The first source-only CI
  [#41762817425](https://github.com/Iam-2squared/ark-ai/actions/runs/41762817425)
  failed all six jobs due solely to the **Ruff I001 import order** at
  `disconnected_registered_read_preflight.py:11`, repaired without changing
  authorization semantics at `4ad07224...`.
- CI for later source + tests requires **independent exact-head confirmation**
  in the canonical checkpoint. Authored test counts are not pass counts.
- The two packages are independent: a registered READ preflight change
  does not claim Planner journal authorization; Planner tests do not make
  `RUNNING` safe to replay.

### Unclosed integration gates (keep WRITE execution disabled)

1. Authenticated local approval/consent issuer and explicit revocation/expiry
   proof; caller-supplied `CapabilityGrant` and synthetic clocks are not enough.
2. Durable exactly-once token/occurrence claim and trusted-clock
   audit-*before*-action binding, with recovery that quarantines UNKNOWN.
3. A verified atomic or explicitly uncertainty-preserving cross-store
   recovery policy; independent SQLite transactions cannot prove a unified
   transaction or actual external action.
4. Independent non-app-controlled evidence custody, startup readiness, and
   exact-head multi-platform tests before any production backend connection.

No paid/potentially billable services, external GPU, Candidate generation,
protected V2 final evaluation, real ToolBackend call, main merge, UI change,
new credentials or destructive action is authorized or performed. PR #5,
PR #8 and UI-paused PR #9 remain Draft/unmerged. ARK/JARVIS/V3 NOT_PASSED.

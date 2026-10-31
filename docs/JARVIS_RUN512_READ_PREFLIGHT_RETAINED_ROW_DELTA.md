# ARK Run512 — Inert Registry READ Preflight + Retained Memory Row Delta

> **Run512 test-correction addendum (after original evidence):** The original evidence below was pinned at source/test HEAD `805990eb2d22e9461cf321d4b79ea2f69c118894`. Its Ubuntu pytest completed with **2 failed, 5828 passed, 1 skipped** because two new tests expected the generic word `denied` while the guard deliberately raised the more precise `registered READ binding changed` and `preflight input identity changed`. The normal test-only Contents API correction changed only those expectations. The corrected exact source/test HEAD is `6e3c0291ef46fe506336b708a525ab222333834b`; test file blob is `c3ba56748d6204f91a262f5919c1f9f0de5cca58`; source blob remains `29e67ce597cbe7414c5d48c5548197ba743800de`. Corrected CI [41241156470](https://github.com/Iam-2squared/ark-ai/actions/runs/41241156470): **3/6 GREEN, 3 in progress at addendum preparation**. Do not construe this as completed six-job evidence unless separately verified. Total new authored pytest cases: **36** (registered READ 19, retained Memory row delta 17). No authority denial was weakened.\n\n## Scope, branches, and exact source/test basis

- Repository: `Iam-2squared/ark-ai`; work branch `research/jarvis-foundations` / Draft PR #8; initial work-basis HEAD `00ff7e5551424d44025d1f8745fffa98303bea9d`.
- Final source/test HEAD at creation of this evidence: `805990eb2d22e9461cf321d4b79ea2f69c118894`. Any later evidence/checkpoint commits are distinct GitHub HEADs and must not be conflated with this tested source.
- V3 Draft PR #5 remains at `20781a6c752a00a406b2543d621fe29062d1a982`, unchanged. Main stays `7a843f17eb96ed13d66f23b58b06406b3002e405`.
- Contracts remain frozen: Agency `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`, Memory `b6e93821ecd69270a7634aceb20775dc36e9953c`, V3 `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`.

## Package A — immutable registry + exact-scope policy, READ-only, zero dispatch

- `src/ark/agency/disconnected_registered_read_preflight.py` blob `29e67ce597cbe7414c5d48c5548197ba743800de`.
- `tests/test_disconnected_registered_read_preflight_run512.py` blob `fef53adbc0a2762ea47817e92566b5beac084b44`.
- Bridges existing immutable `ToolRegistry.bind` and `PermissionGate.authorize_registered` for **READ registrations only**. A WRITE is rejected **before entering PermissionGate**, so it cannot consume a one-shot token. No registered ToolBackend is called, no filesystem/network action is dispatched, and no external READ is authorized by the inert diagnostic.
- Inputs require exact `ToolRegistry`, `PermissionGate`, `ToolCall`, bounded exact tuple of `CapabilityGrant`, and exact synthetic `now_ms`. Capture original action/grant carriers across registry and policy callbacks; compare the registry revision, bound action ID, request ID, registered name/capability and effect before building the denial-only report.
- Test classes cover true READ binding, repeatability, no backend calls or token spending, WRITE-before-gate rejection, exact grant/scope/capability/expiry mismatch, forged tools, excessive grants, invalid synthetic clock, altered grants during policy callbacks, substituted policy return, frozen report, and equal-value-but-different original action scope identity.
- The synthetic `now_ms` is **not a trusted clock**; a successful diagnostic is **not durable authorization, real consent, external effect, trusted backend attestation, or permission to connect a real executor**.

## Package B — prior row commitments survive unrelated append

- `src/ark/memory/sqlite_retained_row_delta_review.py` blob `3387c3bf28bbe97c0819e746525a6921b0515eb9`.
- `tests/test_memory_retained_row_delta_run512.py` blob `7272f8452ec370a823d1667b447855c3440fe1e7`.
- The new **read-only one-transaction** capture/review preserves per-row domain-separated SHA-256 commitments (ID, revision, content SHA, metadata SHA, scope, source and timestamp/expiry) alongside the original event-prefix commitment. The private content is never emitted in a witness or report.
- After a valid append to a *different* memory, the reviewer still detects a silent content+checksum rewrite, metadata/expiry/revision rewrite, or disappearance of the prior row without that row having its own appended event. Historical event-prefix changes and rollback are rejected. Valid new-row create, update and delete transitions are treated only as **locally explained row differences**.
- Added fixtures cover empty/unchanged snapshots, new rows, own update/delete, four categories of unrelated-tail hidden changes, missing row, event-prefix mutation/rollback, retained witness shape and callback retargeting, read-only SQL invariance, changed schema, and a WAL writer interleaved after row sampling.
- **Limitations:** the baseline witness is caller retained, not independently signed or authenticated; an attacker controlling both the witness and database can fabricate consistency. A new event with the same memory ID is *not* a cryptographic proof of a legitimate prior write or content. This row-delta review is a supplemental audit, **not** a replacement for the full Memory lifecycle/row alignment reviewer, nor a cross-store snapshot, consent/erasure proof or Memory disclosure authorization.

## CI chronology and evidence semantics

- Earlier canonical Run511 checkpoint: CI [41236823096](https://github.com/Iam-2squared/ark-ai/actions/runs/41236823096), six jobs SUCCESS, predecessor only.
- Run512 initial test head `3b69933f6257c68ecc2ad3fe0993c782ae5a09cf`: CI [41240458435](https://github.com/Iam-2squared/ark-ai/actions/runs/41240458435) FAIL due to Ruff import ordering. Normal Contents API test correction at `9ab1a0400338df5c9ccc803c38729f1c81ba2214`.
- After the first pass, Ubuntu pytest identified expected-message mismatch on WRITE denial, a frozen-slots assignment raising `TypeError`, and a Memory schema error escaping the local reviewer exception type. Implemented proper WRITE rejection classification, accepted both frozen-slot denial exception kinds, normalized schema rejection, and added a regression for equal-valued action scope replacement. No permission or provenance condition was relaxed.
- The intermediate `4361f9e701d51279483d17bc6712ad7a851ef963` and `3b6e2026fcc56aba074cd68f8630de59a60c1a82` CI surfaced a Ruff `E714` from an incorrectly composed boolean guard expression. Corrected that expression while retaining **all-field identity checks** at `805990eb2d22e9461cf321d4b79ea2f69c118894`.
- **Latest source/test CI:** [41240963739](https://github.com/Iam-2squared/ark-ai/actions/runs/41240963739), exact `805990eb2d22e9461cf321d4b79ea2f69c118894`, **IN PROGRESS at evidence preparation**; six-job GREEN is NOT asserted.
- The newly authored cases are declarations, **not evidence of a separate local pytest/Ruff pass**. Local container cannot resolve GitHub DNS to fetch a checkout. All allowed writes used GitHub's normal Contents API; no raw-object/ref bypass, force push, main merge or protected evaluation.

## Hard stops and next integration

No GPU or billable services, model download, Candidate training/adapter/weight generation, V2 protected final-evaluation opening, Candidate promotion, new identity/consent claim, external ToolBackend/OS dispatch, unknown WRITE replay, irreversible operation, or main merge. Both PRs remain Draft/unmerged. ARK/JARVIS overall **NOT_PASSED**.

1. Confirm exact-head [41240963739](https://github.com/Iam-2squared/ark-ai/actions/runs/41240963739) matrix; repair only verified failures, otherwise preserve GREEN evidence.
2. Before any connected scheduler or planner pathway, demand verified registry/policy READ-only invariants and trusted-clock/audit-before-action design. No WRITE execution from this diagnostic.
3. Extend Memory supplemental row-delta review with rigorous lifecycle/scope causality and independently retained witness custody, keeping the full coherent reviewer authoritative for current row/event structure.
4. Keep V3 offline guard work isolated and free-only; all frozen evaluation, human-approval, budget and compute boundaries remain closed.

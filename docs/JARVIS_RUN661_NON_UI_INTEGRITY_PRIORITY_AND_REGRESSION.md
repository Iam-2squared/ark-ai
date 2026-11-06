# Run661 — Non-UI integrity regression packages and execution-gate review

Date: 2026-11-06 JST. **Draft PR #8**, local-first, synthetic-only. No UI work, paid service, live backend, Candidate generation, protected V2 evaluation or main merge.

## Work basis and source authority

- Work-basis HEAD: `957777328de7daf339d802ca715bde1a0e8030ec`. Its exact-head [CI #42213164435](https://github.com/Iam-2squared/ark-ai/actions/runs/42213164435) completed **six of six GREEN** (Windows/Ubuntu, Python 3.11/3.12/3.13).
- Read actual PR #8 source before adding tests: `src/ark/agency/durable_occurrence_review.py`, `src/ark/agency/disconnected_write_recovery_fence.py`, `src/ark/offline_context_redaction.py` and `src/ark/memory/generation_fenced_cas.py`. These are non-UI modules on the same branch. All new tests use disposable fixtures or pure detached claims.
- Files were saved separately through ordinary GitHub Contents writes after PR-head re-read. Existing frozen V1/V2/Local UI/Launcher contracts, PR #5, PR #9 and main remain unchanged.

## NEW packages

1. **Synthetic occurrence row integrity and token expiry (8 authored cases).** `tests/test_registry_synthetic_row_and_expired_token_run661.py` at commit `551f9f90136457a08c3aa91297c486a04e55c9cd`. Seven parameterized malformed SQLite row fields (digest, occurrence, registry revision, bound-action ID, request ID, and inconsistent clock relations) must fail reopen, count, and fresh reservation without allocating a second row. A changed registry with a later expiry must not recycle the same already reserved token identifier. Backend call counter must stay zero.
2. **Mixed recovery DAG terminal precedence (7 authored cases).** `tests/test_disconnected_mixed_dag_terminal_precedence_run661.py` at `53f67976df30f9821f205e7f8fb84df1ae207177`. Four 9-step claim combinations distinguish terminal and unknown ancestor propagation, held WRITE, quarantined reservations, and independent `READY_MOCK_ONLY` READ. Three re-used reservation cases must reject duplicate WRITE occurrence ownership even in inert plans.
3. **Unicode span coverage and partial-data custody (8 authored cases).** `tests/test_offline_redaction_boundary_disclosure_run661.py` at `a64e8c6923afb72a8db112cf0c7b41cc439d3074`. Unicode codepoint splits of emoji/combining/zero-width fixtures remain completely masked and non-exportable. Three uncovered/overlapping spans are rejected in complete mode. Partial mode explicitly demonstrates that local preview can reveal a tail without gaining consent, erasure or export authority.
4. **Disjoint Memory event sequence vs target lifetime CAS (3 authored cases).** `tests/test_memory_disjoint_global_event_cas_run661.py` at `0c60662cc6eb06969ace5751ec2838edc7e38a69`. A separate handle appends to another owner, another namespace or another source in the same scope. A retained target token must still recognize its unchanged target lifetime, then a later generation-fenced local update must advance the target while retaining both independent history and global event high-water.

**Total: 26 authored test cases, not independently confirmed passes.** These are added coverage of existing code paths, not a claim of new live integration. The three initial source/test CI runs #42220601798, #42220652153, #42220717831 were seen IN PROGRESS after their commits; the fourth follows its own HEAD. The latest 6/6 GREEN is **not yet established** at document-writing time. Do not treat an earlier HEAD's CI as validation of later tests.

## Source-grounded hard boundaries and next dependency order

- `SyntheticOccurrenceStore` rejects malformed local row syntax and duplicate token/occurrence. It **does not** prove signatures, authentic issuers, human review, true clock, filesystem integrity against a capable attacker, or exactly-once remote effects. Syntactically canonical replacement rows are not independently authenticated.
- `review_disconnected_recovery_fence` receives **untrusted** caller state claims. `READY_MOCK_ONLY` is a classification, never dispatch permission; unresolved WRITE stays quarantined. An external driver must not silently turn these labels into capabilities.
- `preview_offline_redaction` requires a caller-retained hash and caller-declared spans. Full mask is not anonymization, independently authenticated consent, privacy erasure, or permission to export. Partial previews may contain unmasked text and must remain local.
- `generation_fenced_memory_update` is an opt-in local SQLite mutation with begin-immediate CAS, row/event/readback checks. Its token is not a capability; any ambiguous post-COMMIT outcome remains **UNKNOWN/manual-only**, never an automatic retry. Global append epochs and per-row generations are separate invariants.
- Next: confirm all exact-head CI jobs, fix only observed failures without loosening semantic gates; advance Memory COMMIT-UNKNOWN/expiry/ABA and Planner durable terminal recovery; then integrate registry-bound exact PermissionGate, durable occurrence, audit-before-action and disconnected mock-only executor **only after prerequisite exact-head GREEN**. Parallel free lanes: Personal Context revocation, proactive readiness, observation fixture adapters and V3 local-only identity/path/approval validation.
- Stop boundaries: new credentials/accounts, paid/external compute or GPUs, real Candidate artifacts, protected V2 opening, main merge requiring approval, destructive changes, unreviewed trust/consent assumptions, frozen-contract edits, physical target PC actions. PR #5/#8/#9 must remain Draft/unmerged; UI development paused.

No external effects, physical device, notification, live ToolBackend or training were exercised. Local fixture hashes and synthetic evidence are not real authorizations.

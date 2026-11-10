# ARK AI — Run769 NON-UI Core / Registry CI Correction, Atomic WAL Alignment, Context Receipt Constructor Custody

**Scope:** FREE-ONLY, offline synthetic/read-only and SQLite mock fixtures, no UI. Work-basis Run768 checkpoint HEAD `76e94a66b2298b19bfb0e3e92aa8ce20f215909b`; Draft PR #8 `research/jarvis-foundations`. This report is evidence of code changes and observed CI only, **not** authentication, independent custody, external-tool permission, or completed JARVIS.

## A — CI failure analyzed and minimally repaired

At Run768 source/test HEAD `816df19af91dc0bf733969e7a38e0fc72a7415f4`, workflow [#42851457266](https://github.com/Iam-2squared/ark-ai/actions/runs/42851457266) yielded Ubuntu **3/3 FAIL**, each with **1 failed / 12,645 passed / 1 skipped**. Job logs specifically identified `tests/test_registry_nul_identity_run768.py::test_unicode_registry_identity_remains_stable_and_never_executes`: `registry.resolve(item.name)` passed a string, while the established immutable `ToolRegistry.resolve` contract requires exact `ToolCall`. **No production contract was changed.**

Commit `1e7deaf8ba4eafbe69136c7b6d29ae4c052d1a22` changed that test to construct `ToolCall(item.name, item.capability, "fixture.local", {})` and call `registry.resolve(call)`. The Unicode revision and backend non-execution assertions remain. Previous checkpoint CI [#42852239724](https://github.com/Iam-2squared/ark-ai/actions/runs/42852239724) also showed Ubuntu failures on its older HEAD; neither obsolete failure constitutes post-fix evidence.

## B — Atomic pre-action intent/audit SQLite integrity

Commit `bda2cd87a22c8190924956a9121dc7e350b72478` added `tests/test_atomic_preaction_wal_alignment_run769.py`: **5** parameterized cases. An uncommitted conflicting intent row remains invisible to a read-only consistent WAL snapshot; mutations to audit digest, deletion, and mismatched replacement audit sequence are rejected; unknown schema user_version rejects further reserve without introducing a new row. These use only local SQLite and synthetic identifiers. They cannot attest effect delivery or provide a replay grant.

## C — Personal Context replay receipt constructor custody

Commit `d823291dedebaeb3900129fd4239eb87185119a0` modified only non-frozen `src/ark/personal_context_replay_ledger.py`: retained import-time exact `OfflineContextReplayReceipt` constructor, slot, and denial-property identities, and validated them immediately before/after constructing the post-COMMIT return receipt. A forged constructor or slotted field is refused **without executing attacker-supplied constructor/getter code**. A local SQLite COMMIT is never represented as rolled back when receipt construction is rejected; caller must reconcile and must not retry blindly.

Commit `2b33b2543b8103854898a5cd6df698fd3b9615b3` added `tests/test_context_replay_receipt_constructor_run769.py`: **6** parameterized cases (replaced receipt class, initializer, request slot, witness slot, denial getter, and positive original receipt). The negative checks require zero injected callback executions, a persisted local reservation, stale genesis witness refusal, and no new permission. Existing receipt-last-getter reentrant tests are left unchanged; no read-only recovery or live disclosure path is enabled.

## CI evidence / limitations at report creation

- [Run767 basis #42839474821](https://github.com/Iam-2squared/ark-ai/actions/runs/42839474821) at `83e4658d...`: **6/6 GREEN**; NOT evidence for Run768/769.
- [Run768 obsolete #42851457266](https://github.com/Iam-2squared/ark-ai/actions/runs/42851457266) at `816df19...`: Ubuntu 3/3 FAIL due exact-ToolCall regression test misuse (fixed above).
- [Run768 checkpoint #42852239724](https://github.com/Iam-2squared/ark-ai/actions/runs/42852239724): Ubuntu 3/3 FAIL at earlier snapshot; Windows outstanding at last check.
- [Atomic package CI #42853532414](https://github.com/Iam-2squared/ark-ai/actions/runs/42853532414) at `bda2cd87...`: **6/6 IN PROGRESS** at last inspection.
- **Latest `2b33b254...` 6/6 GREEN NOT VERIFIED.** GitHub Actions may queue/merge PR refs; do not reuse another SHA's result. No duplicate workflow manually launched. Local full pytest unavailable in this execution environment; no local PASS is claimed.

## Frozen contracts and hard blockers

Draft PR #5 remains gated and unmerged. Draft PR #9 remains paused, untouched and unmerged. Frozen V1/V2/Local UI/Launcher/ObservationEnvelope v1 contracts, evidence and protected final evaluation remain unchanged; no frontend code, UI features, or frontend tests. `main` remains unmodified. No paid services, external/GPU compute, Candidate weights, new credentials, tool WRITE, network disclosure, notification, physical PC actions, protected evaluation opening, human-approval fabrication, irreversible operation, automatic promotion/replay or main merge.

Remaining limits: a local digest chain or class-level monkeypatch check cannot prove original runtime custody, independent audit, trusted clock, signed consent, privacy policy, cross-store atomicity or exactly-once external effects. A committed-but-response-unknown actual WRITE stays quarantined for manual review.

## Next

1. Confirm exact-head Windows/Ubuntu 3.11–3.13 CI. If failures, inspect the **new** job logs, fix ordinary source/test files without touching protected contracts, and keep an independent lane running while CI executes.
2. Extend Memory CAS/ABA retained high-water and multi-scope COMMIT-UNKNOWN; preserve identity versus identical-byte ambiguity.
3. Extend Planner persisted terminal-state reconstruction and registry-bound exact PermissionGate + audit-before-action mock Executor only after matching exact-head lower-level GREEN.
4. Continue privacy-safe Personal Context revocation/expiry, proactive trusted-clock startup, observation fixture adapters, and free-only V3 path/approval/identity guards, all isolated. Obtain explicit user authority only at a genuinely protected or paid boundary.

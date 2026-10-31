# ARK AI — Canonical Project Status

**LATEST — 2026-10-31 / Run497: five independent free-only work packages; 9 new pytest functions / 18 parameterized cases; V3 exact-source CI GREEN, JARVIS final-head CI pending.**

**Saved at:** **2026-10-31T15:54:42.417+09:00 Asia/Tokyo/JST** (local runtime wall clock, not a trusted/externally attested clock).

**Overall ARK/JARVIS: NOT_PASSED.** Disconnected/local integrity and defensive diagnostics advance; no end-to-end JARVIS, authenticated issuer/consent, trusted external clock, independently authenticated SQLite source, real-world effect, real training, Candidate promotion or protected V2 evaluation has been demonstrated.

## LATEST branches, work-basis and checkpoint provenance

- **JARVIS foundations:** [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), branch `research/jarvis-foundations`, OPEN / DRAFT / UNMERGED. **Invocation work-basis HEAD:** `92a5252b05e846366af586021a1be45da1352159` (Run496 checkpoint). **Final source/test HEAD = checkpoint-write-basis HEAD:** `cdcfa3b5aff2d741867b6618c1ee8ad6bf8a0050`. **Checkpoint-result HEAD:** assigned by this GitHub Contents update and verified *after* saving, never guessed within this self-referential file.
- **V3:** [Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5), branch `research/v3-learning-evaluation`, OPEN / DRAFT / UNMERGED. **Invocation work-basis HEAD:** `1a9abe3fe57c01ab2f03d8f6ad717543d30fc94f`; **final source/test HEAD:** `792543bd8fa9734e4c64fe6e5e451662eae9daa7`.
- **main:** `7a843f17eb96ed13d66f23b58b06406b3002e405`; no change and no merge attempted.
- **Previous canonical checkpoint:** [Run496](https://github.com/Iam-2squared/ark-ai/blob/92a5252b05e846366af586021a1be45da1352159/docs/PROJECT_STATUS.md). Older immutable commits, history, technical reports and evidence remain available.

## NEW work this invocation — five independent free-only packages

1. **V3 CI failure correction:** `src/ark/learning/lineage.py` retains strict 4,096-byte UTF-8 identity rejection but restores the existing `identity fields` error-contract phrase. Previous 6/6 failure on [#1805](https://github.com/Iam-2squared/ark-ai/actions/runs/41173650595) was exactly a regex mismatch, not a reason to weaken validation. Source commit `107a8eaeccb67626e096d638b632bf00057939e7`; resulting source CI [#1810 / 41177961859](https://github.com/Iam-2squared/ark-ai/actions/runs/41177961859) **6/6 GREEN**.
2. **Startup readiness post-authority epoch:** `src/ark/disconnected_local_readiness.py` rechecks the full schema/plan/grant/registry epoch and exact constructed result *after* denied-authority getters, detecting a reflected late mutation. Source `7b6283df219e584af81bec99243ba9a7b9276de5`; `tests/test_disconnected_readiness_late_report_epoch_run497.py` `b44e12673f9e9c68a671d18ad3f1bd49294ad8c9`; **2 pytest functions / 5 cases**.
3. **Scheduler read-only recovery:** `src/ark/disconnected_schedule_quarantine_ledger.py` opens an *existing* synthetic quarantine ledger in SQLite URI `mode=ro` with `BEGIN`, rather than `mode=rw`/`BEGIN IMMEDIATE`. Explicit initialization and append remain separate write operations. Source `b18115c61f4566349051235ee03f6fa259d593b2`; `tests/test_quarantine_restart_readonly_run497.py` `ada98440ddfc83eff8a4013fb66ac8a3f63ad957`; **2 functions / 2 cases**, including a concurrent reserved writer and a missing-DB fail-closed test.
4. **V3 bounded model artifact size:** `ArtifactIdentity.bytes` now requires an exact positive int no greater than `2**63-1`, preventing enormous claims entering lineage JSON. The upper bound remains a *claim*, not proof of actual weight bytes. Source `1b8ee6c236be21d77b52c9094b227cc861e4868c`; `tests/v3/test_lineage_artifact_size_bound_run497.py` `792543bd8fa9734e4c64fe6e5e451662eae9daa7`; **3 functions / 6 cases**.
5. **Memory retained-chain post-authority epoch:** `src/ark/memory/retained_epoch_chain.py` revalidates observed source epochs, earlier edges and exact result after denial-only authority getters; it still cannot certify historical source authenticity or authorize disclosure. Source `aab022d8925b38c071c815c74a76ee7811c96f54`; `tests/test_retained_memory_late_authority_run497.py` `cdcfa3b5aff2d741867b6618c1ee8ad6bf8a0050`; **2 functions / 5 cases**.

**TOTAL NEW: 9 pytest functions, 18 concrete cases, four new test files.** Source/test changes are saved on independent Draft branches; a new test file is not considered GREEN until exact-head CI verifies it.

## Exact-source CI / evidence

- **Previous PR #8 checkpoint** `92a5252b05e846366af586021a1be45da1352159`: [#1809 / 41173844845](https://github.com/Iam-2squared/ark-ai/actions/runs/41173844845) GREEN (older HEAD only). Previous source [#1807 / 41173686694](https://github.com/Iam-2squared/ark-ai/actions/runs/41173686694) 6/6 GREEN.
- **PR #8 current source/test** `cdcfa3b5aff2d741867b6618c1ee8ad6bf8a0050`: [#1818 / 41178360058](https://github.com/Iam-2squared/ark-ai/actions/runs/41178360058) **IN_PROGRESS**. No final-head 6/6 GREEN claim until all jobs pass.
- **PR #5 corrected intermediate source** `107a8eaeccb67626e096d638b632bf00057939e7`: [#1810 / 41177961859](https://github.com/Iam-2squared/ark-ai/actions/runs/41177961859) **6/6 GREEN** by exact individual job inspection.
- **PR #5 current source/test** `792543bd8fa9734e4c64fe6e5e451662eae9daa7`: [#1816 / 41178250696](https://github.com/Iam-2squared/ark-ai/actions/runs/41178250696) **COMPLETED / SUCCESS**; six Ubuntu/Windows × Python 3.11–3.13 jobs independently inspected and **6/6 GREEN** before this checkpoint.
- Local independent full pytest/Ruff: **NOT VERIFIED**. External GitHub DNS access from the container was unavailable. GitHub normal-source CI was used; no duplicate workflow runs manually dispatched.

## Frozen evidence and authorization boundaries

- Frozen Memory v1 contract `src/ark/memory/contracts.py` blob `b6e93821ecd69270a7634aceb20775dc36e9953c`; frozen Agency v1 `src/ark/agency/contracts.py` blob `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`. Both re-read, unchanged.
- Frozen V3 `docs/v3/CONTRACT.md` blob `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23` and `docs/v3/CONTRACT.sha256` blob `176154514bd6be22685ca0555bc682c3bd8d45dc` re-read, unchanged. Frozen V1/V2/Local UI/Launcher source/verification boundaries untouched.
- **No paid/external compute, GPUs, paid API, real Candidate adapter/weight generation, protected V2 final-suite opening, automatic promotion, real Tool execution, live sensor collection, external disclosure, new credentials/accounts, irreversible/destructive action, or main merge.** PR #5 and PR #8 remain Draft/unmerged.
- SQLite local hashes, CAS and synthetic witness objects do not prove issuer authenticity, human consent, genuine deletion, trusted clocks or cross-store atomicity. UNKNOWN/RUNNING WRITE remains quarantined; no automatic replay. PR #5 still blocked on immutable model/runtime identities, human-approved data/provenance decisions and explicit cost/billing gate.

## Next plan / 今後の方針

1. **Exact-head CI closure:** confirm every one of six PR #8 [#1818] jobs; if FAIL, inspect job log and repair only the failing semantics via normal writes, then continue unrelated free lanes. PR #5 current source is GREEN.
2. **Memory:** independently retained row/event custody, CAS concurrency, expiry and coherent multi-scope snapshots; never claim external authentication from local hashes.
3. **Planner/Tool/Agency:** durable UNKNOWN WRITE manual reconciliation; immutable registry-bound identity, exact PermissionGate and trusted-clock audit-before-action with one occurrence and mock-only executor; no real effects.
4. **Scheduler/Personal Context/Observation:** durable replay fences, revoked-consent/retention veto, startup readiness and synthetic audio/image/text fixture boundaries; no live capture/disclosure.
5. **V3 free-only guards:** local approval/reproducibility/hash/path validation; no training, model weights, protected V2 evaluation, promotion or spending.

---
**Historical checkpoints and frozen evidence remain in git; this invocation updates the canonical latest checkpoint only once.**

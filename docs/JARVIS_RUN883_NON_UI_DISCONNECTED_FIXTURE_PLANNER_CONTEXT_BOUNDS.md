# ARK AI Run883 — disconnected observation, Planner graph ingress, private context plaintext caps

**Observed at (Asia/Tokyo/JST): 2026-11-15T08:49:06.309+09:00.** This is an observed runtime wall clock only, NOT a trusted clock, source authentication, human consent, or review decision.

**Overall JARVIS: NOT_PASSED.** Current branch `research/jarvis-foundations`, open **Draft PR #8**, unmerged. Initial exact work-basis HEAD: `ae77fa2b2486a9f95a77f07b604b6ec41f49c4b8` (Run882 checkpoint). This invocation's **complete source/test HEAD**: `e5b6a6b2292859240867145791aac2ad53aa8dd9` (verified by PR head and exact compare). The technical-report commit SHA is unknown at document authoring and must be read from normal GitHub API after writing. The canonical checkpoint is updated at most ONCE near the end, never speculatively assigned a future SHA.

## NEW — three independent non-UI source+test packages (six commits, 31 synthetic parameter cases authored)

1. **Disconnected multimodal fixture boundary**, source `src/ark/disconnected_observation_fixture.py` at `2f0d2e7312e080ca47c026e81cf073bdd00ad4d0`, tests `tests/test_disconnected_observation_fixture_run883.py` at `56e507fc3ec3409cf447d0ca8b2308c8edf03734`. A new optional in-memory synthetic fixture adapter accepts only exact nonempty `bytes` up to 65,536 bytes and exact ObservationKind, returns an existing ObservationEnvelope with SHA-256 and fixed disconnected adapter ID. No raw payload appears in envelope metadata; no real microphone/camera/screen/file/network access, device claims, source provenance, consent, or tool authority. Guards reject changed local digest/class dependencies and invalid buffers. **14 authored cases** include four modality labels, boundary lengths, mutability/coercion, tampered dependencies and no payload retention.
2. **Planner standalone graph pre-hash identity cap**, source `src/ark/agency/planner.py` at `48f54f4aafae3805ea02147c2ab6ec77b5e5ae07`, tests `tests/test_planner_reflected_identifier_budget_run883.py` at `4b4cb45229a16ff534e263d649b7a4864a43bfa1`. `PlanGraph` now rejects reflected overlong step/dependency/action textual labels before duplicate sets, graph mappings or request-ID hashing. Optional graph limit is **4,096 UTF-8 bytes per label** with invalid-surrogate rejection. Frozen `PlanStep`, `ToolCall`, terminal propagation, journal schema and UNKNOWN no-replay are unchanged. **11 authored cases** include boundary acceptance, overlong/multibyte inputs and existing edge cap.
3. **Privacy-minimized context projection**, source `src/ark/personal_context_review.py` at `51cb538f0831687100b992bf7bf979e496ebf40c`, tests `tests/test_personal_context_plaintext_budget_run883.py` at `e5b6a6b2292859240867145791aac2ad53aa8dd9`. The optional ephemeral Personal Context projection now caps each scanned plaintext record at **65,536 UTF-8 bytes** and all scanned candidate content at **1,048,576 UTF-8 bytes**, rejecting before hashing/assembling sensitive plaintext. Unicode and import-time budget tampering fail closed. Frozen Memory v1 content storage contract/schema and source data are unchanged; no storage or export action occurs. **6 authored cases** include byte-vs-character width, surrogate, full input budget, acceptance and tampering.

Exact source/test compare `ae77fa2...e5b6a6b`: **six commits, exactly three non-UI source paths and three non-UI test paths**. No UI, frozen evaluations/contracts, PR #5 or PR #9 paths changed. Authored tests are not verified PASSES until exact-head Actions jobs complete.

## CI / evidence

- Inherited Run882 checkpoint HEAD `ae77fa2b2486a9f95a77f07b604b6ec41f49c4b8`: [CI #43650333364](https://github.com/Iam-2squared/ark-ai/actions/runs/43650333364) **GREEN 6/6** (Windows/Ubuntu × Python 3.11–3.13), verified by all individual job conclusions before new work.
- Observation source/test HEAD `56e507fc3ec3409cf447d0ca8b2308c8edf03734`: [CI #43654542494](https://github.com/Iam-2squared/ark-ai/actions/runs/43654542494), **IN_PROGRESS at last observation**, not full PASS.
- Planner source/test HEAD `4b4cb45229a16ff534e263d649b7a4864a43bfa1`: [CI #43654623189](https://github.com/Iam-2squared/ark-ai/actions/runs/43654623189), **IN_PROGRESS at last observation**.
- Full three-package source/test HEAD `e5b6a6b2292859240867145791aac2ad53aa8dd9`: [CI #43654952382](https://github.com/Iam-2squared/ark-ai/actions/runs/43654952382), **QUEUED at last observation**.
- No local checkout or pytest/Ruff was possible in this invocation: public GitHub clone could not resolve `github.com` from the local container. GitHub connector supplied read/write evidence; Actions is required for integrated validation. No duplicate manual workflow was launched.

**No new protected evaluation, paid compute, training, real backend dispatch, trusted clock, credential, source capture, actual user consent or human review.** PR #5 (approval-gated), #8 (JARVIS foundation) and #9 (UI foundation) remain open Draft/unmerged. **All new frontend/UI remains PAUSED.** V1/V2/Local UI/Launcher evidence, frozen contracts and Memory v1 schema unchanged. The synthetic fixture and ephemeral Personal Context are local *data transformations*, never real-world execution authorization.

## Unresolved blockers / next plan

1. Confirm latest exact-head Windows/Ubuntu × Python 3.11–3.13 CI 6/6; if any job FAILS, inspect logs and repair only through the normal Contents API, then work an independent non-UI lane during CI.
2. Diagnose SQLite WAL/SHM last-client-close transient unlinked-inode races and Privacy Revocation competing-process loser, retaining symlink/hardlink/alias rejection.
3. Continue generation-fenced Memory CAS/expiry coherent snapshots and durable Planner UNKNOWN recovery/terminal cascades without ambiguous WRITE replay.
4. Connect immutable ToolRegistry, exact-type PermissionGate, durable occurrence, audit-before-action, disconnected Mock Executor only on exact-head GREEN evidence.
5. Extend privacy-safe context, proactive scheduler, synthetic observation fixtures and detached free-only V3 path/identity/reproducibility guards; no UI or paid actions.

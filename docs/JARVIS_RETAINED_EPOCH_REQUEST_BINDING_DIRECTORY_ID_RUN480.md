# Run480 — retained local epochs, request-bound context, synthetic due restarts, V3 directory identity

**Scope:** Four reversible, disconnected/free-only implementation+regression-test packages in two still-Draft branches. The term "witness" denotes an untrusted, caller-retained local claim, **never** authenticated human approval, immutable writer, trusted time, license provenance or real-world authority.

**Initial work basis:** PR #8 research/jarvis-foundations at a13c6424d9f96a0d64e72ff117b370acefcf2ecd; PR #5 research/v3-learning-evaluation at 58a8f53c69ebb9104a95c9419ac6a4cf7e101087.

## Work saved this invocation — 44 authored pytest cases

1. **V3 local identity / same-name tree replacement (5 cases):** src/ark/learning/identity.py blob 8295659ad59735edc7c07ca5af67ff87cff9003f; tests/v3/test_manifest_directory_epoch_run480.py blob 761c5481911b30d763ce75dff69794bc87132f6f. Snapshot enumeration now retains root and per-entry device/inode/mode/mtime/ctime/link metadata, rather than only relative names and entry types. Tests swap a root or nested directory for same-name/same-byte copies after file hashing, change directory timestamps, and cover the code tree. Corrected the error message to its established "snapshot entries changed during hashing" wording so legacy tests remain valid. **Still NOT atomic against an adversarial writer or immutable upstream HF identity.** No downloaded weights, external tool or GPU execution.
2. **Memory coherent content epoch and retained comparison (12 cases):** src/ark/memory/atomic_epoch_review.py blob 7d3ba8d50e3ed048d70cb6d3496211c350e9a3b2; src/ark/memory/retained_epoch_review.py blob 7d4245014e90429cba5812341ad01e5985fa00ed; tests/test_memory_retained_epoch_review_run480.py blob d4d8ae1d8339759b5f1637356534ec4f598c291d. Single-transaction Memory v1 review adds a domain-separated **clock-independent content digest**, without changing existing timestamp-bound epoch_digest or frozen SQLite v1 schema. Separately retained views reject event count/tail rollback, same-count tail rewrite and no-event content changes. Increased event history is only ADVANCED_HISTORY_UNVERIFIED, not a proven append-only prefix: paired in-database rewrites remain undetectable without external custody.
3. **Personal Context request-bound local preview (16 cases):** src/ark/personal_context_request_binding.py blob b5d484218efda86547e57dc03ea963ddc642f7ae; tests/test_personal_context_request_binding_run480.py blob 9f6fea433b913375109dbeea0372e420c05fb676. Revalidates canonical JSON, owner/record IDs, scopes, content byte budgets and existing v1 local digest; returns only request-bound hash/count, not raw content. No revocation or consent authority can be inferred. A synthetic rewritten preview with recomputed local hash is deliberately treated as untrusted; its receipt still forbids export, retention and dispatch. Follow-up correction preserves explicit oversize exception text through JSON error handling.
4. **Synthetic due-slot restart triage (11 cases):** src/ark/agency/disconnected_due_recovery_review.py blob cba9ea9895c153dca261473cd023493df777869f; tests/test_disconnected_due_recovery_run480.py blob d3c6aebd57ac16a83005438617cfee50816a0a36. Read-only reopening + caller-retained witness detects count regression or same-count mutation; additional reservations are explicitly unverified rather than authorizing replay. Exact types and benign result authority fields checked. No scheduled execution, notification, OS call, cross-store transaction or trusted clock.

## CI and corrections — failures explicitly retained

- PR #8 prior Run479 checkpoint a13c6424d9f96a0d64e72ff117b370acefcf2ecd: #1610 / 41059506054 completed SUCCESS, but does not cover Run480.
- PR #8 Memory-only test HEAD 006f0c1871d1a864c46e4973ec5ae0e5cf2a5a90: #1616 / 41067052307 completed SUCCESS across six jobs; does not cover later Context/Scheduler.
- PR #5 initial V3 source/test HEAD 329c44498042f4c39ed8a2ecce3aac83b1722819: #1612 / 41066585009 FAILED all six jobs for three legacy regex expectations. Restored original refusal diagnostic via normal Contents update; identity guard unchanged.
- **PR #5 corrected final source/test HEAD ac08ee7f69c04fe6eb24d5dd1a044e5fc289118c: #1619 / 41067545964 six jobs SUCCESS**, Ubuntu/Windows Python 3.11–3.13 inspected directly.
- PR #8 initial Context test HEAD ee9d189372e4e24ca4d85a14c419f824b91930d0: #1618 / 41067395976 FAILED Ubuntu due to explicit size-limit exception being wrapped as generic JSON error. Correction preserved explicit size rejection without relaxing the limit.
- **PR #8 corrected final source/test HEAD bbff54155714a9d26aea039608c6c574a23a3c8f: #1622 / 41067877747 QUEUED** at last check. Do not call it six-job GREEN yet. Intermediate Scheduler source/test #1621 / 41067765315 also in flight.
- Local whole-repo pytest/Ruff **NOT independently run**: container Git clone could not DNS-resolve github.com. GitHub hosted CI is the executed matrix evidence. No manually duplicated runs or new paid/external compute.

## Frozen and blocked boundaries

All V1/V2/Local UI/Launcher original evidence, frozen v1 DDL, protected V2 final-evaluation restriction, V3 one-Candidate/no-sweep contract, human review and contamination/provenance/regression/reproducibility gates stay unchanged. PR #5 and #8 remain Draft/unmerged. No secrets, credentials, accounts, paid APIs/GPUs, real Candidate, dataset downloads, sensor capture, production Tool execution, irreversible action, model promotion or main merge.

Hard blockers: independent immutable retained event custody and trusted clock, authenticated consent/revocation, external WRITE-effect reconciliation for UNKNOWN WRITE, cross-store atomicity, actual model bytes and licensing provenance, physical PC/GPU evidence and separately authorized paid execution. An in-database hash or caller-created request ID does not resolve these.

## Next plan / 今後の方針

1. Confirm corrected final PR #8 exact-source CI #1622; on FAIL inspect jobs and make the narrowest semantics-preserving correction while pursuing independent free work.
2. Prove cross-restart retained epoch continuity only with separately retained independent evidence; synthetic append remains unverified.
3. Extend Planner UNKNOWN WRITE isolation, audit-before-action trusted-clock and immutable ToolRegistry/PermissionGate witnesses without actual dispatch or uncertain retry.
4. Improve privacy revocation/reuse, Scheduler occurrence sequence, Observation fixtures and V3 pre-paid path/provenance guards.
5. Protected V2 final evaluation, Candidate generation/promotion, paid compute and approval-gated main merge remain blocked.

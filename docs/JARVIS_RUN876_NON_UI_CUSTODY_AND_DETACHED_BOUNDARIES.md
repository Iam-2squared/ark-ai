# Run876 — isolated non-UI boundary hardening and regression evidence

**State:** non-UI foundations, disconnected and zero-new-cost; overall ARK/JARVIS **NOT_PASSED**. This is synthetic source/test evidence, not genuine user consent, independent attestation, trusted clock, model evaluation, Windows physical hardware, or any external effect.

**Work-basis:** Run875 checkpoint `ec10063917a92b30963a65e4d0c0cd4b1a24a33d`. **Source+test HEAD for this report:** `e9afa9ba56bd124fce5847126921276900d7f2e8`. Target is `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8). Four independent packages, **46 authored parametrized regression scenarios**, subject to exact-HEAD CI. No PR #5 or #9 changes, no main merge.

## Package A — disposable SQLite WAL diagnostic ingress (16 scenarios)

- `scripts/diagnose_ark_store_wal_last_close.py` commit `126792d4b56fa4213afae37634ea204dc9f163c6`: require **exact str** for iteration parsing and **exact str/bool** for direct fixture probe calls. Reject caller-supplied `__hash__` or truth-value hooks *before* any temp-file or child-process access. This is fixture-only; it does not relax a real SQLite WAL/SHM pathname, alias, or link-count denial.
- `tests/test_ark_store_wal_last_close_run847.py` commit `c150921ea7927c02092e9148a7b323a855be78c1`: five invalid iteration-carrier cases, five invalid store kinds, five nonexact keeper carriers, one adversarial hash hook; temp-directory opening patched to fail if input admission is bypassed.
- Does not establish a causal explanation or repair for historical Windows `-wal` `link_count=0`. POSIX held-file-descriptor probes remain **UNSUPPORTED** on Windows rather than a false PASS.

## Package B — detached free-only V3 packet adversaries (15 scenarios)

- `tests/test_v3_free_only_packet_boundary_run876.py` commit `d59459dfeaee5a2fd05aaf30f776e28b90ebdcaa`: exact upper numerical budget acceptance without authority; overflow/nonpositive/ordering/timeout mutations; invalid UTF-8/BOM/NUL; four receipt-authority descriptor swaps which must be refused without invoking injected code; modified crossbind callback denied before invocation.
- **No V3 frozen contract edit, no Candidate creation, GPU call, training permission, paid compute, weight generation, protected evaluation, promotion or reproducibility PASS**. Passing synthetic bounds is not signed measurement evidence.

## Package C — readiness hash/semantic separation (7 scenarios)

- `tests/test_startup_readiness_semantic_digest_run876.py` commit `5d96db58e815160de2461821649fe71d43528d3d`: independently rebuild a valid digest for semantically **forged** blocked-descendant states, unknown parents and a cycle. Both state and ancestor projections must fail closed despite a matching digest; valid blocked/degraded diagnostics and the UTF-8 identifier budget remain covered.
- READY is a disconnected diagnostic, not activation or tool permission.

## Package D — private observation hashing helper custody (8 scenarios)

- `src/ark/observation_fixture_adapters.py` commit `1a19ca65d6c0f43b011b31f0c2798f38fe7d8c09`: pin the original *local* private-byte hashing helper and reject a swapped callback before raw text/transcript/image/screen fixture bytes are passed to it. Existing original hashlib and content-byte budgets remain in force. This is a same-process guard, **not** anti-tamper attestation.
- `tests/test_observation_private_hash_helper_custody_run876.py` commit `e9afa9ba56bd124fce5847126921276900d7f2e8`: injected helper cannot see raw payload for any of four fixture kinds; unmodified helper still returns exact SHA-256 digest and a content-minimized envelope. No camera, microphone, file read, UI or actual private context ingestion.

## CI / test evidence policy

- Prior checkpoint `ec10063917a92b30963a65e4d0c0cd4b1a24a33d`: [#43611994857](https://github.com/Iam-2squared/ark-ai/actions/runs/43611994857), individually checked **GREEN 6/6** (Ubuntu/Windows, Python 3.11–3.13) on **Run875 only**.
- This run's automatic intermediate CI: [#43617514269](https://github.com/Iam-2squared/ark-ai/actions/runs/43617514269), [#43617574539](https://github.com/Iam-2squared/ark-ai/actions/runs/43617574539), [#43617653125](https://github.com/Iam-2squared/ark-ai/actions/runs/43617653125), [#43617732209](https://github.com/Iam-2squared/ark-ai/actions/runs/43617732209). At this report's source-write basis these were **IN PROGRESS/QUEUED**, not yet complete exact-head evidence. Additional source/test commits initiate Actions automatically; do not issue duplicate manual runs.
- **46 authored cases ≠ 46 proven PASS cases.** No local repository checkout/pytest/Ruff: this runtime's shell cannot resolve github.com. Read and write operations used the supported connected GitHub interface. Later test/CI results must be recorded against exact SHAs separately, without extrapolating between commits.

## Unresolved and next work

1. Confirm exact latest source+test **six-job** CI (and report/checkpoint commits separately); make only minimal normal-Contents-API repairs if there are genuine FAILs.
2. Diagnose intermittent Privacy Revocation multi-process loser rejection and Memory/ActionAudit WAL/SHM last-client-close transition; never skip a single-link/path/inode denial, auto-retry UNKNOWN, or regrant a veto.
3. Strengthen Planner crash-recovered RUNNING→UNKNOWN, CAS/expiry coherent Memory snapshots and retained evidence.
4. Integrate immutable ToolRegistry, exact-type PermissionGate, durable occurrence, audit-before-action and mock-only executor **only after prerequisite exact-head GREEN**; no real effect.
5. Continue private Personal Context, proactive schedule and observation back-end fixture contracts. Frozen V1/V2/Local UI/Launcher evidence unchanged. UI [Draft PR #9](https://github.com/Iam-2squared/ark-ai/pull/9) stays paused/unmodified; frozen gated [Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) stays unmerged.

**Prohibitions unchanged:** paid/external compute, new credentials, real Candidate training/promotion, protected evaluation, frozen-contract edits, irreversible action, physical-PC operation, real tool dispatch, forced Git changes, and approval-gated main merge.

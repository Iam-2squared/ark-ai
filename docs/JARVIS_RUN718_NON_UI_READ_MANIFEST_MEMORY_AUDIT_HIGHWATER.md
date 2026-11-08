# ARK Run718 — Free-only non-UI READ manifest and SQLite audit high-water integrity

## Scope and exact repository basis

- **Initial work-basis HEAD:** `6c5868b784097fcc4857cbb4ce024f27f5b146a9` (Run717 checkpoint, PR #8 Draft/unmerged).
- **Branch:** `research/jarvis-foundations`; no writes to main, PR #5, PR #9, frozen V1/V2/Local UI/Launcher evidence or protected Contract 1.
- **Technical report source basis:** `e9fc2d3333dfb3c7018a47a22a87b71bb7a646d3`. The report and later status are additional normal Contents API fast-forward commits, not source-test verification.
- **Scope:** isolated local, no real tool/model/sensor invocation, no private user bytes, no paid service, no Candidate/learning execution, no external compute.

## A — Independent write-once detached READ input manifest

- [Implementation `b2b29b3a`](https://github.com/Iam-2squared/ark-ai/commit/b2b29b3a0f786bfbffca48a6653ea39300f2f1f8): `src/ark/agency/disconnected_read_input_manifest.py` adds an optional **separate file** for the caller's *expected* per-step input SHA-256 values. It does not put raw arguments in the manifest or the SQLite receipt journal.
- Artifact uses a versioned, canonical ASCII JSON envelope with domain-separated SHA-256 and bounded 8,192-byte reads, exact `req_`/`step_`/digest shapes and <=24 unique ordered step claims. `O_CREAT|O_EXCL` forbids overwrite, including a preexisting symlink; file bytes are fsynced. A partial interrupted write remains quarantined, never silently deleted or retried.
- Read-only recovery rejects noncanonical/truncated/symlink/non-regular artifacts, duplicate steps, unrecognized fields and digest drift. The caller may supply an **independently retained SHA-256** to bind the artifact. `review_persisted_read_input_binding` feeds only the exact loaded digest tuples to the existing full receipt/topology/recovery bridge. No backend dispatch or automatic replay.
- [New synthetic tests `63ed8255`](https://github.com/Iam-2squared/ark-ai/commit/63ed825572d6c6591626e0fef4e0325b362ac10f) and import/format corrections [`d47e50cb`](https://github.com/Iam-2squared/ark-ai/commit/d47e50cb18c8832087bd7f1b6f9a2135121a8291) / [`69a13849`](https://github.com/Iam-2squared/ark-ai/commit/69a138492e01db3990176f941a09a2af53c2c003) cover restart, valid synthetic join, forged rehashed receipt, wrong request, exact shape/duplicate checks, race, tamper, short read, symlinks, and deny-only outputs. **21 authored parameter-expanded test cases** (not yet all-platform-certified).
- **Limitation:** The manifest is not independently authenticated, a cryptographically signed log, or a cross-file transaction with SQLite. File fsync alone does not promise directory-entry durability on every OS/filesystem. An attacker controlling the manifest AND a caller-supplied current hash can rewrite both. No authorization, device effect, audit-before-action or exact-once real execution is granted.

## B — Standalone Memory alignment with unambiguous append high-water

- [Production `bae1b165`](https://github.com/Iam-2squared/ark-ai/commit/bae1b165c087942f13e3c961f5e59456ee2cc735) changes `sqlite_event_alignment.py` to inspect **all** `sqlite_sequence` rows for `memory_events` in the same SQLite transaction, not merely the first.
- [Three synthetic tests `7fb3f117`](https://github.com/Iam-2squared/ark-ai/commit/7fb3f1173c5451ee9f33d0c448410ea7bf655889) distinguish a duplicate appended marker, an empty history carrying forged markers, and valid another-owner append.
- A direct local Python SQLite probe confirmed SQLite permits two `sqlite_sequence` rows with identical `name` and reports `PRAGMA quick_check = ok`. Thus `fetchone()` was an actual local ambiguity, not a schema/quick-check error.

## C — Event-prefix and retained-row readers with the same invariant

- [Event-prefix source `93d0cac1`](https://github.com/Iam-2squared/ark-ai/commit/93d0cac1de608abdb8c155ee3164b60eed938e9e) and [row-delta source `fc1ff682`](https://github.com/Iam-2squared/ark-ai/commit/fc1ff6829049176337127ebbc0d9c91ccdb580f5) reject duplicate sequence markers within their own read snapshots. They preserve prior event-prefix and retained-row witness formats, and never grant custody or disclosure.
- [New tests `5ba10124`](https://github.com/Iam-2squared/ark-ai/commit/5ba1012456f4cb2198d9df6d051b1ef02bcbdf8f), [assertion correction `3c4142ea`](https://github.com/Iam-2squared/ark-ai/commit/3c4142eabdc85ea1d56dbf6de9e3e8b69746565f) add **3 cases** for legitimate foreign-owner append, duplicated marker and empty-history forged marker.

## D — Action Audit before-write and read evidence

- [Source `b849b37b`](https://github.com/Iam-2squared/ark-ai/commit/b849b37b26fd8941daff264b900862c892b6bb3b) tightens `_require_dense_committed_audit_sequence` to require **exactly one** `action_events` high-water marker for nonempty history, none for empty history, inside the existing write or read snapshot. It is already invoked before appends and paged reads, so a plausible first sequence row no longer masks a second.
- [Five parameter-expanded tests `e9fc2d33`](https://github.com/Iam-2squared/ark-ai/commit/e9fc2d3333dfb3c7018a47a22a87b71bb7a646d3) cover append, first-page and later-page reads against duplicate markers, forged empty history and valid restart/append/pagination.
- **Limitation:** Every SQLite high-water is mutable metadata, not external authenticated or signed custody. None of these checks proves real actions or trusted clocks; a stronger attacker can rewrite the sequence and rows together.

## Test/CI evidence and corrections

- **Inherited Run717 checkpoint** [GitHub Actions #42507158610](https://github.com/Iam-2squared/ark-ai/actions/runs/42507158610) **6/6 GREEN**, six Windows/Ubuntu Python 3.11–3.13 jobs completed successfully before this run.
- [Early Run718 CI #42511574143](https://github.com/Iam-2squared/ark-ai/actions/runs/42511574143) **6/6 FAIL** in Ruff (`I001`, missing blank line before third-party `pytest`); exact test-only fix `69a13849` saved, no production checks weakened.
- [Corrected manifest-head CI #42511796012](https://github.com/Iam-2squared/ark-ai/actions/runs/42511796012) observed three Ubuntu jobs GREEN and other jobs in progress. This is a previous head, **not** certification of the latest Memory/Audit modifications.
- [Latest source/test HEAD CI #42512277361](https://github.com/Iam-2squared/ark-ai/actions/runs/42512277361) initially QUEUED. The report commit and later status commit launch separate automatic CI; exact final-head **6/6 GREEN remains UNVERIFIED** unless independently observed.
- The test count is **32 newly authored parameter-expanded test cases** across four new files, not an assertion of CI PASS. No full local Ruff/pytest, private actual data, live PC GGUF or actual hardware test was performed. No duplicate manual workflow run.

## Boundaries and prioritized next plan

1. Confirm **exact latest checkpoint-result HEAD CI** all six Windows/Ubuntu Python 3.11–3.13 jobs. Inspect actual failures; correct only by normal GitHub Contents API without overriding concurrent work. Work elsewhere while CI is running.
2. **Memory:** test/guard remaining cross-owner WAL, CAS/ABA and COMMIT-UNKNOWN attribution. Retain independent row/event witnesses; do not auto-retry ambiguous commits.
3. **Planner:** explicitly preserve manifest artifact hash outside both JSON and SQLite and model crash/failure stages; join only with the full topology/result journal review and no dispatch.
4. **Action safety:** independently grounded trusted-clock audit-before-action, registry-bound PermissionGate and durable occurrence replay prevention, then opt-in disconnected mock-only integration once prerequisite heads are GREEN.
5. Keep PR #5/#8/#9 Draft/unmerged, UI development paused, V1/V2/Local UI/Launcher and Contract 1/V3 frozen/protected evidence unchanged, zero-new-billable boundary enforced, no Candidate, external GPU, credential, hardware action or main merge.

**Overall status: ARK/JARVIS/V3 NOT_PASSED.**

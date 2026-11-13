# Run848 — disconnected startup receipt custody and PCM builtin integrity

Observed 2026-11-13 23:02:17 JST (reporting clock only; not a trusted consent/action clock).
**ARK/JARVIS NOT_PASSED.** This record is non-normative and does not alter frozen contracts or evidence.

## Work basis and concurrent work

- At invocation start, PR #8 / `research/jarvis-foundations` was Draft/unmerged at `c97a8fa42ea547d74a8b27f1997ae7f8f9fb30ba`. Compared with the prior Run846 checkpoint `6f98540cf3d9f96deee509ecf9d48f0a199d17f1`, six independent preceding commits touched the disposable ARK store WAL diagnostic and the offline text-index/redaction lanes. This run did not edit those paths or assume those in-flight CI results.
- The previous exact-HEAD [Run846 checkpoint CI #43429831210](https://github.com/Iam-2squared/ark-ai/actions/runs/43429831210) was checked: six Windows/Ubuntu × Python 3.11–3.13 jobs completed successfully **for `6f98540c` only**.
- [Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) and [paused UI PR #9](https://github.com/Iam-2squared/ark-ai/pull/9) remained Draft/unmerged in the initial metadata read; neither branch was changed in this invocation.

## Package A — startup READ/schema receipt descriptor custody

- Source commit [`fdf1e6fa`](https://github.com/Iam-2squared/ark-ai/commit/fdf1e6fad30ffeda3198e1bed95f9362f7475daa) in `src/ark/disconnected_local_readiness.py` snapshots the original schema and preflight receipt field and lookup descriptors at import time. Before reading retained local schema or invoking potentially reentrant registered-READ/SQLite probes, the review denies tampered descriptors, including False-looking or hostile getters. Original denial-property checks remain.
- Test commit [`980e4657`](https://github.com/Iam-2squared/ark-ai/commit/980e4657c1eeba2a04b1a17b428a05bdee118193) initially authored **20 cases**; after the CI-discovered `__new__` monkeypatch teardown failure, corrected to **18 authored cases**: eleven altered metadata fields, six safe field-lookup/initializer hooks, and one unchanged deterministic READ-only baseline. The source still checks `__new__` identity; only the unsafe in-process monkeypatch fixture was withdrawn. Tests assert that substituted field/hook callbacks and ToolBackend methods are not invoked.
- The startup review still does not authenticate the SQLite source, authorize backend execution, establish cross-store atomicity, or grant write/consent authority.

## Package B — disconnected private PCM sum shadowing and digest width

- Source commit [`a0cfb2e3`](https://github.com/Iam-2squared/ark-ai/commit/a0cfb2e33f1837c81b5f4bcf3f7e4718f859748d) in `src/ark/offline_pcm_activity_regions.py` rejects replaced `builtins.sum` and module-global `sum` before processing private PCM energy samples. It requires a 64-character SHA-256 text carrier before invoking the regex engine. Existing codec digest and budget checks are not relaxed.
- Test commit [`17806cdc`](https://github.com/Iam-2squared/ark-ai/commit/17806cdc04233bb664746098dee6acf9a616a2da) adds **13 authored cases**: two ingress modes × two patched-sum surfaces, two entrypoints × four invalid digest widths, and one original valid silent-offline fixture.
- This is not microphone access, automatic speech recognition, speaker identification, provenance, user consent or a real action. Detached signal metadata remains caller-controlled.

## CI-discovered repairs (same invocation; no weakened safety checks)

- [Startup source CI #43438206189](https://github.com/Iam-2squared/ark-ai/actions/runs/43438206189) reported two Ubuntu regressions in pre-existing `test_disconnected_readiness_pregetter_run612.py`: a new *earlier* fail-closed rejection used an error message that did not match the legacy `authority|denied` taxonomy. [Commit `92aaa11f`](https://github.com/Iam-2squared/ark-ai/commit/92aaa11f33e5a882d4b5d0d5bdcd3a85ec7e32b6) changed the rejection text to include `schema receipt authority carrier`; the earlier denial and metadata preaccess guard are unchanged.
- [Startup test CI #43438356286](https://github.com/Iam-2squared/ark-ai/actions/runs/43438356286) surfaced a test-only `__new__` monkeypatch teardown problem that polluted unrelated schema fixtures (18 failures/8 errors in Ubuntu 3.12, including dependent fixture setup). [Commit `3ebd29c5`](https://github.com/Iam-2squared/ark-ai/commit/3ebd29c58e72380cc741086bda774d07ff33a6e5) stops patching the class `__new__` in-process; `__new__` is still covered by the source's import-time carrier identity check. The test now authors 18 cases, not 20.
- The two safety packages together contain **31 corrected authored cases** (18 startup + 13 PCM), **not a proven 31 PASS**. The exact post-repair full Windows/Ubuntu Python matrix remains unverified, and other in-flight CI runs may show stale-HEAD failures.

## Validation and pending gates

- All four modified source/test paths were fetched again at exact source/test HEAD `17806cdc04233bb664746098dee6acf9a616a2da`; the longest lines were at most 93 characters. **No local full Ruff or pytest** was executed because this runtime cannot resolve github.com for a local checkout. Authored case counts are **not** CI PASS counts.
- Ordinary automatic CI was launched by the four normal Contents API commits, with run IDs:
  - [#43438206189](https://github.com/Iam-2squared/ark-ai/actions/runs/43438206189), startup source — IN PROGRESS at last check.
  - [#43438356286](https://github.com/Iam-2squared/ark-ai/actions/runs/43438356286), startup tests — IN PROGRESS at last check.
  - [#43438613687](https://github.com/Iam-2squared/ark-ai/actions/runs/43438613687), PCM source — QUEUED at last check.
  - [#43438736207](https://github.com/Iam-2squared/ark-ai/actions/runs/43438736207), PCM tests — QUEUED at last check.
- No duplicate workflow runs started. The **newest exact checkpoint HEAD six-job GREEN is not yet proven**. A test or CI failure must be examined and repaired without weakening predicates or misattributing prior-HEAD evidence.

## Non-authorizing boundaries and next work

Continue inspecting the exact latest CI and correct real regressions. Independently prioritize the disposable WAL/SHM last-close diagnostics for Memory/ActionAudit, coherent CAS+event highwater, persistent Planner UNKNOWN quarantine, registry-bound exact PermissionGate, durable occurrence/replay denial and audit-before-action with mock/disconnected execution only. UI/frontend remains paused. No paid or potentially billable service, external GPU, real Candidate/weights or promotion, protected final evaluation, physical-PC access, real ToolBackend/camera/microphone, destruction or main merge was performed.

# ARK AI Run841 — Non-UI held-SHM-FD lifecycle and pre-action cross-store admission

**Recorded at (Asia/Tokyo/JST): 2026-11-13T17:59:17+09:00** — reporting clock only, NOT a trusted action/authorization clock.

**Scope:** [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), branch `research/jarvis-foundations`. Initial work-basis HEAD `c100191c74324ce40e572f768384e96f148ba793` (Run840 checkpoint). No UI, Candidate, frozen evidence, protected evaluation, paid compute, external action or main integration.

## A. Disposable SQLite held-FD last-close comparison

New [`scripts/diagnose_sqlite_sidecar_fd_lifecycle.py`](https://github.com/Iam-2squared/ark-ai/blob/7176e08086f32fd45ba92bcc59eefd92fd7a5d15/scripts/diagnose_sqlite_sidecar_fd_lifecycle.py) (source commit `7176e08086f32fd45ba92bcc59eefd92fd7a5d15`) and [`tests/test_sqlite_sidecar_fd_lifecycle_run841.py`](https://github.com/Iam-2squared/ark-ai/blob/e8a3f6748bb83640844d3c2df5452fc6be8e2fbb/tests/test_sqlite_sidecar_fd_lifecycle_run841.py) (authored 9 parameterized cases, test source initial `600d40bdc7b48d9d51fb81e52e4777723191ec07`, formatting-only repair `e8a3f6748bb83640844d3c2df5452fc6be8e2fbb`).

Only a private TemporaryDirectory and synthetic SQLite WAL row are used. Parent opens the disposable `-shm` through an O_NOFOLLOW file descriptor and retains that FD while a second Python interpreter opens/closes SQLite. Categorize fstat link count on **held inode** versus lstat on **filename** before/after child final-close, with explicit opt-in keeper snapshot for lifetime control. Produce path-free bounded JSON categories; refuse symlink/no-SHM/unsupported fixture conditions. No sidecar bytes, user DB, tool backend or private user content is read. CLI bounds iterations to 1–8 and supports `--keeper`. This **does not demonstrate** ARK-specific Windows root cause; any ordinary last-close nlink-zero result cannot justify weakening no-follow, hardlink, fail-closed, or postcommit uncertainty protections.

## B. Registry-bound Planner + atomic pre-action manual triage ingress

Updated [`src/ark/agency/disconnected_registered_planner_atomic_triage.py`](https://github.com/Iam-2squared/ark-ai/blob/b423503459b9cbf24868765d30e9cde94cd25358/src/ark/agency/disconnected_registered_planner_atomic_triage.py) in `b423503459b9cbf24868765d30e9cde94cd25358`. Preflight exact WRITE occurrence pairs (bounded UTF-8 step IDs, fixed-format occurrence digests, duplicate rejection) and retained atomic witness scalar shapes **before** any registry resolution, Planner recovery field read, SQLite access or other child review. Recheck retained witness using exact scalar identity, never caller-replaceable `__eq__` on malformed values. Tests [`tests/test_registered_planner_atomic_bounded_preflight_run841.py`](https://github.com/Iam-2squared/ark-ai/blob/1c0a81776725a5f868c99f6f8cffdc819b27f095/tests/test_registered_planner_atomic_bounded_preflight_run841.py) added in `1c0a81776725a5f868c99f6f8cffdc819b27f095`, 13 parameterized fail-closed cases with deliberately uninitialized review sources and a never-call registry resolver.

This remains **manual-only**. A matching registry identity and local audit reservation cannot authenticate consent, prove external effect, prove two independent SQLite stores atomic, make a running WRITE outcome known, authorize tool execution, or safely replay a lost response. `ToolRegistry`/frozen contracts unchanged.

## CI evidence and boundaries

- Prior exact Run840 checkpoint `c100191c74324ce40e572f768384e96f148ba793` — [CI #43389534444](https://github.com/Iam-2squared/ark-ai/actions/runs/43389534444) **GREEN 6/6** Windows/Ubuntu Python 3.11–3.13; older HEAD only.
- First A test HEAD `600d40bd` — [CI #43396712496](https://github.com/Iam-2squared/ark-ai/actions/runs/43396712496) **FAIL 6/6 at Ruff E501** on the test's 101-character `_SCRIPT` path. Later test-only wrap in `e8a3f6748bb83640844d3c2df5452fc6be8e2fbb`; no test assertion removed.
- Intermediate B source `b4235034` — [CI #43396981273](https://github.com/Iam-2squared/ark-ai/actions/runs/43396981273) **FAIL 6/6** with the same outstanding test E501; older HEAD.
- Combined B test `1c0a8177` — [CI #43397052068](https://github.com/Iam-2squared/ark-ai/actions/runs/43397052068) **IN PROGRESS, Ubuntu already FAIL on prior E501** when inspected.
- Formatting-fixed last source/test HEAD `e8a3f6748bb83640844d3c2df5452fc6be8e2fbb` — [CI #43397176437](https://github.com/Iam-2squared/ark-ai/actions/runs/43397176437) **IN PROGRESS (six jobs running)** on final report-preparation inspection. No claim of six-job GREEN or 22 confirmed PASS until this exact HEAD run resolves. Report/checkpoint writes may generate their own ordinary CI automatically; do NOT infer their result.

**Execution restrictions:** source/test changes were accepted by ordinary GitHub Contents API; no raw Git objects, bypass writes, force push, duplicate workflow rerun, protected branch modification, paid/external GPU/API, real Candidate/weights, physical PC operation, new secrets, main merge, real backend or notification. PR #5 and paused PR #9 remain Draft/unmerged/untouched. Preserve frozen V1/V2/Local UI/Launcher evidence; ARK/JARVIS is **NOT_PASSED**.

## Next plan / 今後の方針

1. Confirm repaired exact-head CI Windows/Ubuntu all six. If FAIL, inspect exact failing job log; apply smallest semantics-preserving normal-Contents-API fix without stacking into in-flight code path; work on independent non-UI lane while CI runs.
2. Use only synthetic SQLite fixtures to compare held-FD, pathname and keeper behavior in Memory/ActionAudit; NEVER treat benign unlink as permission to retry aliased sidecars or ambiguous commits.
3. Strengthen Memory manual COMMIT-UNKNOWN, Planner persistent UNKNOWN quarantine and registry/audit gate boundaries after exact lower-layer GREEN.
4. Continue disconnected Personal Context revocation/retention, proactive occurrence/restart, observation and V3 free-only guard groundwork; leave UI paused and all gated evaluation/Candidate/main operations blocked.

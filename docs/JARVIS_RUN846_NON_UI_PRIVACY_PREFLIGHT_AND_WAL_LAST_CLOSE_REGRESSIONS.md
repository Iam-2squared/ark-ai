# ARK AI Run846 — retained context privacy preflight and held-FD WAL/SHM regressions

**Recorded JST:** 2026-11-13T21:58:03+09:00 (reporting clock only; NOT a trusted authorization/action time). **Initial work-basis HEAD:** `a3920ef0e75c3151a51e180313dc6e943a713eaa` (Run845 checkpoint). **Last source/test HEAD:** `4fdd237ed93b3525b421fe61ffb574faeb789089`. Branch `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8). ARK/JARVIS **NOT_PASSED**.

## Package 1 — retained private context preview, seven new regressions

- [Source `8b114d26`](https://github.com/Iam-2squared/ark-ai/commit/8b114d2688aaaa4d16ede15bc21ad9dca0c9c170): exact retained owner SHA/record ID/local SHA grammar, strict UTF-8 byte size, and a retained SHA-256 payload match **before rebuilding private fixtures**. The former `len(canonical_local_json)>65536` check alone allowed a malformed *exactly* 65,536-character public receipt to reach private rebuilding. This refuses that mismatch without lowering the valid 65,536-byte ceiling. It neither authenticates caller-supplied scope nor grants consent.
- [Legacy expectation repair `b2b5a5d8`](https://github.com/Iam-2squared/ark-ai/commit/b2b5a5d85214168ffdb2e48b7d82d6f0905dfeb6): all seven dataclass spoof cases still require `OfflineContextPreviewRejected`; distinguish malformed early `exact retained context preview required` from well-shaped but mismatched receipt. Rejection is NOT weakened.
- [Seven pre-rebuild negative tests `cb7736a8`](https://github.com/Iam-2squared/ark-ai/commit/cb7736a8fc28b642b3d659980d26736678683272), [actual surrogate corrected `a5fb6715`](https://github.com/Iam-2squared/ark-ai/commit/a5fb67155195dd259c63d1761149c155988e32ff): exact-limit forged JSON, short forged JSON, lone-surrogate Unicode, multibyte payload over byte budget, malformed record ID, malformed owner digest and malformed local digest. Each patches the private rebuild to fail the test if it is invoked.

## Package 2 — persistent disposable SQLite last-close regression, eight new cases

- [New regression `4fdd237e`](https://github.com/Iam-2squared/ark-ai/commit/4fdd237ed93b3525b421fe61ffb574faeb789089) tests the existing `scripts/diagnose_sqlite_sidecar_fd_lifecycle.py`: five invalid iteration limits, two genuine POSIX child-process WAL/SHM held-file-descriptor lifetime cases (with/without a keeper), and one CLI test requiring no automatic retry or real execution authorization and no path export. Windows/unsupported hosts explicitly SKIP the POSIX observation, not claim it passed.
- Independently reproduced now with *disposable* temporary SQLite DBs on **Linux/Python 3.13.5/SQLite 3.46.1**: held `-shm` link count is `1 → 0` after the last client closes without a keeper, and stays `1` through the child close when a keeper is open, then falls `1 → 0` when the keeper closes. Normal SQLite cleanup can unlink a held FD. This does NOT establish that the ARK CI failures arose from precisely that interleaving; never dismiss a production fail-closed refusal or auto-retry COMMIT-UNKNOWN.
- Memory, ActionAudit and revocation SQLite alias/no-follow/sidecar checks are unchanged. No real database was opened, no user content exported, and no credential, camera, microphone or real tool invocation.

## CI and exact evidence boundary

- Previous confirmed GREEN: [#43412325605](https://github.com/Iam-2squared/ark-ai/actions/runs/43412325605), Windows/Ubuntu Python 3.11–3.13 **6/6 for the earlier Run843 HEAD `c280d2a6` only**.
- Run845 checkout `a3920ef0`: [#43424776528](https://github.com/Iam-2squared/ark-ai/actions/runs/43424776528) Ubuntu 3.12 **FAIL** with three outdated Personal Context denial-text expectations and exactly one forged 65,536-character preview reaching a patched private rebuild. This invocation addressed those four observed failures; **not yet proven GREEN at latest HEAD**.
- Subsequent automatic runs were observed QUEUED: source [#43428276616](https://github.com/Iam-2squared/ark-ai/actions/runs/43428276616), legacy test [#43428526220](https://github.com/Iam-2squared/ark-ai/actions/runs/43428526220), new privacy [#43428583259](https://github.com/Iam-2squared/ark-ai/actions/runs/43428583259), Unicode correction [#43428652254](https://github.com/Iam-2squared/ark-ai/actions/runs/43428652254). New independent WAL regression run and eventual checkpoint run must be checked at their **exact SHAs**, not assumed from older GREEN. No duplicate workflow launch.
- **15 new cases authored, not 15 verified PASS**. Three modified privacy paths were re-fetched with no line over 100 chars; local full Ruff/pytest and physical machine/GGUF test were NOT run. The disposable Linux proof is separate evidence, not six-platform CI.

## Next plan / 今後の方針

1. Match six Windows/Ubuntu jobs to the latest source+test and checkpoint HEAD, repair any FAIL via normal GitHub Contents API only; do not bypass safeguards.
2. Continue **disposable** Memory/ActionAudit WAL/SHM race triage using keeper/held-FD controls. Preserve every alias/single-link denial and manual-only ambiguous COMMIT outcome.
3. Advance Memory CAS/global event continuity/expiry, Planner UNKNOWN persistence/terminal propagation; only after dependency GREEN integrate registry-bound identity, PermissionGate, audit-before-action, occurrence/replay denial and disconnected Mock Executor.
4. Independently advance Personal Context, proactive backend, Observation fixture contracts and free-only V3 identity/path/reproducibility guards.

Frozen V1/V2/Local UI/Launcher contracts and evidence unchanged. [PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) protected Draft/unmerged. [PR #9](https://github.com/Iam-2squared/ark-ai/pull/9) UI Draft/unmerged/untouched; all new UI/frontend development remains PAUSED. No paid/potentially billable GPU/API/service, new secrets/accounts, real Candidate generation/promotion, protected V2 evaluation, trusted consent/clock/human-review identity, actual external execution, destructive operations or main merge.

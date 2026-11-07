# ARK AI — Run681 / NON-UI guard reconciliation, WAL and crash-gap evidence

**Saved at:** 2026-11-07T16:54:01.893+09:00 Asia/Tokyo/JST (administrative host time, **not** an authenticated action clock).

**Status:** FREE-ONLY / disconnected mock and local SQLite fixtures; ARK/JARVIS **NOT_PASSED**. Work is isolated to [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8). No UI, runtime backend dispatch, real consent, paid compute, protected evaluation, Candidate or main merge.

## Work basis and meaningful packages

- Initial exact branch HEAD: `0920b0b990bb3f03c210b6c39483aba84edacdc7` (Run680 checkpoint).
- **A — CI failure diagnosis and semantic-preserving regression correction**: [CI #42349969868](https://github.com/Iam-2squared/ark-ai/actions/runs/42349969868) on the initial HEAD failed in pytest, with Ubuntu Python 3.11 reporting **14 FAIL / 10,297 PASS / 1 SKIP**. The new fail-closed original result-constructor and lookup-hook guards reject before private SQLite access. Four historical test files still expected later error strings or callback execution. Normal Contents API updates: approval result `e4cf7d49adedbdbe359f4040d758ba1dff176fcd`; proactive last getter `fad0d8551fdecf1077d5ef9eee6f8120a939fe65`; proactive getter/preaccess `02234c1592a99bf7220d86f83c7136e2ea719ca5`; proactive constructor/epoch `9629f32c519c9a8231c71282d64ea7065943319a`. Tests now require the **earlier exact rejection**, verify poisoned constructors/getters are *never called*, and check read-only persisted bytes where relevant. No production guard was changed or weakened.
- **B — Multi-scope Memory WAL consistency**: `tests/test_memory_cross_scope_coherent_wal_interleave_run681.py` at source/test commit `b2bdc26ba38aa949632b26a6c5d726ab740771d4` adds **3 parameterized scenarios**. A second SQLite connection commits while the first retained row scan is inside a pinned read transaction: (1) update another scope + append third scope, (2) delete/recreate same ID in a separate scope, (3) append a disjoint owner. The in-flight review must report the old **2-row/2-event** snapshot; a new review must observe the advanced 3- or 4-event coherent epoch. All six output authority flags must remain False; event/row witnesses are local continuity metadata, not writer attribution.
- **C — Detached mock authorization/audit crash gaps**: `tests/test_offline_audit_cross_store_crash_gaps_run681.py` at `e494fa5636ca87d161cd22b4c6b4ac1d209dfdae` adds **3 parameterized scenarios**: restart after reservation only, after the pre-action audit is committed but before the link, and after the sidecar link commits. Independently reopened SQLite stores preserve exact counts and reject a reused token with a new occurrence. No backend is ever called. Even a complete local link cannot prove user consent, trusted time, external effect, or globally atomic exactly-once dispatch.

- **D — Planner mixed-recovery digest-custody hardening**: `src/ark/agency/disconnected_write_recovery_fence.py` changed at `d707bb71e9a5af9116a0d5b3a10d34ef55b6c491` to pin imported SHA-256, JSON serializer/module and digest domain by original **identity**, not only equality. Checks run before untrusted claims and at each reentrant carrier/decision epoch. The existing reentrant regression was strengthened for *early* denial at `481073756996841624629d8962e21dd3e2a77503`, and `tests/test_disconnected_mixed_fence_digest_custody_run681.py` adds **6 parameterized tamper cases** at `96c222aefddf6948ffcea65dcc64a930a5075120`. It requires injected callbacks never execute, including an equal-value byte-domain replacement. Unlike a hash of claimed evidence, this still authenticates no real-world actor, clock or execution. CI pending.

## Exact-head CI / evidence status

- Initial HEAD `0920b0b990bb3f03c210b6c39483aba84edacdc7` [#42349969868](https://github.com/Iam-2squared/ark-ai/actions/runs/42349969868): **FAIL**; failures were old regression expectations for earlier denial, not permission bypasses.
- Corrected source/test HEAD `9629f32c519c9a8231c71282d64ea7065943319a` [#42352811531](https://github.com/Iam-2squared/ark-ai/actions/runs/42352811531): at sampling **Ubuntu 3/3 GREEN; Windows 3/3 IN PROGRESS**.
- Memory package HEAD `b2bdc26ba38aa949632b26a6c5d726ab740771d4` [#42352922287](https://github.com/Iam-2squared/ark-ai/actions/runs/42352922287): **6/6 IN PROGRESS** at sampling.
- Audit package HEAD `e494fa5636ca87d161cd22b4c6b4ac1d209dfdae` [#42353026356](https://github.com/Iam-2squared/ark-ai/actions/runs/42353026356): **5/6 IN PROGRESS, 1 QUEUED** at sampling.
- **None of those partial results prove the subsequent report or checkpoint HEAD GREEN**. Do not inherit or fabricate exact-HEAD CI PASS. Automatic GitHub PR CI only; no equivalent manual reruns.

## Independent blockers and authority bounds

- Branch `main` remained `7a843f17eb96ed13d66f23b58b06406b3002e405` at invocation start; frozen V1/V2/Local UI/Launcher contracts and evidence were not written to. Protected V2 final evaluation remains unopened.
- [V3 Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) at `805b377697472268db02650a89c7a94b1c5337c8`, read-only [PRE_PAID_COMPUTE_GATE](https://github.com/Iam-2squared/ark-ai/blob/805b377697472268db02650a89c7a94b1c5337c8/docs/v3/PRE_PAID_COMPUTE_GATE.md): immutable HF revision/base/tokenizer/tool hashes, real human-approved 120/30 data and rights/contamination, exact environment/device identities, budget and separate explicit preflight/Candidate authorizations remain absent. Nothing billed, downloaded or trained here.
- [UI Draft PR #9](https://github.com/Iam-2squared/ark-ai/pull/9) at `3b49048dd70eebcb6268299b9ecef4e301bbc0fd` was left untouched. No frontend changes or tests.
- Clock callbacks are local mocks; three independent store commits cannot be treated as a globally atomic reservation/audit/action transaction, and none establishes human consent, real occurrence identity, actual tool outcome, automatic replay permission or privacy clearance.

## Next plan / 今後の方針

1. Inspect full six-job exact-head CI after it completes. For failures, read the failing job logs and apply a *minimal*, normal-path correction; avoid any bypass or duplicate workflow run. Keep independent lanes active while CI runs.
2. Extend Memory COMMIT-UNKNOWN, CAS/ABA/expiry/WAL row+event and privacy retention with independently reopened, coherent snapshot evidence. No writer attribution from matching bytes.
3. Harden Planner per-step and ancestor READ receipts, terminal propagation, startup and irreversible mock WRITE recovery. Add persisted occurrence→pre-action audit→result link only behind exact-type, restart-safe deny-only boundaries.
4. Keep PR #5 Draft/no paid training, PR #9 untouched/no UI, V1/V2 frozen and main unmerged; JARVIS **NOT_PASSED** until independent gates are actually evidenced.

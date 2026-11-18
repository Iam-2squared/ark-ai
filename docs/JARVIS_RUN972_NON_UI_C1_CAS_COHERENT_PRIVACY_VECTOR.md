# ARK AI Run972 — opt-in Memory C1 admission and two independent privacy/restart guard epochs

**Report saved (JST, untrusted reporting clock):** 2026-11-19T01:51:27+09:00. **Work-basis PR #8 HEAD:** `78694aebb92f468e23fbfde1344be31fb2516dd2` (Run971). **Last source/test HEAD:** `9216cb2435ee5702d5b268151a2d2e6892ba60ed`. Report is non-normative evidence; **ARK/JARVIS NOT_PASSED**.

## Implemented and saved

1. **Memory generation-fenced CAS C1 alias admission.** `e7e30d9ba4b5d9cebd55e726a3127572568cb111` hardens the two optional source/scope identifier checks: U+007F–U+009F plus C0 now fail *before* path, hash, or SQLite access. The frozen v1 MemoryScope/MemoryWrite contracts remain byte-unchanged. `fd2c307fe9d6a4957c2957ecf54af5c2e601667a` adds 18 negative parametrized cases (six C1 values × three identity positions, each checked on observation and proposed update) plus a Japanese positive admission assertion.
2. **Read-only Memory coherent-expiry restart bridge vector custody.** `ae3c0c2a52354c39918e0f7d8982208037ca25b5` pins the full result/denial field-name vector by import-time object identity before any retained epoch or SQLite read. `6bf4541646d758321ca952274f5a7b5dc8a9458f` adds four hostile vector rewrites and one unchanged-protocol control. No automatic purge, trusted clock, or historical completeness claim.
3. **Privacy retention recheck denial-vector custody.** `865cd4e5e22edf3d1e51c7c0ca2add41d71f9802` checks original class denial, result-field and allocation-hook name vectors before any Memory or revocation database access. `9216cb2435ee5702d5b268151a2d2e6892ba60ed` adds 12 vector mutation cases (three vectors × four rewrites) and an unchanged-protocol control. No erasure, disclosure, consent or context reuse grant.

**3 coherent independent source+test packages; 37 new authored test cases (19 + 5 + 13), not 37 measured PASS.** Normal GitHub Contents API writes only; no force-push, raw Git object bypass, merge, real tool/hardware action, network inference, paid compute, new secrets or irreversible operation.

## Exact-head CI sampling

- [Run971 checkpoint `78694aebb92f468e23fbfde1344be31fb2516dd2`, run #44340998758](https://github.com/Iam-2squared/ark-ai/actions/runs/44340998758): **GREEN**; six actual completed SUCCESS jobs (Windows+Ubuntu × Python 3.11, 3.12, 3.13), verified this invocation. This GREEN is only for the prior HEAD.
- Memory CAS source [#44351273352](https://github.com/Iam-2squared/ark-ai/actions/runs/44351273352), test [#44351351233](https://github.com/Iam-2squared/ark-ai/actions/runs/44351351233); coherent bridge source [#44351487069](https://github.com/Iam-2squared/ark-ai/actions/runs/44351487069), test [#44351533396](https://github.com/Iam-2squared/ark-ai/actions/runs/44351533396); privacy source [#44351687781](https://github.com/Iam-2squared/ark-ai/actions/runs/44351687781), test [#44351740232](https://github.com/Iam-2squared/ark-ai/actions/runs/44351740232): **in progress / queued** at initial sampling. These states can change. Never claim this source/test HEAD fully GREEN without matching six completed jobs.
- No local full-suite or physical PC test was performed. Every retained local digest or mock result is non-authorizing.

## Invariants and blocked gates

Frozen V1/V2, Local UI/Launcher, Memory v1, Observation Envelope v1, PlanStep/ToolCall v1, V3 Contract 1/protected evaluation boundaries and all immutable evidence remain untouched. PR #5 protected Draft/unmerged. PR #8 remains Draft/unmerged. Paused UI PR #9 Draft/unmerged/untouched. Main unchanged. No Candidate weight generation/promotion, GPU/paid service, credentials, protected V2 evaluation, real tool actions, automatic uncertain WRITE retry, irreversible deletion or main merge.

## Priority queue

1. **Certify new exact HEAD CI all six jobs** and repair concrete failures via ordinary Contents API only, while working independent non-UI lanes.
2. Memory WAL/SHM last-close, CAS/ABA and COMMIT-UNKNOWN diagnostic recovery with synchronized row/event/expiry witnesses.
3. Planner restart snapshots and terminal precedence, then registry-bound PermissionGate → persistent one-shot authorization → preaction audit → disconnected mock execution. Integrate only when its prerequisites are GREEN.
4. Personal Context retention/revocation and Proactive occurrence replay/clock fences; Observation remains fixture-only; V3 stays strict, local and free-only; UI remains paused.

**Non-normative report. No new PASS gate.**

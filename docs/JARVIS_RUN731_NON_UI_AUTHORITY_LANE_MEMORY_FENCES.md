# ARK AI — Run731: non-UI authority, free-lane, Memory CAS and clock protocol fences

**Recorded (administrative JST):** 2026-11-09T15:20:10.785+09:00. This is not a trusted action clock, independently authenticated time, user consent or hardware observation.
**Branch:** `research/jarvis-foundations`; [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8) (unmerged). **Initial work-basis HEAD:** `5293c826934933089b6102a2c81e2438d57faa3a`, a Run730 technical-report commit. **Latest saved source/test HEAD before the final report revision:** `158e5172270aa741a72472f106d43a18fa18e9b9`.
**Scope:** 4 independently reversible non-UI packages, 4 production modules updated, 4 new test files with **43 authored cases** (12 + 17 + 7 + 7), and 2 inherited test files amended for safer early refusal. No UI, paid services, external compute/GPU, credentials, physical hardware, real actions, Candidate weights, protected V2 evaluation, promotion, main merge or frozen contract edits.

## A — Non-authorizing authority-gap claim custody

[Production `3383c36`](https://github.com/Iam-2squared/ark-ai/commit/3383c3617f05401df4dd747a4412e02faa938737) pins the import-original `hashlib` and `json` modules/callbacks, all four identity/digest regex authorities, fixed evidence state set, diagnostic digest domain bytes, and timestamp ceiling **before caller-private issuer/subject fields are read or passed to serializers**. The same checks repeat across callback epochs and before a denial-only result is constructed. This is only in-process tamper detection, never cryptographic proof of issuer or consent.

[12 new tests `89b1d52`](https://github.com/Iam-2squared/ark-ai/commit/89b1d520a6a1c248bff18fa275b4e4ceebd56ac4) cover 11 hostile substitutions and a benign deny-only control. Two inherited preexisting test files were corrected at [`b651208`](https://github.com/Iam-2squared/ark-ai/commit/b651208bed828c1a9948bd59506ce078f3688d6f) and [`9300339`](https://github.com/Iam-2squared/ark-ai/commit/9300339990941b7b081ed750ee31e5bdc0959d15): substituted hashing can no longer execute, nor should it mutate an input as a side effect. Production refusal was not weakened.

## B — Disconnected work-lane scheduling protocol

[Production `685ac29`](https://github.com/Iam-2squared/ark-ai/commit/685ac29123dda32c9ce018dae1776b2047e84875) pins codec/regex/path/cost/domain/budget and selector helper identities; also pins original slotted work-lane fields, report fields/constructors and the three explicit deny-only properties. Check before input materialization, at every work-lane iteration epoch, and before returning the result. Caller-supplied CI-green or completion claims remain **untrusted labels** and cannot confer actual GitHub write, execution or spending authority.

[17 new cases `b56809e`](https://github.com/Iam-2squared/ark-ai/commit/b56809e35fafef72123c312a15a11b6f4b19c85c) cover 16 hostile replacements and the original deterministic conflict/defer behavior. The selector remains a **synthetic planning aid**, not an autonomous GitHub permission gate.

## C — Detached Memory generation/CAS retained-witness parser

[Production `5dd70ed`](https://github.com/Iam-2squared/ark-ai/commit/5dd70edcfbfe4c1461b6b4dc306ef56eb3caeff1) binds original SHA/memory-ID parser objects, local event/SQLite integer budgets, retained-field reader and authority-denial checker **before retained private fields or a SQLite store are processed**. The helper is rechecked before invoking the underlying generation reviewer, during comparison epochs and at the terminal return.

[7 new tests `32aae53`](https://github.com/Iam-2squared/ark-ai/commit/32aae535e3106a58d1e6a3e59b696d3886715822) cover six hostile replacements plus clean non-authorizing local review. This detached review is **not** a process-wide atomic CAS, trusted original writer, automatic COMMIT-UNKNOWN retry, or permission to mutate records.

## D — Synthetic clock parser/limit continuity

[Production `2efba9b`](https://github.com/Iam-2squared/ark-ai/commit/2efba9bf9d32e3cdaac3d270ee2c0afc14ee3047) extends the established import-original digest and denial checks to exact clock source/chain regex objects, timestamp and sample budgets, genesis-field vector and denied-authority names. The first check now runs **before the clock sample-count admission**, so a substituted limit cannot affect iteration ahead of a protocol check. Existing deliberately reentrant `_hash` test seam remains intact; no trusted clock is claimed.

[7 new tests `158e517`](https://github.com/Iam-2squared/ark-ai/commit/158e5172270aa741a72472f106d43a18fa18e9b9) cover six parser/limit/denial drifts without advancing the caller-supplied sample iterator and one normal deny-only control. Local monotonic ordering is not signed time, sensor attestation or real action permission.

## CI provenance / remaining gates

- Previous concurrent [Run730 checkpoint-result CI #42570698476](https://github.com/Iam-2squared/ark-ai/actions/runs/42570698476) was read as **6/6 GREEN** on Windows/Ubuntu × Python 3.11–3.13, for its own `5293c8269` HEAD only.
- Latest Run731 source/test commit `32aae535e3106a58d1e6a3e59b696d3886715822` associated with [CI #42572259178](https://github.com/Iam-2squared/ark-ai/actions/runs/42572259178), **QUEUED** at last observed read. Prior [Run731 intermediate CI #42571918734](https://github.com/Iam-2squared/ark-ai/actions/runs/42571918734) was IN PROGRESS then. No latest Run731 six-job GREEN claim and no local full pytest benchmark.
- Latest fourth-package source/test HEAD `158e517` [CI #42572762987](https://github.com/Iam-2squared/ark-ai/actions/runs/42572762987) QUEUED at observed read, with no 43-case cross-platform PASS claim. The earlier `32aae53` [CI #42572259178](https://github.com/Iam-2squared/ark-ai/actions/runs/42572259178) was still QUEUED, and cannot be reused as final evidence.
- This report and later one-time canonical status checkpoint generate distinct HEADs; their CI must be checked separately. Do not carry forward older HEAD's PASS as this run's evidence.
- No manually duplicated workflow runs or unsafe Git writes. All production/test writes used normal GitHub Contents API on Draft PR #8 after HEAD rereads; no force-push, ref rewrite or raw Git object construction.
- Draft PR #5 remains gated/unmerged; Draft PR #9 UI branch remains paused/unmerged; frozen V1/V2/Local UI/Launcher evidence and protected final evaluation untouched. No new secrets, paid services, external compute, real actions, human-review claims or irreversibility. **ARK/JARVIS/V3 NOT_PASSED**.

## Next plan / 今後の方針

1. Check exact Run731 source, report and canonical checkpoint six-job CI, inspect actual failing logs; repair only observed regressions without allowing hostile callback execution.
2. Continue Memory coherent snapshots, ABA/CAS, expiry and manual-only COMMIT-UNKNOWN triage; never infer independent attribution or replay safety.
3. Advance Planner crash-safe READ retained evidence, UNKNOWN quarantine, terminal DAG propagation.
4. After exact-head lower-layer GREEN, join immutable ToolRegistry/exact-type PermissionGate, durable occurrence and audit-before-action to a **disconnected mock executor only**. Trusted time, identity and real effects remain explicit blockers.
5. Continue private Context, proactive state and observation fixture adapters; V3 free-only guards may be reviewed but PR #5 protected compute/frozen evaluation remain closed. UI work stays paused.

# ARK AI — Run711 non-UI core: early-denial CI recovery and custody hardening

**Report captured at:** 2026-11-08T11:57:59.855Z / 2026-11-08 20:57:59 JST (administrative clock; **not** externally authenticated). **Branch:** `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), open/unmerged. **Initial inspected work-basis HEAD:** `bc63a9802f5f84264749721953edafc8e340a17d`. **Latest verified pre-report HEAD:** `ef25233a852f1816782d1cb0521d3b4de9c3879e`.

## Scope and exact evidence

Four independent free-only non-UI packages were saved using the **normal GitHub Contents API**. No writes to frozen contracts, V1/V2/Local UI/Launcher, PR #5, PR #9, main, frontend, paid training, credentials, hardware, or external effects.

1. **CI recovery: PNG forged inventory class** — [`2a7176d`](https://github.com/Iam-2squared/ark-ai/commit/2a7176d10ef1303827f4f1292b2f0a96207ce287) updates the preexisting exact-denial expectation in `tests/test_offline_png_import_authority_run608.py`. Original [Run710 final CI #42473383999](https://github.com/Iam-2squared/ark-ai/actions/runs/42473383999) actually concluded **FAIL 6/6**: Ubuntu 3.11 had **1 failed, 11,070 passed, 1 skipped**; Windows 3.13 had **1 failed, 11,011 passed, 60 skipped**. Both logs identify `test_copied_descriptor_class_never_constructs`, now rejected *earlier* by `constructed PNG inventory field, constructor or lookup changed` instead of the old `denial descriptor changed`. The fix changes **test diagnosis only**; production PNG fail-closed logic is unchanged and counterfeit constructor execution remains forbidden.
2. **Memory post-COMMIT-UNKNOWN triage** — source [`1d7c597`](https://github.com/Iam-2squared/ark-ai/commit/1d7c597fea885e1f7bf6ff33cac3e2ce69a71ccf) imports the optional generation-CAS original `MemoryWrite`/`MemoryScope` class/slot guard and checks it **before reading `proposed.scope`**. Every reentrant triage `stable()` boundary repeats the guard. [`a356f01`](https://github.com/Iam-2squared/ark-ai/commit/a356f01e9728d6b988630f3a887fcfb7d2f19cd8) adds **15 subprocess-isolated hostile field, constructor, allocation and lookup cases**; they assert no injected getter/SQLite reader invocation and unchanged disposable row state. This is read-only manual triage: no caller attribution, automatic retry, consent, trusted-clock or real action authority is added.
3. **Proactive expired schedule quarantine** — source [`82ef305`](https://github.com/Iam-2squared/ark-ai/commit/82ef30555888a17f92062e753e9e50ca6fcae68f) pins original receipt class, `witness`/`quarantined_index` slots and constructor/attribute hooks at entry and again across the write transaction. It prevents a preinstalled executable receipt field/constructor from first executing **after** a synthetic quarantine COMMIT. Import-original *denial-property* checks remain after COMMIT as before, preserving the explicit no-authority/no-rollback semantics. [`86fedbd`](https://github.com/Iam-2squared/ark-ai/commit/86fedbd35712bc3e0e391f1104c9e5f87df2d1dc) adds **7 isolated preinstalled forgeries, 1 digest-time descriptor substitution/rollback regression, 1 healthy non-authorizing result** (**9 tests**).
4. **Disconnected mock-tool digest and JSON custody** — source [`eb10227`](https://github.com/Iam-2squared/ark-ai/commit/eb10227a29578e40ac70502a66d3f4a0eccf7e8f) pins import-original `hashlib`/`sha256`, `json`/`loads`/`dumps` and the local digest domain, before exposing any private synthetic JSON bytes to these primitives; checks repeat after calculation callbacks. Existing digest-time hostile mutation remains rejected as a change. [`ef25233`](https://github.com/Iam-2squared/ark-ai/commit/ef25233a852f1816782d1cb0521d3b4de9c3879e) adds **6 preinstalled primitive replacements, 1 reentrant replacement, 1 normal deny-only calculation** (**8 tests**). No real `ToolBackend` exists in this fixture path.

**New tests:** 15 + 9 + 8 = **32**, plus 1 existing PNG assertion corrected. **Production modules touched:** 3 optional non-UI modules; **test modules touched:** 4 (one existing, three new). Git compare of initial `bc63a9802` to `86fedbd357` was fast-forward, 5 commits with exactly the five corresponding non-UI paths. Later Toolbox work is independent of the earlier Memory/Quarantine source lanes.

## CI and claims, at report preparation

- Last fully verified earlier exact-head CI [#42472512909](https://github.com/Iam-2squared/ark-ai/actions/runs/42472512909): **six jobs GREEN**; it predates later Run710 changes and is **not** evidence for Run711.
- Run710 final [#42473383999](https://github.com/Iam-2squared/ark-ai/actions/runs/42473383999): **six jobs FAIL**, same single legacy PNG test expectation mismatch on checked Ubuntu and Windows logs.
- PNG test fix [#42477156587](https://github.com/Iam-2squared/ark-ai/actions/runs/42477156587): **IN PROGRESS** at latest source read.
- Memory tests [#42477349141](https://github.com/Iam-2squared/ark-ai/actions/runs/42477349141): **IN PROGRESS**.
- Quarantine tests [#42477586755](https://github.com/Iam-2squared/ark-ai/actions/runs/42477586755): **IN PROGRESS**.
- Toolbox tests [#42477879073](https://github.com/Iam-2squared/ark-ai/actions/runs/42477879073): **QUEUED**.
- **No local full pytest/Ruff**, latest exact-head six-job GREEN, real GGUF execution, externally trusted time, or caller/human approval is claimed. The code remains reviewable and reversible until CI evidence is exact-head GREEN. Do **not** manually rerun equivalent workflows while automatic runs exist.

## Boundary review / remaining risk

All work is within public-repository existing CI, local synthetic tests, and the normal permitted contents write path. No external GPU, paid APIs, Candidate creation/promotion, protected V2 final-evaluation gate, credential/account connection, real executor/notification, destructive operation, PR #5/#9 merge or UI work occurred. A local SQLite row digest does not authenticate an external caller, machine clock, consent, history custody or an actual exactly-once effect. Mutation checks are process-local reflective tamper fences, **not** protection against arbitrary malicious Python within the same process. Quarantine receipt checks intentionally do not retroactively roll back a committed event when a denial property changes after COMMIT; the result remains rejected.

## Next plan / 今後の方針

1. Inspect the final six-job logs **for the exact latest HEAD**; fix actual failures with minimal semantics-preserving changes, then run another independent non-UI lane while CI is pending.
2. Deepen Memory WAL/CAS/ABA manual-only post-COMMIT classification and Planner per-step persisted READ terminal/UNKNOWN evidence, including restart and cross-connection fixtures.
3. After exact-head GREEN of dependencies, evaluate Registry-bound identity + one-shot durable authorization + audit-before-mock executor composition. Do not grant real-world execution or automatic retry.
4. Audit independent Action Audit history custody/performance before replacing O(N) prefix validation. Continue V3 free-only path/approval/hash guards as review-only. Keep PR #5/#8/#9 Draft/unmerged and UI paused.

**Overall completion:** ARK/JARVIS/V3 **NOT_PASSED**; paid/hardware/frozen-evaluation approvals not supplied.

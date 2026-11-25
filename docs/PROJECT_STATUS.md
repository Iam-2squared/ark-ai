## LATEST

- **Saved at:** 2026-11-26 03:16:55 JST (Asia/Tokyo).
- **Branch / PR:** `research/jarvis-foundations` / Draft PR #8; isolated research branch, not `main`.
- **Exact work-basis HEAD:** `db7f12a406ef668b2f6bf1cdbf46715d8a406ce8` (PR #8 head and branch ref re-read immediately before this checkpoint write).
- **Checkpoint-result HEAD:** this `docs/PROJECT_STATUS.md` update commit; its exact returned SHA is reported in the invocation summary. The file intentionally does not self-reference its own commit.
- **Overall ARK state:** V1 Local Core, V2 real-model baseline, Local UI v1 and Launcher/Gate Runner retain their frozen evidence. Local-first JARVIS foundations continue in isolated/reversible Draft branches. **ARK/JARVIS overall remains NOT_PASSED.**
- **Main / UI boundary:** PR #5 remains gated Draft/unmerged. PR #8 remains Draft/unmerged. PR #9 remains Draft/unmerged and untouched at `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`; all new UI/frontend development remains paused. No `main` write or merge occurred.

## NEW work this invocation

1. **Personal Context replay carrier absent-hook custody rebase — Draft PR #602.**
   - Child branch: `research/rebase-personal-context-replay-hook-custody-20261126`; exact child HEAD: `d3147122dd95e4705aa793943abe53efedd2f0c9`.
   - Rebased the prior PR #598 package onto current PR #8 HEAD `db7f12a406ef668b2f6bf1cdbf46715d8a406ce8`. The replay source was verified byte-identical between old basis `7178d91c4ae332908dd8bd34fd9f8ab939385bd3` and current parent before applying the patch.
   - Pins true absence of witness/receipt `__new__`, `__getattribute__`, and `__getattr__` hooks with unique sentinels and retained epochs; keeps replay DDL, hash-only persistence, reservation/CAS semantics and public APIs unchanged.
   - Prior child CI run `45668069987` was GREEN on the old child HEAD only; it does not transfer. New exact-head run `45672690179`: **QUEUED**.

2. **Observation envelope + fixture-adapter absent-hook custody rebase — Draft PR #603.**
   - Child branch: `research/rebase-observation-absent-hook-custody-20261126`; exact child HEAD: `72af53e9ccbacb4e645e6db67b1c8a9edd7e6685`.
   - Rebased prior PR #599 onto current PR #8 HEAD. Both source files and the two adjusted legacy regression files were verified byte-identical between old basis `7178d91c4ae332908dd8bd34fd9f8ab939385bd3` and current parent before applying the rebase.
   - Adds absent-hook sentinels/epochs and early-denial regression coverage; corrects two existing fixture-constructor expectations to assert that substituted constructors are rejected before execution. Observation Envelope v1 schema, digest domain, privacy labels and public adapter signatures remain unchanged.
   - Prior child CI run `45668084989` was GREEN on the old child HEAD only; it does not transfer. No PR-triggered workflow run was visible for this exact child HEAD at the last read; exact-head CI is **NOT YET OBSERVED**, not PASS.

3. **Detached READ journal absent-hook custody rebase — Draft PR #604.**
   - Child branch: `research/rebase-read-journal-absent-hook-custody-20261126`; exact child HEAD: `48682cd3e0ad475c2141d73d6f29187bbe82ec2c`.
   - Rebased prior PR #600 onto current PR #8 HEAD. The journal source and adjusted Run546 recovery test were verified byte-identical between old basis `7178d91c4ae332908dd8bd34fd9f8ab939385bd3` and current parent before applying the rebase.
   - Pins absent hooks for ReadReceipt, ReadJournalWitness and ReadJournalSnapshot with a shared retained carrier epoch; preserves the synthetic local READ-only/digest-only boundary, DDL, schema, hash format, 128-row bound, CAS and public APIs.
   - Prior child CI run `45668096242` was GREEN on the old child HEAD only; it does not transfer. New exact-head run `45673239909`: **QUEUED**.

## Tests, CI and evidence

- **PR #8 pre-checkpoint parent HEAD** `db7f12a406ef668b2f6bf1cdbf46715d8a406ce8`, run `45671146217`: **QUEUED** when last read. This run does not validate the checkpoint-result HEAD; a fresh run is required for the updated parent branch.
- **PR #602** exact child HEAD `d3147122dd95e4705aa793943abe53efedd2f0c9`, run `45672690179`: **QUEUED**.
- **PR #603** exact child HEAD `72af53e9ccbacb4e645e6db67b1c8a9edd7e6685`: no PR-triggered workflow run was returned at the last read; no CI PASS is claimed.
- **PR #604** exact child HEAD `48682cd3e0ad475c2141d73d6f29187bbe82ec2c`, run `45673239909`: **QUEUED**.
- **PR #601 ToolRegistry predecessor** exact child HEAD `46c8067f7eae8aaca25deabc10701a536b1318ad`, run `45669883259`: **IN PROGRESS** at last read. All three Ubuntu Python 3.11–3.13 jobs were GREEN; all three Windows Python 3.11–3.13 pytest steps were still running. No overall PASS is claimed, and no duplicate rebase CI was started while that run remained active.
- Prior GREEN results on older child heads are historical only and are not transferred to the new rebases. No local pytest/Ruff execution, target-PC verification, live observation capture, real-model runtime, GPU query, V3 preflight/training, protected evaluation or production dispatch is claimed.

## Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1 and Launcher/Gate Runner evidence remain frozen.
- Memory v1 DDL/schema/retention, PlannerJournal schema/hash-chain/CAS, ActionAudit v1 DDL/event fields, ToolCall/PermissionGate public contracts, Observation Envelope v1, Personal Context privacy/consent boundaries and V3 Contract 1 are unchanged.
- PR #5, PR #8 and PR #9 remain Draft/unmerged. PR #9 remains untouched. No UI/frontend feature, polish, test or integration work occurred. No `main` write or merge occurred.
- PRs #602, #603 and #604 are isolated Draft children; none has been integrated into PR #8 or `main`.

## Blockers and authorization boundaries

- **Free-only:** no paid/external GPU, paid API/service, subscription, purchase or potentially billable action was started.
- PR #5 remains gated Draft/unmerged. No real Candidate adapter/weight generation, V3 preflight/training, protected V2 final-evaluation opening or Candidate promotion occurred.
- PR #601's Windows exact-head CI is still running; do not duplicate its equivalent CI or rebase that ToolRegistry source path until the run resolves. The current PR #8 parent CI was queued on the pre-checkpoint HEAD.
- Class-hook custody remains local in-process Python definition integrity only. It is not a Python sandbox, authenticated consent, trusted-clock proof, independent storage custody, fsync/power-loss durability, cross-store atomicity or exactly-once external-effect evidence.
- No new credentials/secrets/account connection, unavailable physical-PC action, destructive operation, irreversible data change, frozen-contract change or main merge occurred. All UI/frontend work remains paused; PR #9 and Local UI freezes are untouched.

## Next plan / 今後の方針

1. Inspect exact-head CI for PRs #602, #603 and #604 once useful; fix only concrete child-specific failures and launch one fresh run per corrected head.
2. After exact-head GREEN and dependency review, integrate validated children into the latest PR #8 branch one at a time. Re-read the parent HEAD immediately before each integration; keep PR #8 Draft/unmerged and never merge to `main` without approval.
3. After PR #601 run `45669883259` resolves, re-read the latest ToolRegistry source and parent HEAD, then rebase its absent-hook custody package onto the current foundation and require fresh exact-head CI.
4. Continue Memory expiry/WAL/CAS/coherent-snapshot boundaries, Planner terminal/COMMIT-UNKNOWN recovery, ActionAudit commit-outcome and PermissionGate exact-type/one-shot authorization without changing frozen schemas or contracts.
5. Continue privacy-safe Personal Context revocation/replay, proactive scheduler quarantine/recovery, disconnected mock execution and Observation fixture contracts; preserve the no-live-capture boundary.
6. Continue free-only V3 path/identity/provenance guard review without preflight, training, protected evaluation or Candidate promotion.
7. Keep all UI/frontend development paused; PR #9 and Local UI freezes remain untouched.


---

## Historical checkpoint — saved at 2026-11-25 18:02:32 JST

- **Saved at:** 2026-11-25 18:02:32 JST (Asia/Tokyo).
- **Branch / PR:** `research/jarvis-foundations` / Draft PR #8; isolated research branch, not `main`.
- **Exact work-basis HEAD:** `088322f30978da5c5094cd2b5114425107343002` (PR #8 and branch HEAD re-read immediately before this checkpoint).
- **Checkpoint-result HEAD:** this `docs/PROJECT_STATUS.md` update commit; the exact returned SHA is verified after save and reported in the invocation summary. The file intentionally does not self-reference its own commit.
- **Overall ARK state:** V1 Local Core, V2 real-model baseline, Local UI v1 and Launcher/Gate Runner retain frozen evidence. Local-first JARVIS foundations continue in isolated/reversible research branches. **ARK/JARVIS overall remains NOT_PASSED.**
- **Main / UI boundary:** PR #5 remains Draft/unmerged under its V3 gate. PR #8 remains Draft/unmerged. PR #9 remains Draft/unmerged and untouched at `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`; all new UI/frontend development remains paused. No `main` write or merge occurred.

## NEW work this invocation

1. **Run1381 — Planner COMMIT-UNKNOWN recovery evidence integrated (PR #560).**
   - Child exact HEAD: `9868834cb5b30e0bf33b359bb95ab8ddc63a382d`; exact-head CI run `45575640329`: **GREEN, 6/6**.
   - Squash-integrated into `research/jarvis-foundations`; resulting parent HEAD: `088322f30978da5c5094cd2b5114425107343002`.
   - Test/documentation-only. Covers native-COMMIT acknowledgement loss for genesis and transition, reopen/recovery, stale retry denial, ambiguous RUNNING quarantine, and event-prefix truncation. Planner source, schema and CAS semantics remain unchanged.

2. **Run1385 — Memory coherent-snapshot validator vector custody (Draft PR #564).**
   - Current child HEAD: `6410f11f1c44fded81cbfcf0fb128094e7beb603`.
   - Retains import-time request/result field, descriptor and hook vectors in private validator defaults; adds joint-vector replacement tests before request-field access and result-field assignment.
   - Memory v1 DDL/schema/retention, public request/result types, coherent transaction behavior and digest format are unchanged.

3. **Run1386 — ActionAudit event validator vector custody (Draft PR #565).**
   - Child HEAD: `ea9c8e06e22df7bda0a5e450fa8c4d0b17602ab8`.
   - Retains event field/descriptor/hook vectors in the private constructor verifier and tests joint vector replacement before SQLite access.
   - ActionAudit v1 DDL/event fields, chronology and audit-before-action semantics are unchanged.

4. **Run1387 — startup readiness constructor vector custody (Draft PR #566).**
   - Child HEAD: `50629bc200dd049d1d8a9d0ad59fa2dcd31bf439`.
   - Retains the startup carrier type/field/hook/descriptor vectors; tests joint replacement before a hostile descriptor or probe generator can execute.
   - Public readiness types/API and readiness semantics are unchanged.

5. **Run1388 — PlannerJournal stat module/predicate custody (Draft PR #567).**
   - Child HEAD: `fe09c7a4a7a4ae7a19105ce9c9618967f8273ab2`.
   - Retains the original stat module and three predicates; tests preinstalled and reentrant joint alias replacement before any substituted predicate executes.
   - PlannerJournal path semantics, schema/DDL, hash chain, CAS, transition/recovery behavior and public API are unchanged.

## Tests, CI and evidence

- **PR #8 current parent HEAD** `088322f30978da5c5094cd2b5114425107343002`, run `45580347293`: **IN PROGRESS**, 6/6 matrix jobs were running at last observation. This is the parent run after Run1381 integration; it does not validate later child heads or this checkpoint commit.
- **PR #560 / Run1381** child run `45575640329`: **GREEN, 6/6**; merged into PR #8 at parent HEAD `088322f...`.
- **PR #559 / Run1380** child HEAD `0df057641628611304bc1380c0a5a222fa3cb88f`, run `45573783862`: **GREEN, 6/6**. It contains source changes and remains Draft/isolated pending a separate dependency review; it was not integrated.
- **PR #561 / Run1382** child HEAD `59118e37f64f0d40ac5e7a3d6294d11c2384e515`, run `45576193976`: **GREEN, 6/6**, test/documentation-only; not yet integrated.
- **PR #562 / Run1383** child HEAD `8bc8bf974759ca98a9c6be12d0d961716ee654dc`, run `45576435715`: **GREEN, 6/6**, test/documentation-only; not yet integrated.
- **PR #563 / Run1384** child HEAD `419e20612d50b8016b633a496181bbc5b3ca7e5c`, run `45576826207`: **GREEN, 6/6** on the PR #5 V3 branch; PR #5 remains Draft/unmerged.
- **PR #564 / Run1385**: initial run `45579622641` **FAIL** at Ruff B010 in the test probe; next run `45579862539` **FAIL** on Ubuntu pytest because the test incorrectly restored a raw `object.__new__` descriptor, causing unrelated snapshot constructions to fail. The probe has been replaced with a reversible result-field descriptor test at child HEAD `6410f11f...`; fresh run `45581547683` is **QUEUED**. No PASS is claimed.
- **PR #565 / Run1386** child HEAD `ea9c8e06...`, run `45580148671`: **IN PROGRESS** (1/6 GREEN at last job inspection).
- **PR #566 / Run1387** child HEAD `50629bc...`, run `45580672203`: **IN PROGRESS** (2 jobs running and 4 queued at last job inspection).
- **PR #567 / Run1388** child HEAD `fe09c7a...`, run `45581080159`: **QUEUED** (6/6 queued at last observation).
- **PR #5 parent** HEAD `279232c359ec13355f684e1c8cfc081bda0a4a94`, run `45572111257`: **FAIL, 6/6** due Ruff I001 in three main merge-ref/base-owned test files: `tests/test_personal_context_replay_process_crash_run1033.py`, `tests/test_planner_journal_terminal_hard_exit_run1280.py`, and `tests/test_tool_registry_delete_seal_run1240.py`. No main edit, merge workaround or protected evaluation opening was attempted.
- No local pytest/Ruff execution, target-PC verification, real-model runtime, live capture, real backend, GPU, paid compute or production-runtime execution is claimed.

## Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1 and Launcher/Gate Runner evidence remain frozen.
- Memory v1 DDL/schema/retention, PlannerJournal schema/hash-chain/CAS contracts, ActionAudit v1 DDL/event fields, ToolCall/PermissionGate public contracts, Observation Envelope v1, Personal Context privacy/consent boundaries and V3 Contract 1 remain unchanged.
- PR #5 and PR #8 remain Draft/unmerged. PR #9 remains Draft/unmerged and untouched. No UI/frontend feature, polish, test or integration work occurred. No main write or merge occurred.
- PR #560 was integrated only into the PR #8 research branch after exact-head GREEN. No protected V2 final evaluation, real Candidate generation/promotion, credential/account connection, physical hardware action or destructive operation occurred.

## Blockers and authorization boundaries

- **Free-only:** no paid/external GPU, paid API/service, subscription, purchase or potentially billable action was started.
- PR #5's main merge-ref Ruff I001 failure is confined to the three base-owned files above. Do not edit `main`, copy/re-home those tests, or merge PR #5 without the required ownership/approval path. Protected V2 evaluation remains closed.
- PR #559 is green but changes source; keep it isolated until its Personal Context/Observation dependency review is complete.
- PRs #561 and #562 are exact-head GREEN test/documentation-only children. Parent PR #8 CI run `45580347293` is still in progress, so neither child was integrated in this invocation.
- PR #564's two initial failures are recorded above; its corrected exact head awaits run `45581547683`. PRs #565–#567 are still running/queued; no child PASS is claimed for them.
- Planner COMMIT-UNKNOWN evidence simulates acknowledgement loss after native SQLite COMMIT; it does not prove fsync/power-loss durability or exactly-once external effects. Startup readiness leases remain synthetic diagnostics only. Registry deletion checks remain local in-process object-integrity evidence. Stat/path checks are not atomic dirfd custody or process isolation.
- No new credentials/secrets/account connections, unavailable physical-PC actions, destructive operations, frozen-contract changes, protected evaluation openings, Candidate promotion or main merge occurred.

## Next plan / 今後の方針

1. Revisit PR #8 run `45580347293` when useful. After it is GREEN, re-read the latest parent HEAD and integrate test-only PRs #561 and #562 one at a time; launch fresh parent CI after each integration and switch to a non-conflicting lane while it runs.
2. Review green PR #559's source changes in Personal Context and Observation separately before any integration. Do not treat its child CI as proof of combined parent behavior.
3. Inspect PR #564 run `45581547683` and PRs #565–#567 exact-head CI; fix only concrete child-specific failures, then continue another independent non-UI lane.
4. Review PR #563 against the current PR #5 branch, but keep #5 Draft/unmerged; do not edit main to bypass the base-owned Ruff blocker or open protected V2 evaluation/training.
5. Continue Memory CAS/event/expiry/purge recovery, Planner terminal/recovery, ToolRegistry/PermissionGate, restart-safe authorization, trusted-clock audit-before-action, Personal Context revocation, proactive scheduler and Observation fixture boundaries.
6. Keep UI/frontend work paused; PR #9 and Local UI freezes remain untouched.

---

## Historical checkpoint — saved at 2026-11-25 17:12:11 JST

- **Saved at:** 2026-11-25 17:12:11 JST (Asia/Tokyo).
- **Branch / PR:** `research/jarvis-foundations` / Draft PR #8; isolated research branch, not `main`.
- **Exact work-basis HEAD:** `11d72bef1b69df06ed0c0102d6154fc4d44a0214` (PR #8 head re-read immediately before this checkpoint).
- **Checkpoint-result HEAD:** this `PROJECT_STATUS.md` update commit; GitHub returns the exact resulting SHA after save, which is recorded in the invocation summary. The file intentionally does not self-reference its own commit.
- **Overall ARK state:** V1 Local Core, V2 real-model baseline, Local UI v1 and Launcher/Gate Runner retain frozen evidence. Local-first JARVIS foundations continue in isolated/reversible branches. **ARK/JARVIS overall remains NOT_PASSED.**
- **Main / UI boundary:** PR #5 remains Draft/unmerged under its V3 gate. PR #8 remains Draft/unmerged. PR #9 remains Draft/unmerged and untouched at `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`; UI/frontend work remains paused. No main write or merge occurred.

## NEW work this invocation

1. **Run1381 — Planner COMMIT-UNKNOWN recovery rebase (Draft PR #560).**
   - Child branch: `research/run1381-planner-commit-unknown-rebase-20261125`.
   - Exact final child HEAD: `9868834cb5b30e0bf33b359bb95ab8ddc63a382d`.
   - Test/documentation-only rebase onto the exact PR #8 work-basis above; verified unchanged PlannerJournal source blob `d27298a3c6ed5b9d8421ac50944b966a279c8db5`.
   - Covers native-COMMIT acknowledgement loss for genesis and transition, reopen/recovery, stale retry denial, ambiguous RUNNING quarantine, and event-prefix truncation rejection.

2. **Run1382 — disconnected startup-readiness lease regression rebase (Draft PR #561).**
   - Child branch: `research/run1382-startup-readiness-lease-rebase-20261125`.
   - Exact final child HEAD: `59118e37f64f0d40ac5e7a3d6294d11c2384e515`.
   - Test/documentation-only rebase; production evaluator and lease reviewer blobs are unchanged (`bcbe936127ed8ef526862b2be73ecd75aac45dea`, `facddb02cb5c0a53517ca8f4a00a7138a2fab7a2`).
   - Covers freshness/expiry boundaries, clock rollback, exact carriers, dependency blocking, schema mismatch and reflected snapshot/authority mutation.

3. **Run1383 — ToolRegistry deletion-seal regression rebase (Draft PR #562).**
   - Child branch: `research/run1383-tool-registry-delete-seal-rebase-20261125`.
   - Exact final child HEAD: `8bc8bf974759ca98a9c6be12d0d961716ee654dc`.
   - Test/documentation-only rebase; unchanged parent ToolRegistry source blob `2bbb88f6d87a5c51c7b025072e10c998ebc400b9`.
   - Covers ordinary sealed-slot deletion denial, reflective registration-map deletion before binding, replaced class deletion guard denial, and inert mock backend behavior.

4. **Run1384 — V3 preflight parser guard self-custody rebase (Draft PR #563, child of PR #5).**
   - Child branch: `research/run1384-v3-preflight-guard-self-custody-rebase-20261125`.
   - Exact final child HEAD: `419e20612d50b8016b633a496181bbc5b3ca7e5c`; exact parent PR #5 basis: `279232c359ec13355f684e1c8cfc081bda0a4a94`.
   - Adds a keyword-only retained parser-guard default and compares both mutable module bindings before invoking the guard or parsing synthetic report bytes. Adds a test that replaces both bindings with one no-op and instruments the loader.
   - No model/tokenizer load, torch runtime, GPU query, preflight execution, training, adapter/weight generation, Candidate, or protected V2 evaluation.

## Tests, CI and evidence

- **PR #8 work-basis head** `11d72bef1b69df06ed0c0102d6154fc4d44a0214`, CI run `45571957861`: **GREEN, 6/6** Windows/Linux × Python 3.11–3.13. This validates the parent work-basis, not the later checkpoint commit.
- **PR #559 concurrent child** `0df057641628611304bc1380c0a5a222fa3cb88f`, run `45573783862`: **IN PROGRESS** at last observation (5 jobs GREEN; Windows/Python 3.12 still running).
- **PR #560 / Run1381** `9868834cb5b30e0bf33b359bb95ab8ddc63a382d`, run `45575640329`: **IN PROGRESS** (3 jobs GREEN; 3 still running).
- **PR #561 / Run1382** `59118e37f64f0d40ac5e7a3d6294d11c2384e515`, run `45576193976`: **IN PROGRESS / QUEUED** (5 jobs running; 1 queued; no completed result observed).
- **PR #562 / Run1383** `8bc8bf974759ca98a9c6be12d0d961716ee654dc`, run `45576435715`: **QUEUED, 6/6**.
- **PR #563 / Run1384** `419e20612d50b8016b633a496181bbc5b3ca7e5c`, run `45576826207`: **QUEUED, 6/6**.
- **PR #5 parent** `279232c359ec13355f684e1c8cfc081bda0a4a94`, run `45572111257`: **FAIL, 6/6** due Ruff I001 on the main merge-ref files `tests/test_personal_context_replay_process_crash_run1033.py`, `tests/test_planner_journal_terminal_hard_exit_run1280.py`, and `tests/test_tool_registry_delete_seal_run1240.py`. The Ubuntu/Python 3.11 log confirms these are import-order findings in base-owned files; this is the previously known main-merge-ref ownership blocker, not a failure in Run1384's child source/test.
- No local pytest/Ruff, target-PC, real-model, live-capture, real-backend, GPU, paid-compute or production-runtime execution is claimed. No child PASS is claimed before its final exact-head CI completes. The checkpoint update itself triggers a new PR #8 CI run after this save.

## Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1 and Launcher/Gate Runner evidence remain frozen.
- Memory v1 DDL/schema/retention, ToolCall and PermissionGate public contracts, Observation Envelope v1, Personal Context privacy/consent boundaries, ActionAudit v1 DDL/event fields, and V3 Contract 1 remain unchanged.
- PRs #560, #561 and #562 are test/documentation-only. PR #563 changes only the V3 preflight verifier's retained guard argument/check and adds synthetic regression coverage; it does not change Contract 1, report schema, dataset, runtime or training parameters.
- PR #5 and PR #8 remain Draft/unmerged. PR #9 remains Draft/unmerged and untouched. No UI/frontend feature, polish, test or integration work occurred. No main write or merge occurred.

## Blockers and authorization boundaries

- **Free-only:** no paid/external GPU, paid API/service, subscription, purchase or potentially billable action was started.
- PR #5's current merge-ref Ruff I001 failure is confined to three base-owned test files listed above. Do not edit `main`, copy/re-home those tests, or merge PR #5 without the required ownership/approval path. PR #5 remains Draft/unmerged; protected V2 evaluation remains closed.
- PRs #559–#563 remain Draft and isolated until their own final exact-head CI is GREEN. PR #8's GREEN run applies to work-basis HEAD `11d72bef...`, not the later checkpoint commit.
- Planner COMMIT-UNKNOWN fixtures simulate acknowledgement loss after native SQLite COMMIT; they do not prove fsync/power-loss durability or exactly-once external effects.
- Startup readiness leases are synthetic diagnostics only, not trusted time, authenticated identity, startup authorization, dispatch, notification or hardware readiness.
- ToolRegistry deletion checks are local in-process object-integrity evidence, not process isolation, authenticated backend identity or permission.
- V3 parser guard tests are synthetic only and do not invoke model loading, GPU, preflight, training or Candidate creation. No automatic Candidate promotion or human-review decision is inferred.
- No new credentials/secrets/account connections, unavailable physical-PC actions, destructive operations, frozen-contract changes or protected evaluation openings occurred.

## Next plan / 今後の方針

1. Inspect the final exact-head CI for PRs #559–#563 when useful; fix only concrete child-specific failures, then switch to an independent non-conflicting lane while reruns execute.
2. After exact-head GREEN and dependency review, integrate validated test-only PRs #560, #561 and #562 into the PR #8 research branch only. Re-read latest PR #8 HEAD immediately before each integration and run fresh parent CI. Keep PR #8 Draft/unmerged.
3. For PR #563, verify its exact-head CI and review the parser-guard rebase against the current PR #5 branch. Keep PR #5 Draft/unmerged; do not open protected evaluation or training gates and do not modify main to bypass the merge-ref blocker.
4. Continue Memory row/event integrity, WAL/CAS/ABA, expiry/purge commit-outcome recovery and coherent snapshots without changing Memory v1 DDL or retention.
5. Continue Planner terminal propagation and crash recovery, ToolRegistry/exact-type PermissionGate, durable authorization, trusted-clock audit-before-action and occurrence/replay protection.
6. Continue disconnected/mock execution, startup readiness, privacy-safe Personal Context, proactive scheduler state and Observation/multimodal fixture contracts.
7. Continue free-only V3 approval/path/identity/reproducibility guards; no real Candidate adapter/weight generation, protected V2 evaluation or promotion.
8. Keep all UI/frontend work paused; PR #9 and Local UI freezes remain untouched.

---

## Historical checkpoint — saved at 2026-11-25 12:02:32 JST

- **Saved at:** 2026-11-25 12:02:32 JST (Asia/Tokyo).
- **Branch / PR:** `research/jarvis-foundations` / Draft PR #8; isolated research branch, not `main`.
- **Exact work-basis HEAD:** `83f73303778a47430203095b246a94d90cc4bd81` (PR #8 head re-read immediately before this checkpoint; includes the Run1352 Memory child integration).
- **Checkpoint-result HEAD:** this `PROJECT_STATUS.md` update commit; the exact SHA is returned by GitHub after save and reported in the invocation summary. The file intentionally does not self-reference its own commit.
- **Overall ARK state:** V1 Local Core, V2 real-model baseline, Local UI v1 and Launcher/Gate Runner retain their frozen evidence. Local-first JARVIS foundations continue in isolated/reversible work. **ARK/JARVIS overall remains NOT_PASSED.**
- **Main / UI boundary:** PR #5 remains Draft/unmerged under its V3 gate. PR #8 remains Draft/unmerged. PR #9 remains Draft/unmerged and untouched; UI/frontend work remains paused. No main write or merge occurred.

## NEW work this invocation

1. **Run1352 — exact Memory metadata ingress integrated into PR #8.**
   - Child PR #531 exact HEAD `8f369e70a69426c358a4b5114d11ef9fb63e67a0`; CI run `45532803522`: **GREEN, 6/6** Windows/Linux × Python 3.11–3.13.
   - Squash-integrated into `research/jarvis-foundations`; integration commit / current work-basis HEAD: `83f73303778a47430203095b246a94d90cc4bd81`.
   - Exact mapping-proxy admission, 64-entry cap and exact built-in string key/value snapshot occur before reconstruction, serialization, hashing, SQLite open or clock access. Memory v1 DDL/schema/API/event/retention remain unchanged.

2. **Run1353 — Observation private text-encoder custody (Draft PR #532).**
   - Child branch: `research/run1353-observation-text-encoder-custody-20261125`; exact child HEAD: `78ebf994d05462a8065dfdd03aa376c8b0438465`.
   - Retains the import-time bounded UTF-8 encoder, rejects a replaced module binding after metadata preflight, and invokes the retained callable before private fixture text can reach a substituted encoder.
   - Regression coverage includes a preinstalled replacement and a replacement installed during metadata preflight. Observation Envelope v1 and the byte-budget algorithm are unchanged.
   - Exact-head CI run `45535410668`: **IN PROGRESS** (4/6 jobs GREEN; 2 Windows jobs still running at checkpoint).

3. **Run1354 — production PlannerJournal stat-policy custody (Draft PR #533).**
   - Child branch: `research/run1354-planner-production-stat-custody-20261125`; exact child HEAD: `3a3555830a18d9c15f7d6330c8226ce97262ab1e`.
   - Pins the import-time stat module and exact `S_ISDIR`/`S_ISLNK`/`S_ISREG` predicates; rechecks after `lstat`, metadata reads, predicate calls and missing database/sidecar branches.
   - Regression coverage includes preinstalled and reentrant predicate/module substitutions, missing-path callbacks and a valid existing path. Planner journal schema, hash chain, CAS, transition and recovery contracts are unchanged.
   - Exact-head CI run `45536086845`: **IN PROGRESS** (3/6 jobs GREEN; 3 jobs still running at checkpoint).

4. **Run1355 — Personal Context replay-ledger stat-policy custody (Draft PR #534).**
   - Child branch: `research/run1355-personal-context-replay-stat-custody-20261125`; exact child HEAD: `a79bee67b8c58b6b827469ef82eeab2da4e1d4fd`.
   - Adds import-time stat module/predicate checks to the replay protocol, uses retained classifiers, and rechecks after metadata callbacks and missing database/sidecar outcomes.
   - Synthetic regression coverage includes preinstalled/reentrant changes and a valid existing path. Replay schema, hash chain, binding, CAS, reservation, retention and denial-only receipts are unchanged.
   - Exact-head CI run `45536363929`: **IN PROGRESS** (1/6 jobs GREEN; 5 jobs still running at checkpoint).

5. **Run1356 — ActionAudit reentrant stat-policy custody (Draft PR #535).**
   - Child branch: `research/run1356-action-audit-reentrant-stat-custody-20261125`; exact child HEAD: `cbb19bf5bd713c05e56c0c82436e6f5fd5fcc1ee`.
   - Uses retained stat predicates and rechecks after `lstat`, metadata access, classifier calls and missing-path branches; preserves the bounded sidecar recheck.
   - Synthetic tests cover reentrant predicate/module replacement, metadata accessors, missing database/sidecar and a valid path. ActionAudit v1 DDL, event fields, digest identity, chronology and audit-before-action ordering are unchanged.
   - Exact-head CI run `45536671862`: **IN PROGRESS** (6/6 jobs running at checkpoint).

## Tests, CI and evidence

- PR #8 pre-integration head `8c969bbd2dc83c800b7bad998fd8e480aec941e7`, run `45533045246`: **GREEN, 6/6**.
- PR #531 exact child head `8f369e70a69426c358a4b5114d11ef9fb63e67a0`, run `45532803522`: **GREEN, 6/6**; squash integration commit `83f73303778a47430203095b246a94d90cc4bd81`.
- PR #8 post-integration head `83f73303778a47430203095b246a94d90cc4bd81`, run `45536986740`: **QUEUED** when last observed; it predates this checkpoint-only documentation update.
- PR #532 exact child head/run `78ebf994d05462a8065dfdd03aa376c8b0438465` / `45535410668`: **IN PROGRESS, 4/6 GREEN**.
- PR #533 exact child head/run `3a3555830a18d9c15f7d6330c8226ce97262ab1e` / `45536086845`: **IN PROGRESS, 3/6 GREEN**.
- PR #534 exact child head/run `a79bee67b8c58b6b827469ef82eeab2da4e1d4fd` / `45536363929`: **IN PROGRESS, 1/6 GREEN**.
- PR #535 exact child head/run `cbb19bf5bd713c05e56c0c82436e6f5fd5fcc1ee` / `45536671862`: **IN PROGRESS, 0/6 completed**.
- PR #5 prior exact-head run `45532003801`: **FAIL** on Ruff I001 in the three main-merge-ref files already recorded below; no main write, test removal or merge was attempted.
- No local pytest/Ruff, physical-PC, real-model, live-capture, real-backend, paid-compute or production-runtime execution is claimed. The checkpoint commit's own exact-head CI is created after this save and is reported in the invocation summary when observed.

## Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1 and Launcher/Gate Runner evidence remain frozen.
- Frozen ToolCall/PermissionGate public contracts, Memory v1 DDL/schema, Observation Envelope v1, Personal Context consent/privacy boundaries, ActionAudit v1 DDL/event fields and V3 Contract 1 were not changed.
- PR #5 and PR #8 remain Draft/unmerged. PR #9 remains Draft/unmerged and untouched. No UI/frontend feature, polish, test or integration work occurred.
- No protected V2 final evaluation, real Candidate generation/promotion, credentials, new account connection, physical hardware action, destructive operation or frozen-contract change occurred.

## Blockers and authorization boundaries

- **Free-only:** no paid/external GPU, paid API/service, subscription, purchase or potentially billable action was started.
- PRs #532–#535 remain Draft and isolated until their own exact-head CI is GREEN. Their tests are synthetic/disconnected and do not grant dispatch, consent, trusted-time or external-effect authority.
- PR #8 post-Run1352 integration CI run `45536986740` was queued at last observation; integration is not yet revalidated on the combined parent head.
- PR #5 remains blocked at the main merge-ref ownership boundary: run `45532003801` reported Ruff I001 in main-base files absent from the inspected PR #5 branch. Explicit approval is required before any main ownership/import-order change. PR #5 stays Draft/unmerged; protected V2 evaluation remains closed.
- SQLite pathname preflights are not atomic dirfd custody or a sandbox. Process-exit/COMMIT-UNKNOWN tests do not prove fsync/power-loss durability, trusted time, authenticated consent, independent custody, cross-store atomicity or exactly-once external effects.
- No automatic Candidate promotion, real backend dispatch or human-review decision is inferred from these CI results.

## Next plan / 今後の方針

1. Inspect exact-head CI for PRs #532–#535 and PR #8 run `45536986740` when useful; fix only concrete failures with the smallest semantics-preserving change, then switch to a non-conflicting lane while reruns execute.
2. After each child is exact-head GREEN, review and integrate it into the PR #8 research branch only; re-read latest HEAD before each integration and run fresh parent CI. Keep PR #8 Draft/unmerged.
3. Continue Memory CAS/concurrency/expiry/ABA and coherent-snapshot work; Planner crash recovery and ambiguous-RUNNING quarantine; immutable ToolRegistry/exact-type PermissionGate; durable authorization and audit-before-action; disconnected mock execution; privacy-safe Personal Context; proactive scheduler state; and Observation fixture contracts.
4. Continue free-only V3 approval/path/identity/reproducibility guards without opening protected evaluation or promoting a Candidate.
5. Keep PR #5 Draft/unmerged and PR #9 untouched; UI/frontend work remains paused.


## Historical checkpoint — saved at 2026-11-25 11:26:19 JST

- **Saved at:** 2026-11-25 11:26:19 JST (Asia/Tokyo).
- **Branch / PR:** `research/jarvis-foundations` / Draft PR #8; isolated research branch, not `main`.
- **Exact work-basis HEAD:** `d8079f8b96bfa0875e0ad77372088b003e1c6550` (PR #8 branch HEAD re-read immediately before this checkpoint update).
- **Checkpoint-result HEAD:** this `PROJECT_STATUS.md` update commit; the exact SHA is returned by GitHub after save and recorded in the run summary. The file intentionally does not self-reference its own commit.
- **Overall ARK state:** V1 Local Core, V2 real-model baseline, Local UI v1 and Launcher/Gate Runner retain their previously frozen evidence. Local-first JARVIS foundations continue in isolated, reversible branches. **ARK/JARVIS overall remains NOT_PASSED.**
- **Main / UI boundary:** `main` HEAD `ecd72fced0f3e575e504331f9f7bf1c4f0187614` was rechecked and not modified. PR #5 and PR #8 remain Draft/unmerged. PR #9 remains Draft/unmerged and untouched; UI/frontend work remains paused.

## NEW work this invocation

1. **Run1347 — ActionAudit outcome-boundary regression integrated into PR #8.**
   - Draft PR #526 was reviewed as test/documentation-only against the existing `_validate_outcome` source and bounded persisted-row checks.
   - Exact child-head CI run `45523117005`: **GREEN, 6/6** Windows/Linux × Python 3.11–3.13.
   - Squash-integrated into `research/jarvis-foundations`; resulting PR #8 work-basis HEAD: `d8079f8b96bfa0875e0ad77372088b003e1c6550`.
   - ActionAudit v1 schema and public event fields remain unchanged; no trusted-time, independent-custody or external-effect claim is added.

2. **Run1348 — Personal Context revocation no-open regression correction integrated into its parent branch.**
   - Draft PR #527 corrected stale assertions so the helper-identity guard must reject before SQLite open and before validator callback.
   - Exact child-head CI run `45528689065`: **GREEN, 6/6**.
   - Squash-integrated into Draft PR #524 branch at commit `c77f37e65392ec794566e583f82026cad60519d6`.
   - Fresh PR #524 exact-head CI run `45531939444`: **IN PROGRESS**. PR #523 remains FAIL on its prior head; no integration into #523 or #8 is claimed.

3. **Run1349 — V3 preflight-report strict JSON parser integrated into gated PR #5 branch.**
   - Draft PR #528 added recursive duplicate-key rejection, finite-float parsing and import-original parser/guard identity checks, plus synthetic tests/docs. No torch, model, GPU, preflight, training or Candidate path was invoked.
   - Exact child-head CI run `45529326895`: **GREEN, 6/6**.
   - Squash-integrated into `research/v3-learning-evaluation`; resulting PR #5 HEAD: `cff9cfb71e15fa7f614eec7674177bbf58f0aa27`.
   - Fresh PR #5 run `45532003801`: **FAIL, 6/6 jobs** because Ruff I001 is reported in three main-merge-ref test files absent from the inspected PR #5 branch: `tests/test_personal_context_replay_process_crash_run1033.py`, `tests/test_planner_journal_terminal_hard_exit_run1280.py`, and `tests/test_tool_registry_delete_seal_run1240.py`. This is the existing main/V3 merge-ref ownership blocker, not evidence to copy JARVIS modules into `main`, remove tests, or merge PR #5.

4. **Run1351 — nested V3 preflight-report symlink-ancestor regression (Draft PR #530).**
   - Adds a synthetic test where the immediate report parent is a real directory reached through a symlinked grandparent; it requires denial before `os.open` and preserves target sentinel bytes.
   - Production source and V3 Contract 1 are unchanged.
   - Exact child-head CI run `45532275776`: **GREEN, 6/6**. PR #530 remains Draft/unmerged and isolated while the PR #5 main-merge-ref blocker remains unresolved.

5. **Run1352 — exact Memory metadata admission (Draft PR #531).**
   - Adds an exact `MappingProxyType` carrier check, a 64-entry bound and exact built-in string key/value admission in `SQLiteMemoryStore.put`, before validated-write reconstruction, serialization, hashing, SQLite open or clock access.
   - Adds synthetic regressions for string-subclass keys/values and a reflectively replaced hostile mapping, plus evidence documentation.
   - No Memory v1 DDL/schema/API/event/retention change. Exact child HEAD: `8f369e70a69426c358a4b5114d11ef9fb63e67a0`; CI run `45532803522`: **IN PROGRESS**.

6. **Run1350 — exact one-shot token-field admission remains isolated (Draft PR #529).**
   - Exact token ID/request ID/expiry validation is performed before PermissionGate grant iteration and before synthetic occurrence registry binding/digest/SQLite reservation.
   - Exact child HEAD: `e21100195d68535956527d664448f1ebaad49ff0`; CI run `45530953609`: **IN PROGRESS**. No authenticated issuer, trusted clock, cross-store atomicity or exactly-once external effect is claimed.

7. **Duplicate-child cleanup — closed without merging after byte-identity review.**
   - Closed PRs #491, #492, #494, #495, #496 and #497 after their changed source/test files were compared against the current PR #8 branch and found byte-identical.
   - Closed PRs #491/#495 (Planner), #492/#496 (Proactive), and #494/#497 (Personal Context) without deleting branches or historical CI evidence.

## Tests, CI and evidence

- PR #8 previous exact-head CI on `f5ca69fa46855a53315b5149d7cfecef4e941a23`, run `45528595100`: **GREEN, 6/6**; this includes the earlier Run1345 mock-backend-return hard-exit regression.
- PR #8 current work-basis HEAD `d8079f8b96bfa0875e0ad77372088b003e1c6550`, run `45531903137`: **IN PROGRESS** after Run1347 integration.
- PR #524 updated exact head `c77f37e65392ec794566e583f82026cad60519d6`, run `45531939444`: **IN PROGRESS**.
- PR #529 exact head `e21100195d68535956527d664448f1ebaad49ff0`, run `45530953609`: **IN PROGRESS**.
- PR #530 exact head `2a6875f2069a0a33565cd97761d581beaaddca2b`, run `45532275776`: **GREEN, 6/6**.
- PR #531 exact head `8f369e70a69426c358a4b5114d11ef9fb63e67a0`, run `45532803522`: **IN PROGRESS**.
- PR #5 exact head `cff9cfb71e15fa7f614eec7674177bbf58f0aa27`, run `45532003801`: **FAIL, 6/6 jobs**, Ruff I001 on the three main-merge-ref files listed above. The existing main import-order/ownership path requires explicit approval; no main write or merge was attempted.
- PR #523 prior exact-head run `45513867238`: **FAIL**; PR #524 is the corrective child and requires its own GREEN result before any dependency integration.
- PR #525 Run1345 exact-head run `45522184303`: **GREEN** on its child head; its mock-only test/evidence package is already represented in the PR #8 history.
- PR #526 run `45523117005`, PR #527 run `45528689065`, and PR #528 run `45529326895`: each **GREEN, 6/6** on its exact child head before the integrations described above.
- No local pytest/Ruff, physical-PC, real-model, live-capture, real-backend, paid-compute or production-runtime execution is claimed.

## Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1 and Launcher/Gate Runner evidence remain frozen.
- Frozen ToolCall/PermissionGate public contracts, Memory v1 schema/DDL and retention, Observation Envelope v1, Personal Context consent/privacy boundaries, and V3 Contract 1 were not changed.
- PR #5 remains Draft/unmerged; no protected V2 final evaluation, real Candidate generation or promotion was opened.
- PR #8 remains Draft/unmerged; all JARVIS foundation work remains isolated from `main`.
- PR #9 remains Draft/unmerged and untouched. No frontend feature, polish, test or integration work was performed.

## Blockers and authorization boundaries

- **Free-only:** no paid/external GPU, paid API/service, subscription, purchase or potentially billable action was started.
- No real Candidate adapter/weight generation, protected V2 evaluation opening, Candidate promotion, credentials/secrets, new account connection, physical hardware action, destructive/irreversible operation, frozen-contract change or main merge occurred.
- PR #5 remains blocked at the main merge-ref ownership boundary: current CI reports Ruff import-order failures in main-base files absent from the PR #5 branch. PR #483 is the separate main import-order/ownership path and is not merged; explicit approval is required before any main change.
- PR #523 is not GREEN. PR #524's corrected child head is in CI; integrate it into #523 only after exact-head GREEN, then rerun #523 before any PR #8 integration.
- PR #530 is GREEN but remains isolated until the PR #5 parent merge-ref blocker is resolved through an approved path. PR #5 remains Draft/unmerged.
- Synthetic SQLite/process-exit and fixture tests do not prove fsync/power-loss durability, trusted time, authenticated consent, independent custody, cross-store atomicity, erasure, or exactly-once external effects.

## Next plan / 今後の方針

1. Inspect the exact-head CI results for PR #8 run `45531903137`, PR #524 run `45531939444`, PR #529 run `45530953609`, and PR #531 run `45532803522` when useful; fix only concrete failures and immediately switch to a non-conflicting lane while reruns execute.
2. If PR #531 is GREEN, review and integrate its Memory metadata admission package into the PR #8 research branch only; keep PR #8 Draft/unmerged.
3. If PR #524 is GREEN, integrate it into PR #523 only and run fresh exact-head CI on #523. Integrate #523 into PR #8 only after that exact head is GREEN and reviewed.
4. Keep PR #530's GREEN nested-ancestor regression isolated until the PR #5 main-merge-ref ownership blocker is resolved through an approved path. Do not merge PR #5 or open protected V2 evaluation.
5. Continue Memory CAS/concurrency/expiry/ABA and coherent-snapshot review; Planner COMMIT-UNKNOWN recovery and ambiguous-RUNNING quarantine; immutable ToolRegistry/PermissionGate; durable authorization and audit-before-action; disconnected mock execution; privacy-safe Personal Context; proactive scheduler state; and Observation fixture contracts.
6. Keep PR #5 and PR #8 Draft/unmerged, PR #9 untouched, and all UI/frontend work paused.



## Historical checkpoint — saved at 2026-11-25 10:01:03 JST

- **Saved at:** 2026-11-25 10:01:03 JST (Asia/Tokyo).
- **Checkpoint branch / PR:** `research/jarvis-foundations` / Draft PR #8; isolated research branch, not `main`.
- **Exact work-basis HEAD:** `4d6f94257bd87b23ebbbc1e76ba5f04ccb1bef2d` (latest PR #8 branch head immediately before this checkpoint write).
- **Checkpoint-result HEAD:** this `PROJECT_STATUS.md` update commit; its exact SHA is returned by GitHub after save and recorded in the run summary. The file intentionally does not self-reference its own commit.
- **Overall ARK state:** V1, V2, Local UI v1 and Launcher/Gate Runner retain their previously reviewed/frozen evidence. JARVIS foundations remain isolated/reversible. **ARK/JARVIS overall remains NOT_PASSED.** No protected V2 evaluation, real Candidate generation/promotion or later milestone PASS is claimed.
- **Main/UI boundary:** `main` HEAD is `ecd72fced0f3e575e504331f9f7bf1c4f0187614` and was not modified. PR #9 remains Draft/unmerged and untouched; UI/frontend development remains paused.

## NEW work this invocation

1. **Run1342 — startup snapshot method custody + public-reader pre-dispatch guard integrated (PR #522).**
   - Child branch/head: `research/run1342-startup-method-guard-combined-20261125` / `e5565caa92b5f91f5ec28025cb45210baf15f7ac`.
   - Exact-head CI run `45513927591` / run 7558: **GREEN, 6/6** Windows/Linux × Python 3.11–3.13.
   - Source reviewed; no frozen schema/contract change or live startup/dispatch authority added. Squash integration into PR #8: `f809c1c2cd6d186cb317752607cab904a9fd0f92`.
   - Superseded children PR #518 and #519 were closed without merging; their historical branches/evidence remain.

2. **Run1346 — V3 free-only source revalidation recorded.**
   - Exact PR #5 branch HEAD inspected: `f7252fbe7d5f65c640fed41bbb5b3cc7ae817296`; exact-head CI run `45484069708`: **FAIL**.
   - Updated `docs/JARVIS_FOUNDATION_GAP_MATRIX.md` with current source findings: learning code-tree traversal already rejects symlink/reparse entries before recursion; preflight report output checks already walk reparse ancestors; most V3 JSON readers already reject duplicate keys/canonical drift.
   - Recorded the remaining strictness inconsistency in `training_cli._verify_preflight_report()`, plus unresolved hash-then-use, runtime chat-template, attempt/receipt and main-merge-ref ownership gaps. Read-only audit only; no V3 source, runtime, torch, model, GPU, training or Candidate action.

3. **Run1344 — Personal Context revocation helper-custody regression correction (Draft PR #524).**
   - Child branch: `research/run1344-personal-context-revocation-guard-tests-20261125`; latest saved child HEAD at checkpoint: `d1c47b8c68e924cf082a2de4dab11b8b7a669c32`.
   - Updates five synthetic regression modules so replaced digest/validator helpers are rejected before callback dispatch; asserts no scope/path mutation and no veto write. Production source, Memory v1 schema/DDL and privacy policy are unchanged.
   - Initial exact-head run `45520692351`: **FAIL at Ruff E501 only** (three unique overlong lines repeated across the six jobs; pytest did not run). Formatting/callback-count corrections saved; fresh run `45521650446`: **IN_PROGRESS** at checkpoint.

4. **Run1345 — mock backend-return / pre-completion-audit hard-exit regression (Draft PR #525).**
   - Child branch: `research/run1345-mock-backend-return-precompletion-hard-exit-20261125`; latest saved child HEAD at checkpoint: `2553bfb6e9c2f0be1d91d59816411785c92decdb`.
   - Adds a spawned-process profile-hook boundary proving the mock backend returned before exit at entry to the second audit append; cold recovery retains the occurrence and pre-action event, does not invent a completion event, and denies reuse of the old one-shot before a new gate/backend call. Production executor, registry, gate and audit schemas are unchanged.
   - Initial exact-head run `45521290805`: **FAIL at Ruff E501 only** (one 447-character docstring line; pytest did not run). Docstring wrapped; fresh run `45522184303`: **QUEUED** at checkpoint.

5. **Duplicate-child cleanup.**
   - PR #515 closed without merge after all six changed files were verified byte-identical to the current PR #8 branch; Run1319/Run1325 are already integrated via PR #520.
   - PR #518/#519 closed as superseded by integrated PR #522. No source history was deleted.

## Tests, CI and evidence

- PR #522 Run1342 exact-head CI `45513927591`: **GREEN, 6/6**.
- PR #523 Run1343 exact-head CI `45513867238`: **FAIL**, 15 stale callback/diagnostic expectations across six matrix jobs; no PASS is claimed. PR #524 is the test-only correction child and must validate independently before integration.
- PR #524 initial Run1344 CI `45520692351`: **FAIL at Ruff E501 only**; corrected head run `45521650446`: **IN_PROGRESS**.
- PR #525 initial Run1345 CI `45521290805`: **FAIL at Ruff E501 only**; corrected head run `45522184303`: **QUEUED**.
- PR #8 Run1346 documentation-audit head `4d6f94257bd87b23ebbbc1e76ba5f04ccb1bef2d`, CI `45522118070`: **QUEUED** at checkpoint. This run predates the current checkpoint commit.
- PR #5 exact-head run `45484069708`: **FAIL**; V3 remains NOT_PASSED and gated. No V3 runtime or paid compute is claimed.
- PR #515 exact-head run `45494873858`: GREEN 6/6 on its duplicate child; not integrated from that child.
- No local pytest/Ruff, physical-PC, real-model, live capture, external backend or production runtime execution is claimed.

## Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1 and Launcher/Gate Runner evidence remain frozen.
- Frozen ToolCall/PermissionGate public contracts, Memory v1 schema/DDL and retention policy, Observation Envelope v1, Personal Context consent/privacy boundaries and V3 Contract 1 were not changed.
- PR #522 is integrated only into PR #8, not `main`. PR #8 remains Draft/unmerged.
- PR #5 remains Draft/unmerged; no protected V2 final evaluation, Candidate generation or Candidate promotion was opened.
- PR #9 remains Draft/unmerged and untouched. No UI features, polish, frontend tests or UI integration were performed.

## Blockers and authorization boundaries

- **Free-only:** no paid/external GPU, paid API/service, subscription, purchase or potentially billable action was started.
- No new credentials/secrets/account connection, physical hardware action, destructive/irreversible operation, frozen-contract change, protected evaluation opening, Candidate promotion or main merge occurred.
- PR #523 is not green; integrate PR #524 into #523 only after its exact-head CI is GREEN, then rerun #523 before any integration into PR #8.
- PR #525 is not green yet; keep it isolated until exact-head CI is GREEN, then integrate into PR #8 only.
- V3 main merge-ref ownership remains blocked because current main lacks foundation modules imported by some copied test paths. Do not copy those modules into main, delete/disable tests, merge PR #5, or open protected V2 evaluation.
- QUEUED/IN_PROGRESS/FAIL is not PASS. Synthetic SQLite/process-exit evidence does not prove fsync/power-loss durability, trusted time, independent custody, authenticated consent, cross-store atomicity or exactly-once external effects.

## Next plan / 今後の方針

1. Inspect PR #524 run `45521650446` and PR #525 run `45522184303` when results are available; fix only concrete failures, then switch to a non-conflicting lane while reruns execute.
2. If PR #524 is GREEN, integrate it into PR #523 only and run fresh exact-head CI on the corrected PR #523 branch. Integrate PR #523 into PR #8 only after that exact head is GREEN and reviewed; never merge to main.
3. If PR #525 is GREEN, integrate it into PR #8 only after source/test review; preserve the explicit mock-only evidence boundary.
4. After the V3 main-base ownership blocker is resolved through an approved path, implement the strict preflight-report parser/duplicate-key regression and nested symlink-ancestor test on an isolated PR #5 child. No runtime or compute.
5. Continue local-first Planner crash recovery, Memory durability/privacy, immutable ToolRegistry/PermissionGate, durable authorization and audit-before-action, disconnected mock execution, Personal Context, proactive scheduler and Observation backend contracts.
6. Keep PR #5 Draft/unmerged, PR #8 Draft/unmerged, PR #9 untouched and all UI/frontend work paused.

## Historical checkpoint — saved at 2026-11-25 08:56:59 JST

- **Saved at:** 2026-11-25 08:56:59 JST (Asia/Tokyo).
- **Checkpoint branch / PR:** `research/jarvis-foundations` / Draft PR #8; isolated research branch, not `main`.
- **Exact work-basis HEAD:** `4ee3f7e7f82f5348810c303c3e1e1a3c27cbde26` (latest PR #8 branch head immediately before this checkpoint write).
- **Checkpoint-result HEAD:** this `PROJECT_STATUS.md` update's commit; the exact resulting branch HEAD is verified immediately after save and recorded in the run summary. This file does not self-reference its own commit hash.
- **Overall ARK state:** V1, V2, Local UI v1 and Launcher/Gate Runner retain their previously reviewed/frozen evidence. JARVIS foundations continue in isolated, reversible Draft work. **ARK/JARVIS overall remains NOT_PASSED.** No protected V2 evaluation, Candidate promotion or later milestone PASS is claimed. No merge to `main`.
- **Main/UI boundary:** `main` HEAD is `ecd72fced0f3e575e504331f9f7bf1c4f0187614` and was not modified. PR #9 remains Draft/unmerged and untouched; all work this invocation was non-UI.

## NEW work this invocation

1. **Run1337 — mock completion-audit COMMIT hard-exit regression integrated (PR #517)**
   - Child branch/head: `research/run1337-mock-completion-audit-hard-exit-20261125` / `da7509fe0094b32d9998661b3a9479f9ca6c45e5`.
   - Squash integration into `research/jarvis-foundations`: `6bd2703c0ba830545e577e0333e7ea71fbb6be12`.
   - Exact-head CI run `45503899320`: **GREEN, 6/6** Windows/Linux × Python 3.11–3.13. Synthetic test-only boundary; no production executor change and no external exactly-once claim.

2. **Run1319 / Run1325 — Memory query-text pre-access and diagnostic correction integrated (PR #520)**
   - Child branch/head: `research/run1340-memory-query-preaccess-rebase-20261125` / `da98d53bec346ccbcb5de503575f9ea07f443d93`.
   - Squash integration: `404a24aa6e18583586068ddedd47138917ec6cd6`.
   - Exact-head CI run `45504156637`: **GREEN, 6/6**. Exact query epoch is checked before read-only SQLite open; diagnostic wording and two synthetic regression expectations are aligned. Memory v1 schema/DDL/public contracts remain unchanged.

3. **Run1336 — Observation UTF-8 chunk-boundary regression integrated (PR #521)**
   - Child branch/head: `research/run1341-observation-utf8-rebase-20261125` / `a33b30fdec8fe54f08b81dd43b175d30ca2c6527`.
   - Squash integration: `4ee3f7e7f82f5348810c303c3e1e1a3c27cbde26`.
   - Exact-head CI run `45504310253`: **GREEN, 6/6**. Test/evidence-only; no capture adapter or Observation Envelope v1 change.

4. **Run1342 — combined startup snapshot method custody and public-reader pre-dispatch guard (Draft PR #522)**
   - Child branch: `research/run1342-startup-method-guard-combined-20261125`; current exact child HEAD: `e5565caa92b5f91f5ec28025cb45210baf15f7ac`.
   - Combines the Run1338 method identity pin and Run1339 direct-reader guard. The old Draft PRs #518 and #519 remain open pending this combined package's validation; no integration is claimed.
   - Previous exact-head run `45513482941` / run 7554: **FAIL at Ruff only** (two E501 lines and one I001 import block). All three lint findings were corrected in the current child head.
   - Fresh exact-head run `45513927591` / run 7558: **QUEUED**. No PASS is claimed.

5. **Run1343 — Personal Context revocation digest/schema-validator custody (Draft PR #523)**
   - Child branch: `research/run1343-personal-context-revocation-validator-custody-20261125`; current exact child HEAD: `241a2f7ff6e0f21b73762b42a6dc228341ddc191`.
   - Pins the scope-digest helper and SQLite schema validator before constructor/revoke/read SQLite access. The constructor guard is executable and positioned after its docstring, before path/SQLite work. No Memory schema/DDL or consent contract change.
   - Fresh exact-head run `45513867238` / run 7556: **QUEUED**. No PASS is claimed.

## Tests, CI and evidence

- PR #8 work-basis HEAD `4ee3f7e7f82f5348810c303c3e1e1a3c27cbde26`, exact-head CI run `45512631829` / run 7553: **IN PROGRESS** at checkpoint preparation.
- PR #517 Run1337 run `45503899320`: **GREEN, 6/6**.
- PR #520 Run1319/1325 run `45504156637`: **GREEN, 6/6**.
- PR #521 Run1336 run `45504310253`: **GREEN, 6/6**.
- PR #518 Run1338 run `45503772771`: **FAIL**; six matrix jobs failed on 29 legacy assertions expecting the previous later-stage diagnostic, while the new method-identity guard rejects earlier. The combined Run1342 package updates those regressions and adds direct-reader pre-dispatch checks.
- PR #519 Run1339 run `45497903814`: **FAIL at Ruff I001** in two test files on the old dependent branch; the combined PR #522 has corrected import grouping.
- PR #522 initial Run1342 run `45513482941`: **FAIL at Ruff only**; corrected. Fresh exact-head run `45513927591`: **QUEUED**.
- PR #523 Run1343 exact-head run `45513867238`: **QUEUED**.
- PR #5 run `45484069708`: **FAIL at Ruff I001** in all six matrix jobs on three V3/main-base test paths.
- PR #483 run `45422941503`: **FAIL at pytest collection**; the main base lacks `ark.personal_context_offline_preview` and `ark.agency` modules imported by the three test files. This remains a source/test ownership blocker, not a reason to copy foundation modules into `main`.
- No local pytest/Ruff execution, physical-PC verification, live capture, real model runtime, paid compute or external service action is claimed.

## Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1 and Launcher/Gate Runner evidence remain frozen as previously reviewed.
- Frozen ToolCall/PermissionGate public contracts, Memory v1 schema/DDL and retention policy, Observation Envelope v1, Personal Context consent/privacy boundaries and V3 Contract 1 were not changed.
- PR #517, #520 and #521 are integrated only into the PR #8 research branch, not `main`.
- PR #8 remains Draft/unmerged. PR #5 remains Draft/unmerged; no protected V2 evaluation, real Candidate generation or promotion was opened.
- PR #9 remains Draft/unmerged and untouched. UI/frontend development remains paused.
- PR #522 and #523 remain Draft/unmerged children pending exact-head CI and review. PR #518/#519 remain open and unmerged as superseded predecessors until the combined package validates.

## Blockers and authorization boundaries

- **Free-only boundary:** no paid/external GPU, paid API/service, subscription, purchase or potentially billable action was started.
- No real Candidate adapter/weight generation, protected V2 final-evaluation opening, Candidate promotion, credentials/secrets, new account connection, unavailable physical-PC action, destructive operation or irreversible data change occurred.
- Startup Run1338/1339 is not integrated; use combined PR #522 only after exact-head GREEN and source review. Its synthetic readiness result remains diagnostic, not startup/dispatch authority.
- Personal Context Run1343 is isolated in PR #523 until exact-head GREEN and review. The local revocation ledger remains a synthetic veto fixture, not authenticated consent or trusted storage.
- V3's main-base ownership blocker remains unresolved; PR #5 and #483 stay Draft/unmerged. Do not merge to `main` or copy foundation modules into it.
- QUEUED/IN PROGRESS is not PASS. SQLite COMMIT/process-exit tests cover only their named synthetic native-COMMIT boundaries; they do not prove fsync/power-loss durability, trusted time, independent custody, authenticated consent, cross-store atomicity or exactly-once external effects.

## Next plan / 今後の方針

1. Inspect exact-head CI for PR #522 and #523 once useful results are available; fix only concrete failures, then immediately work a non-conflicting lane while reruns execute.
2. After Run1342 PR #522 is exact-head GREEN and reviewed, integrate it into PR #8 only; then mark/close the superseded #518/#519 children without touching `main`.
3. After Run1343 PR #523 is exact-head GREEN and reviewed, integrate it into PR #8 only.
4. Continue local-first Memory durability/privacy, Planner crash recovery, immutable ToolRegistry/PermissionGate, durable authorization and audit-before-action, disconnected mock execution, Personal Context, proactive scheduler and observation backend contracts.
5. Keep V3 approval/path/identity/reproducibility guards isolated while the main-base ownership blocker remains unresolved. PR #5 stays Draft/unmerged and all paid/real-Candidate gates stay closed.
6. Keep UI paused: no frontend features, polish, tests or integration.


## Historical checkpoint — saved at 2026-11-25 07:49:25 JST

- **Saved at:** 2026-11-25 07:49:25 JST (Asia/Tokyo).
- **Checkpoint branch / PR:** `research/jarvis-foundations` / Draft PR #8; isolated research branch, not `main`.
- **Exact work-basis HEAD:** `44d6cbdb6a554d42ba1c86c1f646a12fe4487f4f` (PR #8 exact head immediately before this checkpoint write).
- **Checkpoint-result HEAD:** the GitHub commit created by this `PROJECT_STATUS.md` update; its exact returned SHA is recorded in the run summary. This file does not self-reference its own commit hash.
- **Overall ARK state:** V1, V2, Local UI v1 and Launcher/Gate Runner retain their previously reviewed/frozen PASS evidence. JARVIS foundations continue in isolated, reversible Draft branches. **ARK/JARVIS overall remains NOT_PASSED.** No protected V2 evaluation, Candidate promotion, or later milestone PASS is claimed. No merge to `main`.
- **Main/UI boundary:** `main` is unchanged by this invocation. PR #9 remains Draft/unmerged and untouched; all new work is non-UI.

## NEW work this invocation

1. **Draft PR #518 — Run1338 startup snapshot method-custody lint correction**
   - Branch: `research/run1338-startup-snapshot-method-custody-20261125`.
   - Exact child head before the correction: `9d531b38f9e943401956c27e60379b40dbdec58e`; fix commit: `23302646e144bcabbe24e09a4d7adea8dc1105e3`.
   - Exact-head run `45497687313` failed at Ruff I001 in the new test import block; pytest was skipped. Added the required separation between third-party and first-party imports only. No production semantics changed.
   - Fresh exact-head CI run `45503772771`: IN PROGRESS at checkpoint time.

2. **Draft PR #517 — Run1337 mock completion-audit COMMIT hard-exit fixture correction**
   - Branch: `research/run1337-mock-completion-audit-hard-exit-20261125`.
   - Exact child head before the correction: `5d2ef03019a9fe43ecbcde5a016d1f04efa12e29`; fix commit: `da7509fe0094b32d9998661b3a9479f9ca6c45e5`.
   - Exact-head run `45496873298` failed in the synthetic child because the `CommitExit` SQLite proxy forwarded attribute reads but not attribute writes; `row_factory` was assigned to the proxy rather than the underlying SQLite connection, causing tuple rows during audit-history validation. The test proxy now forwards non-`connection` assignments to the wrapped connection. This is a test-harness correction, not a production audit change.
   - Fresh exact-head CI run `45503899320`: IN PROGRESS at checkpoint time.

3. **Draft PR #520 — Run1340 Memory query pre-access package rebased onto current PR #8**
   - Branch: `research/run1340-memory-query-preaccess-rebase-20261125`.
   - Exact current parent work-basis: `44d6cbdb6a554d42ba1c86c1f646a12fe4487f4f`; exact child head: `da98d53bec346ccbcb5de503575f9ea07f443d93`.
   - Rebased the six-file package from stale PR #515 without changing its intended semantics: exact query-epoch validation before read-only SQLite open, inexact query-text rejection before SQLite/expiry-clock access, corrected “during read” diagnostics, and synthetic pre-access regressions.
   - Predecessor PR #515 exact-head run `45494873858` was GREEN, 6/6, on its old child head only; that evidence does not transfer to #520.
   - Fresh exact-head CI run `45504156637`: IN PROGRESS at checkpoint time.

4. **Draft PR #521 — Run1341 Observation UTF-8 chunk-boundary package rebased onto current PR #8**
   - Branch: `research/run1341-observation-utf8-rebase-20261125`.
   - Exact current parent work-basis: `44d6cbdb6a554d42ba1c86c1f646a12fe4487f4f`; exact child head: `a33b30fdec8fe54f08b81dd43b175d30ca2c6527`.
   - Rebased the two-file test/evidence package from stale PR #516. It corrects the multibyte fixture so the chunk loop is exercised and adds accepted/one-byte-under UTF-8 budget boundaries. Test/documentation-only; no capture adapter or frozen Observation contract change.
   - Predecessor PR #516 exact-head run `45495516730` was GREEN, 6/6, on its old child head only; that evidence does not transfer to #521.
   - Fresh exact-head CI run `45504310253`: QUEUED at checkpoint time.

5. **Run1339 startup-reader follow-up remains blocked on its dependency**
   - Existing Draft PR #519 exact child head: `5111c49c353b1753627cd31793309ebfd3f9d83c`.
   - Exact-head run `45497903814` failed at Ruff I001 in both the parent Run1338 test and the Run1339 test; pytest was skipped. The Run1338 import grouping is corrected in PR #518, but PR #519 still needs its own import grouping correction and a rebase onto the corrected, exact-head-GREEN #518 parent. No integration or PASS is claimed.

## Tests, CI and evidence

- PR #8 exact current-head run `45498250484`: GREEN, 6/6 Windows/Linux × Python 3.11–3.13. This validates the current research parent at work-basis HEAD `44d6cbdb6a554d42ba1c86c1f646a12fe4487f4f`, not the new child PRs.
- PR #517 original run `45496873298`: FAIL in the test subprocess due to the proxy's missing attribute-write forwarding; fixed on the child branch. Fresh run `45503899320`: IN PROGRESS.
- PR #518 original run `45497687313`: FAIL at Ruff I001 only; fixed on the child branch. Fresh run `45503772771`: IN PROGRESS.
- PR #519 run `45497903814`: FAIL at Ruff I001 in two test files; stale dependency branch remains unintegrated.
- PR #520 run `45504156637`: IN PROGRESS on exact child head `da98d53bec346ccbcb5de503575f9ea07f443d93`.
- PR #521 run `45504310253`: QUEUED on exact child head `a33b30fdec8fe54f08b81dd43b175d30ca2c6527`.
- Predecessor PR #515 run `45494873858` and PR #516 run `45495516730`: GREEN, 6/6 on their predecessor child heads only; no result transfers to #520 or #521.
- No local pytest/Ruff execution, physical-PC verification, live capture, real model runtime, paid compute, or external service action is claimed.

## Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1 and Launcher/Gate Runner evidence remain frozen as previously reviewed.
- Frozen ToolCall/PermissionGate public contracts, Memory v1 schema/DDL and retention policy, Observation Envelope v1, Personal Context privacy boundaries and V3 Contract 1 were not changed.
- PR #5 remains Draft/unmerged; no protected V2 evaluation, real Candidate generation or promotion was opened.
- PR #8 remains Draft/unmerged. PRs #517–#521 remain isolated Draft children; none is integrated into #8 or `main`.
- PR #9 remains Draft/unmerged and untouched. UI/frontend development remains paused.

## Blockers and authorization boundaries

- **Free-only boundary:** no paid/external GPU, paid API/service, subscription, purchase or potentially billable action was started.
- No real Candidate adapter/weight generation, protected V2 final-evaluation opening, Candidate promotion, credentials/secrets, new account connection, unavailable physical-PC action, destructive operation or irreversible data change occurred.
- PR #519 remains dependent on exact-head GREEN for PR #518 and requires its own Ruff correction/rebase.
- QUEUED/IN PROGRESS is not PASS. No child package is integrated before exact-head validation and dependency review.
- SQLite process-exit/COMMIT-UNKNOWN tests establish only the specific synthetic native-COMMIT boundaries exercised; they do not prove fsync/power-loss durability, trusted time, independent custody, authenticated consent, cross-store atomicity or exactly-once external effects.
- V3's previously recorded main-base source/test ownership blocker remains unchanged; keep PR #5 Draft/unmerged and protected gates closed.

## Next plan / 今後の方針

1. Inspect exact-head CI for #517, #518, #520 and #521 once useful results are available; fix only concrete failures and switch to an independent lane while reruns execute.
2. After #518 is exact-head GREEN, rebase Run1339 onto its corrected head, fix the child test's import grouping, and require fresh exact-head CI before considering that dependent package.
3. Rebase #517 onto the latest PR #8 parent after its fixture correction is GREEN; preserve the synthetic-only evidence boundary.
4. After #520 and #521 exact-head GREEN plus source review, integrate validated packages into the PR #8 research branch only. Keep PR #8 Draft/unmerged.
5. Continue free-only Memory durability/privacy, Planner crash recovery, ToolRegistry/PermissionGate, audit-before-action, Personal Context, proactive and observation back-end work. Keep V3 approval/path/identity/reproducibility guards isolated while the main-base ownership issue remains unresolved.
6. Keep UI paused: no frontend feature, polish, test or integration work.


## Historical checkpoint archive

### Previous checkpoint — saved at 2026-11-25 07:09:08 JST

- **Saved at:** 2026-11-25 07:09:08 JST (Asia/Tokyo).
- **Checkpoint branch / PR:** `research/jarvis-foundations` / Draft PR #8; isolated research branch, not `main`.
- **Exact work-basis HEAD:** `2af77814dd01f0959d99a86ddcf9387d94e8053c` (current exact PR #8 head before this checkpoint write).
- **Checkpoint-result HEAD:** the GitHub commit created by this `PROJECT_STATUS.md` update; the exact returned SHA is recorded in the run summary. This file does not self-reference its own commit SHA.
- **Overall ARK state:** V1, V2, Local UI v1 and Launcher/Gate Runner retain their previously reviewed/frozen PASS evidence. JARVIS foundations continue in isolated, reversible Draft branches. **ARK/JARVIS overall remains NOT_PASSED.** No protected V2 evaluation or later milestone PASS is claimed.
- **Main boundary:** no write, merge, protected evaluation, or Candidate action against `main` was performed in this invocation.

### NEW work this invocation

1. **Draft PR #517 — disconnected mock completion-audit COMMIT hard-exit regression (Run1337)**
   - Branch: `research/run1337-mock-completion-audit-hard-exit-20261125`.
   - Exact child HEAD: `5d2ef03019a9fe43ecbcde5a016d1f04efa12e29`; work basis: PR #8 HEAD `2af77814dd01f0959d99a86ddcf9387d94e8053c`.
   - Adds a subprocess exit immediately after the second native ActionAudit COMMIT, after the exact in-process mock backend call and before the completion append returns. Cold recovery checks both audit events and the durable occurrence, denies reuse of the old one-shot before a fresh gate/backend call, and permits a distinct new one-shot for the same canonical request.
   - Test-only plus evidence note; no production executor, schema, or public contract change.
   - CI run `45496873298`: IN PROGRESS at checkpoint time.

2. **Draft PR #518 — startup snapshot method custody (Run1338)**
   - Branch: `research/run1338-startup-snapshot-method-custody-20261125`.
   - Exact child HEAD: `9d531b38f9e943401956c27e60379b40dbdec58e`; work basis: PR #8 HEAD `2af77814dd01f0959d99a86ddcf9387d94e8053c`.
   - Pins the import-original `StartupSnapshot._assert_integrity`, `state`, and `root_blockers` method identities in the startup implementation guard. Tests reject method substitution before probe iteration and reject a forged-digest lease before the substituted integrity callback runs.
   - CI run `45497687313`: QUEUED at checkpoint time.

3. **Draft PR #519 — direct startup snapshot reader guard (Run1339), stacked on PR #518**
   - Branch: `research/run1339-startup-reader-integrity-guard-20261125`.
   - Exact child HEAD: `5111c49c353b1753627cd31793309ebfd3f9d83c`; exact parent basis: PR #518 HEAD `9d531b38f9e943401956c27e60379b40dbdec58e`.
   - Adds a guard call at the beginning of the original `StartupSnapshot.state()` and `root_blockers()` methods, before dispatch through `_assert_integrity`; adds direct-reader regressions. This follow-up is isolated and does not alter PR #518's exact head.
   - CI run `45497903814`: QUEUED at checkpoint time. Validate in dependency order: #518 before #519.

4. **V3 CI blocker reconciliation (read-only)**
   - PR #5 exact head remains `f7252fbe7d5f65c640fed41bbb5b3cc7ae817296`; parent CI run `45484069708` is FAIL across all six jobs on Ruff I001 in three files present on `main` but absent from the V3 branch checkout.
   - Confirmed the three files exist on `main`, not on `research/v3-learning-evaluation`.
   - Existing Draft PR #483 (`fix/run1303-main-ci-import-groups-20261125`, head `82edf57452ffae117cb4dfaff3bb26aac5987c91`) removes the three import separators, but its exact-head CI run `45422941503` is FAIL at pytest collection because the main base lacks the JARVIS modules those tests import. No merge or workaround was attempted; the main/foundation ownership boundary remains blocked pending explicit integration approval.

### Tests, CI and evidence

- PR #8 exact-head CI run `45494409207`: IN PROGRESS; three Windows jobs remained in progress at the last inspection, with the Ubuntu matrix jobs successful.
- PR #515 Memory child run `45494873858`: IN PROGRESS.
- PR #516 Observation child exact head `e3d4674c3e01dc315f647e0f6da39dd8a34a4317`: no workflow run surfaced at the last inspection; no PASS is claimed.
- PR #517 Run1337 exact-head run `45496873298`: IN PROGRESS.
- PR #518 Run1338 exact-head run `45497687313`: QUEUED.
- PR #519 Run1339 exact-head run `45497903814`: QUEUED.
- PR #5 exact-head run `45484069708`: FAIL; all six matrix jobs failed at Ruff I001 on the three main-base test paths.
- PR #483 exact-head run `45422941503`: FAIL; Ruff passes, but pytest collection cannot import the JARVIS foundation modules absent from its main base.
- No local pytest/Ruff execution, physical-PC verification, real model runtime, external service, or paid compute result is claimed.

### Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1 and Launcher/Gate Runner evidence remain frozen as previously reviewed.
- Frozen ToolCall/PermissionGate public contracts, Memory v1 schema/DDL, Observation Envelope v1, Personal Context privacy boundaries and V3 Contract 1 were not changed.
- PR #5 remains Draft/unmerged; no protected V2 evaluation, real Candidate generation or promotion was opened.
- PR #8 remains Draft/unmerged. PRs #517–#519 are isolated Draft children; none is merged into #8 or `main`.
- PR #9 remains Draft/unmerged and untouched. UI/frontend development remains paused.

### Blockers and authorization boundaries

- **Free-only boundary:** no paid/external GPU, paid API/service, subscription, purchase, or potentially billable action was started.
- No real Candidate adapter/weight generation, protected V2 final-evaluation opening, Candidate promotion, credentials/secrets, new account connection, unavailable physical-PC action, destructive operation, or irreversible data change occurred.
- **V3 main-base blocker:** PR #5's merge-ref lint paths belong to `main`; the import-only PR #483 then fails collection because the foundation modules are not on `main`. Keep #5 and #483 Draft/unmerged; do not copy isolated foundation modules into V3 or merge to main without the explicit integration decision.
- **CI evidence boundary:** QUEUED/IN PROGRESS is not PASS. Do not integrate #517–#519 until each exact child head is GREEN and its dependency order is satisfied.
- **Architecture boundary:** the new readiness methods remain synthetic diagnostics only; the mock executor remains exact in-process mock only. Neither establishes trusted time, independent custody, authenticated consent, power-loss durability, or exactly-once external effects.

### Next plan / 今後の方針

1. Inspect PR #517 run `45496873298` once useful results are available; correct only a concrete exact-head failure, then return to an independent lane while validation runs.
2. Validate PR #518 run `45497687313` before PR #519 run `45497903814`; integrate the startup reader follow-up only after its parent and child exact-head evidence is GREEN.
3. Revisit PR #8 run `45494409207`, PR #515 Memory run `45494873858`, and PR #516's missing run evidence without duplicating workflows.
4. Continue non-UI free work on Memory durability/privacy, Planner crash recovery, ToolRegistry/PermissionGate, audit-before-action, disconnected execution, Personal Context, proactive state and Observation fixture contracts.
5. Keep V3 free-only guards isolated until the main-base source/test ownership blocker is resolved with explicit approval; keep PR #5 Draft/unmerged and all protected evaluation/Candidate gates closed.

### Previous checkpoint — saved at 2026-11-25 05:53:35 JST


- **Saved at:** 2026-11-25 05:53:35 JST (Asia/Tokyo)
- **Checkpoint branch / PR:** `research/jarvis-foundations` / Draft PR #8; isolated research branch, not `main`.
- **Exact work-basis HEAD:** `05d65aa006fb4d429abce70869d4271db5bed825` (PR #509 ActionAudit outcome-boundary regression/evidence package integrated into the PR #8 research branch).
- **Checkpoint-result HEAD:** the GitHub commit created by this `PROJECT_STATUS.md` update; the exact returned SHA is recorded in the run summary. This file does not self-reference its own commit SHA.
- **Overall ARK state:** V1, V2, Local UI v1 and Launcher/Gate Runner retain their previously reviewed/frozen PASS evidence. JARVIS core foundations continue in isolated, reversible research branches. **ARK/JARVIS overall remains NOT_PASSED.** No protected V2 evaluation was opened; no later milestone PASS is claimed.
- **Main remains unchanged by this invocation:** no merge to `main`.

### NEW work this invocation

1. **Draft PR #509 — ActionAudit outcome-boundary regressions integrated into PR #8**
   - Child exact HEAD: `d4fbc8dfefcdc6de3af1e7b3649722bf9e8299c9`.
   - Exact-head CI run `45474932797`: GREEN, 6/6 Windows/Linux × Python 3.11–3.13.
   - Integrated by squash merge into `research/jarvis-foundations`; resulting PR #8 work-basis HEAD: `05d65aa006fb4d429abce70869d4271db5bed825`.
   - PR #8 remains Draft/unmerged. Parent-head CI run `45483923713` is IN PROGRESS.

2. **Draft PR #507 — V3 preflight report-path validation integrated into PR #5**
   - Child exact HEAD: `1efb0d25f329035035921241acdd3b95fc9a406d`.
   - Exact-head CI run `45474021116`: GREEN, 6/6 Windows/Linux × Python 3.11–3.13.
   - Integrated by squash merge into `research/v3-learning-evaluation`; resulting PR #5 head: `f7252fbe7d5f65c640fed41bbb5b3cc7ae817296`.
   - PR #5 remains Draft/unmerged and its protected evaluation/training gates remain closed.
   - Parent-head CI run `45484069708` is FAIL. Retrieved job logs report Ruff I001 in three JARVIS test paths, but those paths were absent from the inspected tree for the reported head `f7252fbe7d5f65c640fed41bbb5b3cc7ae817296`. Treat this as an unresolved CI checkout/evidence mismatch; do not attribute it to PR #507 or claim a clean PR #5 head.

3. **Draft PR #510 — Memory query pre-access validation rebased onto current PR #8**
   - Exact child HEAD: `1cdf172797fbb32183ae779d854613fdf9dd89f5`.
   - Replays the narrow pre-SQLite query-epoch check, “during read” diagnostics, and synthetic str-subclass rejection tests.
   - CI run `45484412532`: IN PROGRESS.
   - Supersedes stale PR #505; its description was corrected to disclose the production-source change and stale base.

4. **Draft PR #511 — PermissionGate / ToolRegistry lookup-hook custody**
   - Exact child HEAD: `baaf80d9f4e54e26e2863d97222e51af7fa20049`.
   - Pins class/instance `__getattribute__` and optional `__getattr__` lookup hooks before registered authorization can invoke callbacks, iterate grants or consume a one-shot token.
   - CI run `45484936865`: IN PROGRESS.

5. **Draft PR #512 — Planner COMMIT-UNKNOWN recovery regressions**
   - Exact child HEAD: `28bd01428f6e3d8d9f3fc99d7138f2139d198836`.
   - Covers lost genesis/transition COMMIT acknowledgements, ambiguous RUNNING recovery, no automatic replay/dispatch, stale-transition conflicts and event-prefix truncation.
   - CI run `45485005891`: QUEUED.

6. **Draft PR #513 — Personal Context revocation exact-scope ingress**
   - Exact child HEAD: `cb9a7e7c0e06c9b939eb668628529fed3bb8e45a`.
   - Rejects non-exact owner/namespace text carriers before frozen MemoryScope validation, SQLite access or row writes.
   - CI run `45485106994`: QUEUED.

7. **Draft PR #514 — Proactive privacy fixture digest binding**
   - Exact child HEAD: `baaa0c0ec8d5b862de0be6dda3bb95c44823d859`.
   - Binds the synthetic private observation's actual SHA-256 digest through the hard-exit child process and checks the recovered digest.
   - CI run `45485244434`: QUEUED.

### Tests, CI and evidence

- PR #509 child run `45474932797`: GREEN, 6/6; integrated into PR #8 at work-basis HEAD `05d65aa006fb4d429abce70869d4271db5bed825`.
- PR #8 exact current-head run `45483923713`: IN PROGRESS.
- PR #507 child run `45474021116`: GREEN, 6/6; integrated into PR #5 at head `f7252fbe7d5f65c640fed41bbb5b3cc7ae817296`.
- PR #5 current-head run `45484069708`: FAIL; Ruff I001 is reported in the downloaded logs, with an unresolved mismatch between the reported paths and the inspected commit tree.
- PR #510 run `45484412532`: IN PROGRESS.
- PR #511 run `45484936865`: IN PROGRESS.
- PR #512 run `45485005891`: QUEUED.
- PR #513 run `45485106994`: QUEUED.
- PR #514 run `45485244434`: QUEUED.
- Historical predecessor runs for PR #500–#503 and #505 were GREEN on their old heads only; none of those results transfers to the new rebased child heads.
- PR #508 run `45474394318`: FAIL during pytest collection with missing `ark.personal_context_offline_preview` and `ark.agency` imports on the V3 branch. Those modules belong to the separate JARVIS foundation branch; do not weaken the tests or copy them into V3 merely to silence the failure.
- No local pytest/Ruff result, physical-PC verification, real model runtime, paid compute or external service action is claimed in this invocation.

### Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1 and Launcher/Gate Runner evidence remain frozen as previously reviewed.
- Frozen ToolCall/PermissionGate public contracts, Memory v1 schema/DDL, Observation Envelope v1, Personal Context privacy boundaries and V3 Contract 1 were not changed.
- PR #5 remains Draft/unmerged; no protected V2 evaluation, real Candidate generation or promotion was opened.
- PR #8 remains Draft/unmerged; this checkpoint and child packages do not merge to `main`.
- PR #9 remains Draft/unmerged and untouched. UI/frontend development remains paused.

### Blockers and authorization boundaries

- **Free-only boundary:** no paid/external GPU, paid API/service, subscription, purchase or potentially billable action was started.
- No real Candidate adapter/weight generation, protected V2 final-evaluation opening, Candidate promotion, credentials/secrets, new account connection, unavailable physical-PC action, destructive operation or irreversible data change occurred.
- PR #5 parent CI failure and PR #508's V3/JARVIS dependency mismatch remain explicit blockers; neither is hidden by the green child-head results.
- SQLite process-exit/COMMIT-UNKNOWN tests establish only the specific synthetic native-COMMIT recovery boundaries exercised. They do not prove power-loss/fsync durability, trusted time, independent custody, authenticated consent, cross-store atomicity or exactly-once external effects.
- No automatic promotion, real backend dispatch or human-review decision is inferred from test results.

### Next plan / 今後の方針

1. Inspect exact-head CI for PRs #510–#514 and PR #8 once useful results are available; fix only concrete failures, then switch to an independent non-conflicting lane while reruns execute.
2. After exact-head GREEN and dependency review, integrate validated child packages into the PR #8 research branch only. Keep PR #8 Draft/unmerged and preserve exact-head evidence.
3. For PR #5, reconcile run `45484069708` against the exact checkout/tree and reported Ruff paths before making any correction. Keep PR #5 Draft/unmerged and do not open protected evaluation or training gates.
4. Keep the V3/JARVIS test dependency boundary explicit. Re-home JARVIS-only tests to the foundation branch where their source modules exist; do not weaken tests or make V3 depend on an unproven foundation merge.
5. Continue independent free-only work on Observation fixture byte/lineage guards, startup readiness leases, occurrence/replay protection and disconnected mock execution.
6. Keep UI paused; no frontend features, polish, tests or integration.

### LATEST

- **Saved at:** 2026-11-24 20:40:23 JST (Asia/Tokyo)
- **Checkpoint branch / PR:** `research/jarvis-foundations` / Draft PR #8; this is an isolated research branch, not `main`.
- **Exact work-basis HEAD:** `ddc4a574437361059552615ceb44936a628555dc` (Run1280 Planner terminal hard-exit regression integration).
- **Checkpoint-result HEAD:** the GitHub commit created by this `PROJECT_STATUS.md` update; its exact returned SHA is verified after the write and reported in the run summary. This file does not self-reference its own commit hash.
- **Overall ARK state:** V1, V2 and Local UI v1 retain their reviewed/frozen PASS evidence. JARVIS foundations continue in isolated, reversible research branches. **ARK/JARVIS overall remains NOT_PASSED.** No V3+ protected evaluation was opened and no later milestone PASS is claimed.

### NEW work this invocation

All new packages are test/documentation-only rebases onto the exact Run1280 foundation HEAD above. No production source, schema, DDL, public API or frozen contract was changed.

1. **Draft PR #462 — startup readiness lease regression correction**
   - Current child HEAD: `7b71f62204a293cb5c978b6524aec3d64d95ea97`.
   - Corrected one invalid negative-case fixture: age 1 ms with a 100 ms maximum is valid, and added a positive assertion for that case.
   - Corrected the descriptor-substitution assertion to expect the stronger, earlier `readiness result authority epoch changed before review` denial.
   - Added `docs/JARVIS_RUN1282_STARTUP_READINESS_LEASE.md`.
   - Initial run `45382547475` failed in pytest with those two test-expectation errors; Ruff passed. No production defect was reported. Fresh run `45385945866` is QUEUED.

2. **Draft PR #463 — durable-ledger native-COMMIT hard-exit regression bundle**
   - Current child HEAD: `78f1d782d2415ba8ded06401a6607ae6e56b5630`.
   - Rebased synthetic hard-exit tests for Memory scoped expiry purge, Personal Context replay reservation, and proactive eligibility state.
   - Added `docs/JARVIS_RUN1283_LEDGER_NATIVE_COMMIT_RECOVERY.md`.
   - Initial run `45385180828` failed Ruff F401 for one now-unused `hashlib` import after a test assertion simplification. The import was removed without changing test semantics. Fresh run `45385683618` is QUEUED.

3. **Draft PR #464 — ToolRegistry deletion-seal regression**
   - Child HEAD: `605842017b112f09619928c80209b0564cdafd68`.
   - Rebased ordinary slot-deletion, reflective registration-map deletion and replaced-guard checks; inert backend remains uncalled.
   - Added `docs/JARVIS_RUN1284_TOOL_REGISTRY_DELETE_SEAL.md`.
   - Exact-head CI run `45385289828` is IN PROGRESS.

4. **Draft PR #465 — Personal Context final revocation veto**
   - Child HEAD: `ee9fa010ef9deceb904cf8c3e37d90ac6e21fee5`.
   - Rebased the synthetic race regression in which a revocation appended during final retained-history review must veto projection return.
   - Added `docs/JARVIS_RUN1285_CONTEXT_FINAL_VETO.md`.
   - Exact-head CI run `45385417961` is IN PROGRESS.

5. **Draft PR #466 — Observation fixture UTF-8 allocation**
   - Child HEAD: `8ec985d4b7290fdc59b8f309678b25e90a699837`.
   - Rebased ASCII/multibyte byte-boundary, early oversize rejection, surrogate rejection and pre-hash denial tests for the disconnected fixture adapter.
   - Added `docs/JARVIS_RUN1286_OBSERVATION_UTF8.md`.
   - Exact-head CI run `45385598574` is IN PROGRESS.

### Tests, CI and evidence

- **Foundation basis:** PR #460 merge commit `ddc4a574437361059552615ceb44936a628555dc`; exact-head CI run `45379837623` was GREEN, 6/6 jobs. This is the current research-branch basis, not a main merge.
- **PR #462:** run `45382547475` FAIL (Ruff passed; pytest had 2 expectation failures, 19,472 passed and 151 skipped in the observed Windows/Python 3.11 job). Test-only correction committed at `31ac179ffef6fc536f45b2e8d580d259e36df151`; evidence doc added at `7b71f62204a293cb5c978b6524aec3d64d95ea97`. Fresh run `45385945866` QUEUED.
- **PR #463:** run `45385180828` FAIL (Ruff F401 only; pytest was skipped). Fix commit `78f1d782d2415ba8ded06401a6607ae6e56b5630`. Fresh run `45385683618` QUEUED.
- **PR #464:** run `45385289828` IN PROGRESS.
- **PR #465:** run `45385417961` IN PROGRESS.
- **PR #466:** run `45385598574` IN PROGRESS.
- No local pytest/Ruff run or physical-PC verification was performed in this invocation. No new PASS is claimed for PRs #462–#466.

### Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1 and Launcher evidence remain frozen as previously reviewed.
- Frozen ToolCall/PermissionGate, Memory v1, Observation Envelope v1, Personal Context privacy and existing V1/V2 contracts were not changed.
- UI/frontend development remains paused. PR #9 and existing Local UI/Launcher branches were not modified.
- PR #5 remains under its V3 gate; protected/frozen V2 evaluation was not opened. PR #8 remains Draft/unmerged. No main merge was attempted.

### Blockers and authorization boundaries

- All work remained within existing repository/GitHub workflows; no paid API, subscription, purchase, external GPU, Candidate weight generation, or paid compute was started.
- No credentials, new account connections, live personal data, real capture, hardware action, notification, external dispatch, destructive operation or irreversible change was performed.
- Synthetic SQLite hard-exit tests demonstrate process-exit recovery after a successful native COMMIT only. They do not prove fsync/power-loss durability, trusted time, authenticated consent, independent custody, cross-store atomicity or exactly-once external effects.
- CI is pending on the new child heads. The two initial failures above are recorded honestly and have narrow test-only fixes queued for fresh exact-head validation.
- No user confirmation is currently required; no protected gate or paid boundary was approached.

### Next plan / 今後の方針

1. **Close the current CI loop:** inspect the queued/running exact-head results for PRs #462–#466 once; fix only concrete failures, then immediately return to an independent lane while reruns execute.
2. **Integrate only validated foundations:** after exact-head GREEN and dependency review, consider the isolated test/evidence packages for the Draft #8 research branch. Keep all child PRs Draft until their evidence is complete; do not merge to `main`.
3. **Memory durability:** continue CAS/concurrency, coherent snapshot, event-frontier and expiry/purge recovery tests; preserve schema v1 and avoid claims beyond tested SQLite boundaries.
4. **Planner and authorization:** advance journal genesis/terminal commit-outcome recovery, audit-before-action and occurrence/replay protection; keep disconnected mock execution non-authorizing.
5. **Privacy and proactive/observation:** extend Personal Context revocation/replay lifecycle and proactive CAS/privacy tests; harden observation fixture budgets without connecting real capture.
6. **V3 free-only guards:** continue isolated approval/path/identity/reproducibility review without opening protected evaluation or promoting a Candidate.
7. **UI remains paused:** no frontend work unless explicitly resumed.

## LATEST

- **Saved at:** 2026-11-26 11:55:10 JST (Asia/Tokyo).
- **Branch / PR:** `research/jarvis-foundations` / Draft PR #8; isolated research branch, not `main`.
- **Exact work-basis HEAD:** `37d8d69cd187b70e8a21f5c455bb4d11f4e3c076` (latest PR #8 branch HEAD re-read immediately before this checkpoint update).
- **Checkpoint-result HEAD:** the GitHub commit returned by this one `docs/PROJECT_STATUS.md` update; exact SHA is reported in the invocation summary. This file intentionally does not self-reference its own commit.
- **Overall ARK state:** V1 Local Core, V2 real-model baseline, Local UI v1, and Launcher/Gate Runner retain frozen evidence. Memory, Planner, ToolRegistry, PermissionGate, ActionAudit, Personal Context, proactive state, Observation, disconnected/mock execution, startup readiness, and free-only V3 guards remain isolated local-first foundations. **ARK/JARVIS overall remains NOT_PASSED.**
- **PR #8 source work-basis CI:** run [45739410448](https://github.com/Iam-2squared/ark-ai/actions/runs/45739410448) on the immediately preceding source/evidence basis HEAD `2e19c1f3edd4e7e404243f5e0d28f18e70665240` is **GREEN 6/6**. Current PR #8 HEAD is this later documentation checkpoint; no CI result is claimed for the checkpoint commit itself.
- **Main / UI boundary:** PR #5 remains gated Draft/unmerged. PR #8 remains Draft/unmerged. PR #9 remains untouched and Draft/unmerged. All new UI/frontend development remains paused. No main write or merge occurred.

## NEW work this invocation

1. **V3 pre-runtime wall-time budget origin — Draft PR #641.**
   - Branch `research/run1453-v3-pre-runtime-wall-budget-origin-20261126`; current exact child HEAD `d0ace5e6bc72abb8a2527e8fe611b474e725c979`; targets only gated Draft PR #5, whose exact parent source HEAD is `ea373c3496d06e2789cee5bb58836054ef35ed28`.
   - Both V3 CLI paths now create one `WallTimeBudget` before common evidence/runtime identity work (the preflight path preserves its earlier fail-fast report-destination admission). The same exact budget instance is checked around runtime identity work and passed into the preflight backend or full runner, preventing the backend/runner from silently restarting the timeout after `_verify_actual_runtime()`. Direct backend/runner callers retain the existing injectable local-budget fallback when no budget is supplied.
   - Adds synthetic monotonic-clock coverage for both paths: 30 seconds in fake runtime identity plus 31 seconds in fake local identity exceeds a 60-second budget before model/tokenizer loading.
   - Initial CI run [45744896062](https://github.com/Iam-2squared/ark-ai/actions/runs/45744896062) failed on two compatibility regressions: preflight report-path fail-fast ordering and the existing injectable direct-runner budget alias. Both were fixed without changing authorization or frozen semantics.
   - Fresh exact-head CI run [45745225918](https://github.com/Iam-2squared/ark-ai/actions/runs/45745225918) on `d0ace5e6bc72abb8a2527e8fe611b474e725c979` is **GREEN 6/6** (Windows/Linux × Python 3.11–3.13). PR #641 remains Draft and isolated; CI GREEN is not a V3 PASS or runtime authorization.
2. **Previously launched JARVIS persistence hard-exit packages rechecked.**
   - PR #638 Planner RUNNING + ActionAudit native-COMMIT hard exits: exact child HEAD `4f57e4c282cd739d7bf2453177e1430f7e4c12d4`; run [45738614764](https://github.com/Iam-2squared/ark-ai/actions/runs/45738614764) is **GREEN 6/6**.
   - PR #639 atomic pre-action intent/audit native-COMMIT hard exit: exact child HEAD `ec46e63d3997366d5869d894a1e59b726ff46c35`; run [45738913572](https://github.com/Iam-2squared/ark-ai/actions/runs/45738913572) is **GREEN 6/6**.
   - PR #640 Personal Context revocation native-COMMIT hard exit: exact child HEAD `30c21f6382e92d6cb936434d6f1381e663c96785`; run [45739164978](https://github.com/Iam-2squared/ark-ai/actions/runs/45739164978) is **GREEN 6/6**.
   - A read-only review of ToolRegistry, PermissionGate and disconnected mock execution found existing exact-type, registry-binding, one-shot, occurrence and crash-boundary coverage; no duplicate test or source change was added in those paths.

## Tests, CI and evidence

- PR #8 source/evidence basis HEAD `2e19c1f3edd4e7e404243f5e0d28f18e70665240`: run 45739410448 **GREEN 6/6**; later checkpoint commit is documentation-only and has no claimed CI result.
- PR #636 exact child HEAD `9f4af6e41ece8c54cf651636435525a7f45e08dc`: run 45733987136 **GREEN 6/6**.
- PR #637 exact child HEAD `669055a3502ccbbc832bc41be2cb75a88642c652`: run 45734462849 **GREEN 6/6**; read-only V3 source reconciliation only, not a V3 PASS.
- PR #638 exact child HEAD `4f57e4c282cd739d7bf2453177e1430f7e4c12d4`: run 45738614764 **GREEN 6/6**.
- PR #639 exact child HEAD `ec46e63d3997366d5869d894a1e59b726ff46c35`: run 45738913572 **GREEN 6/6**.
- PR #640 exact child HEAD `30c21f6382e92d6cb936434d6f1381e663c96785`: run 45739164978 **GREEN 6/6**.
- PR #641 exact child HEAD `d0ace5e6bc72abb8a2527e8fe611b474e725c979`: run 45745225918 **GREEN 6/6**; supersedes the failed initial head/run 45744896062.
- PR #5 exact source HEAD `ea373c3496d06e2789cee5bb58836054ef35ed28`: run [45668716864](https://github.com/Iam-2squared/ark-ai/actions/runs/45668716864) remains **FAIL** at Ruff I001 in three merge-ref test paths supplied by its base branch and absent from PR #5's own head. This ownership/import-order blocker is not bypassed by PR #641.
- No local pytest/Ruff execution, physical-PC verification, live personal-data access, real-model runtime, GPU query, V3 preflight/training, protected evaluation, live observation capture, or production dispatch is claimed.

## Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1, and Launcher/Gate Runner evidence remain frozen.
- Memory v1 DDL/schema/retention, PlannerJournal v1 DDL/event/hash/CAS, ActionAudit v1 DDL/event fields, ToolCall/PermissionGate public contracts, Observation Envelope v1, Personal Context privacy/consent boundaries, startup readiness contracts, and V3 Contract 1 remain unchanged.
- PR #5 remains gated Draft/unmerged; PR #8 remains Draft/unmerged; PR #9 remains untouched. PRs #636–#640 remain isolated Draft children targeting PR #8; PR #641 remains an isolated Draft child targeting PR #5. None is integrated. No main write or merge occurred.
- No UI/frontend feature, polish, test, or integration work occurred.

## Blockers and authorization boundaries

- **PR #5 / main ownership boundary:** the PR #5 merge-ref Ruff failure remains tied to three test paths absent from its head. Do not alter `main`, disable Ruff/tests, copy isolated foundation modules into V3, or open the protected gate.
- **Draft integration gates:** PRs #636–#640 are exact-head GREEN but remain Draft and isolated pending the normal review/readiness gate. PR #641 is exact-head GREEN but remains Draft and isolated. PR #8 remains Draft/unmerged. No ready-for-review transition or merge bypass is attempted.
- **Free-only:** no paid/external GPU, paid API/service, subscription, purchase, or potentially billable action was started.
- No real Candidate adapter/weight generation, V3 preflight/training, protected V2 final-evaluation opening, Candidate promotion, new credentials/secrets/account connection, unavailable physical-PC action, destructive operation, or irreversible data change occurred.
- Synthetic process/SQLite tests do not prove fsync/power-loss durability, trusted time, authenticated consent, independent custody, cross-store atomicity, physical erasure, or exactly-once external effects. A recovered Planner RUNNING step remains ambiguous and is never automatically replayed; ActionAudit and pre-action rows are local evidence only; a Personal Context revocation marker is a local veto, not proof of consent or erasure.
- The new wall-time guard is cooperative, not asynchronous preemption: a blocking runtime-identity probe cannot be interrupted mid-call, but elapsed time is included and the next boundary fails closed.
- No frozen-contract change or human-review decision is inferred from CI.

## Next plan / 今後の方針

1. Keep PR #641 Draft/unmerged and PR #5 gated. Do not run preflight/training, import a live GPU runtime, query hardware, generate weights, or open protected V2 evaluation.
2. Preserve the PR #5 merge-ref Ruff/ownership blocker; do not change `main`, remove tests, or copy foundation modules into V3 to bypass it.
3. Continue free-only V3 local model/tokenizer hash-to-loader binding work with explicit TOCTOU limits; do not claim atomic handle custody until implemented and independently validated.
4. Keep PRs #636–#640 Draft and isolated until exact-head CI and the normal review/readiness gate permit integration; do not merge to `main`.
5. Continue Memory WAL/SHM lifecycle, delete/recreate ABA, expiry/CAS, coherent snapshots, and manual-only COMMIT-UNKNOWN recovery without changing schema v1.
6. Continue PlannerJournal retained-prefix/recovery, terminal propagation, and ambiguous RUNNING quarantine; never auto-replay.
7. Continue restart-safe one-shot authorization, occurrence/replay protection, trusted-clock audit-before-action, and disconnected/mock execution without connecting real backends.
8. Continue privacy-safe Personal Context, proactive restart state, Observation fixture lifecycle, ToolRegistry/PermissionGate identity, and startup readiness.
9. Keep all UI/frontend work paused; PR #9 and Local UI freezes remain untouched.

---

## Historical checkpoint — 2026-11-26 11:49:43 JST

- **Saved at:** 2026-11-26 11:49:43 JST (Asia/Tokyo).
- **Branch / PR:** `research/jarvis-foundations` / Draft PR #8; isolated research branch, not `main`.
- **Exact work-basis HEAD:** `2e19c1f3edd4e7e404243f5e0d28f18e70665240` (latest PR #8 branch HEAD re-read immediately before this checkpoint update).
- **Checkpoint-result HEAD:** the GitHub commit returned by this one `docs/PROJECT_STATUS.md` update; exact SHA is reported in the invocation summary. This file intentionally does not self-reference its own commit.
- **Overall ARK state:** V1 Local Core, V2 real-model baseline, Local UI v1, and Launcher/Gate Runner retain frozen evidence. Memory, Planner, ToolRegistry, PermissionGate, ActionAudit, Personal Context, proactive state, Observation, disconnected/mock execution, startup readiness, and free-only V3 guards remain isolated local-first foundations. **ARK/JARVIS overall remains NOT_PASSED.**
- **PR #8 exact-head CI:** run [45739410448](https://github.com/Iam-2squared/ark-ai/actions/runs/45739410448) on work-basis HEAD `2e19c1f3edd4e7e404243f5e0d28f18e70665240` is **GREEN 6/6**.
- **Main / UI boundary:** PR #5 remains gated Draft/unmerged. PR #8 remains Draft/unmerged. PR #9 remains untouched and Draft/unmerged. All new UI/frontend development remains paused. No main write or merge occurred.

## NEW work this invocation

1. **V3 pre-runtime wall-time budget origin — Draft PR #641.**
   - Branch `research/run1453-v3-pre-runtime-wall-budget-origin-20261126`; exact child HEAD `17d824aba930e9953437970fa3ab14a3fee70d81`; targets only gated Draft PR #5, whose exact parent source HEAD is `ea373c3496d06e2789cee5bb58836054ef35ed28`.
   - Both V3 CLI paths now create one `WallTimeBudget` immediately after scope-specific authorization validation, check it around local evidence/runtime identity work, and pass that same exact instance into the preflight backend or full-runner. Runtime work no longer silently restarts the timeout after `_verify_actual_runtime()`. Direct backend/runner callers retain their previous local-budget fallback when no budget is supplied.
   - Adds a synthetic monotonic-clock test for both paths: 30 seconds in fake runtime identity plus 31 seconds in fake local identity exceeds a 60-second budget before model/tokenizer loading. No torch import, GPU query, model load, preflight, training, or Candidate path is reached.
   - Exact-head CI run [45744896062](https://github.com/Iam-2squared/ark-ai/actions/runs/45744896062) is **IN PROGRESS**. No PASS is claimed; PR #641 remains Draft and isolated from main.
2. **Previously launched JARVIS persistence hard-exit packages rechecked.**
   - PR #638 Planner RUNNING + ActionAudit native-COMMIT hard exits: exact child HEAD `4f57e4c282cd739d7bf2453177e1430f7e4c12d4`; run [45738614764](https://github.com/Iam-2squared/ark-ai/actions/runs/45738614764) is now **GREEN 6/6**.
   - PR #639 atomic pre-action intent/audit native-COMMIT hard exit: exact child HEAD `ec46e63d3997366d5869d894a1e59b726ff46c35`; run [45738913572](https://github.com/Iam-2squared/ark-ai/actions/runs/45738913572) is now **GREEN 6/6**.
   - PR #640 Personal Context revocation native-COMMIT hard exit: exact child HEAD `30c21f6382e92d6cb936434d6f1381e663c96785`; run [45739164978](https://github.com/Iam-2squared/ark-ai/actions/runs/45739164978) is now **GREEN 6/6**.
   - These are isolated synthetic regression packages; none is integrated or promoted.

## Tests, CI and evidence

- PR #8 exact work-basis HEAD `2e19c1f3edd4e7e404243f5e0d28f18e70665240`: run 45739410448 **GREEN 6/6**.
- PR #636 exact child HEAD `9f4af6e41ece8c54cf651636435525a7f45e08dc`: run 45733987136 **GREEN 6/6**.
- PR #637 exact child HEAD `669055a3502ccbbc832bc41be2cb75a88642c652`: run 45734462849 **GREEN 6/6**; read-only V3 source reconciliation only, not a V3 PASS.
- PR #638 exact child HEAD `4f57e4c282cd739d7bf2453177e1430f7e4c12d4`: run 45738614764 **GREEN 6/6**.
- PR #639 exact child HEAD `ec46e63d3997366d5869d894a1e59b726ff46c35`: run 45738913572 **GREEN 6/6**.
- PR #640 exact child HEAD `30c21f6382e92d6cb936434d6f1381e663c96785`: run 45739164978 **GREEN 6/6**.
- PR #641 exact child HEAD `17d824aba930e9953437970fa3ab14a3fee70d81`: run 45744896062 **IN PROGRESS** at checkpoint time.
- PR #5 exact source HEAD `ea373c3496d06e2789cee5bb58836054ef35ed28`: run [45668716864](https://github.com/Iam-2squared/ark-ai/actions/runs/45668716864) remains **FAIL** at Ruff I001 in three merge-ref test paths supplied by its base branch and absent from PR #5's own head. This ownership/import-order blocker is not bypassed by PR #641.
- No local pytest/Ruff execution, physical-PC verification, live personal-data access, real-model runtime, GPU query, V3 preflight/training, protected evaluation, live observation capture, or production dispatch is claimed.

## Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1, and Launcher/Gate Runner evidence remain frozen.
- Memory v1 DDL/schema/retention, PlannerJournal v1 DDL/event/hash/CAS, ActionAudit v1 DDL/event fields, ToolCall/PermissionGate public contracts, Observation Envelope v1, Personal Context privacy/consent boundaries, startup readiness contracts, and V3 Contract 1 remain unchanged.
- PR #5 remains gated Draft/unmerged; PR #8 remains Draft/unmerged; PR #9 remains untouched. PRs #636–#640 remain isolated Draft children targeting PR #8; PR #641 is a new isolated Draft child targeting PR #5. None is integrated. No main write or merge occurred.
- No UI/frontend feature, polish, test, or integration work occurred.

## Blockers and authorization boundaries

- **PR #5 / main ownership boundary:** the PR #5 merge-ref Ruff failure remains tied to three test paths absent from its head. Do not alter `main`, disable Ruff/tests, copy isolated foundation modules into V3, or open the protected gate.
- **Draft integration gates:** PRs #636–#640 are exact-head GREEN but remain Draft and isolated pending the normal review/readiness gate. PR #641 is Draft with exact-head CI in progress. PR #8 remains Draft/unmerged. No ready-for-review transition or merge bypass is attempted.
- **Free-only:** no paid/external GPU, paid API/service, subscription, purchase, or potentially billable action was started.
- No real Candidate adapter/weight generation, V3 preflight/training, protected V2 final-evaluation opening, Candidate promotion, new credentials/secrets/account connection, unavailable physical-PC action, destructive operation, or irreversible data change occurred.
- Synthetic process/SQLite tests do not prove fsync/power-loss durability, trusted time, authenticated consent, independent custody, cross-store atomicity, physical erasure, or exactly-once external effects. A recovered Planner RUNNING step remains ambiguous and is never automatically replayed; ActionAudit and pre-action rows are local evidence only; a Personal Context revocation marker is a local veto, not proof of consent or erasure.
- The new wall-time guard is cooperative, not asynchronous preemption: a blocking runtime-identity probe cannot be interrupted mid-call, but elapsed time is included and the next boundary fails closed.
- No frozen-contract change or human-review decision is inferred from CI.

## Next plan / 今後の方針

1. Revisit exact-head CI for PR #641 when useful; if a concrete failure appears, make the smallest semantics-preserving correction and do not launch duplicate equivalent workflows.
2. Keep PR #641 Draft/unmerged and PR #5 gated. Do not run preflight/training, import a live GPU runtime, query hardware, generate weights, or open protected V2 evaluation.
3. Keep PRs #636–#640 Draft and isolated until exact-head CI and the normal review/readiness gate permit integration; do not merge to `main`.
4. Continue Memory WAL/SHM lifecycle, delete/recreate ABA, expiry/CAS, coherent snapshots, and manual-only COMMIT-UNKNOWN recovery without changing schema v1.
5. Continue PlannerJournal retained-prefix/recovery, terminal propagation, and ambiguous RUNNING quarantine; never auto-replay.
6. Continue restart-safe one-shot authorization, occurrence/replay protection, trusted-clock audit-before-action, and disconnected/mock execution without connecting real backends.
7. Continue privacy-safe Personal Context, proactive restart state, Observation fixture lifecycle, ToolRegistry/PermissionGate identity, and startup readiness.
8. Continue free-only V3 approval/path/identity/reproducibility guards. Preserve the PR #5 merge-ref lint/ownership blocker; no preflight, training, torch/CUDA, GPU query, protected evaluation, or Candidate promotion.
9. Keep all UI/frontend work paused; PR #9 and Local UI freezes remain untouched.


---

## Historical checkpoint — 2026-11-26 10:59:31 JST

- **Saved at:** 2026-11-26 10:59:31 JST (Asia/Tokyo).
- **Branch / PR:** `research/jarvis-foundations` / Draft PR #8; isolated research branch, not `main`.
- **Exact work-basis HEAD:** `1cf7b725fcf3c32ff5ffd59bda04ef03d140324b` (PR #8 branch re-read immediately before this single checkpoint update).
- **Checkpoint-result HEAD:** the GitHub commit returned by this one `docs/PROJECT_STATUS.md` update; exact returned SHA is reported in the invocation summary. This file intentionally does not self-reference its own commit.
- **Overall ARK state:** V1 Local Core, V2 real-model baseline, Local UI v1, and Launcher/Gate Runner retain frozen evidence. Memory, Planner, ToolRegistry, PermissionGate, ActionAudit, Personal Context, proactive state, Observation, disconnected/mock execution, startup readiness, and free-only V3 guards remain isolated local-first foundations. **ARK/JARVIS overall remains NOT_PASSED.**
- **PR #8 exact-head CI:** run [45734650593](https://github.com/Iam-2squared/ark-ai/actions/runs/45734650593) on work-basis HEAD `1cf7b725fcf3c32ff5ffd59bda04ef03d140324b` is **GREEN 6/6**.
- **Main / UI boundary:** PR #5 remains gated Draft/unmerged. PR #8 remains Draft/unmerged. PR #9 remains untouched and Draft/unmerged. All new UI/frontend development remains paused. No main write or merge occurred.

## NEW work this invocation

1. **Production PlannerJournal RUNNING + ActionAudit native-COMMIT hard exits — Draft PR #638.**
   - Branch `research/run1450-planner-audit-native-commit-hard-exit-20261126`; exact child HEAD `4f57e4c282cd739d7bf2453177e1430f7e4c12d4`; targets only PR #8.
   - Adds test-only spawned-process exits immediately after native SQLite COMMIT returns, before connection cleanup or receipt return. Planner cold recovery must retain one PENDING → RUNNING event, mark the step ambiguous, keep dependent/independent steps PENDING, deny dispatch/replay, and reject stale genesis CAS. ActionAudit cold readback must retain exactly two ordered rows, preserve schema v1/quick_check, and not persist raw ToolCall arguments.
   - No production source, schema, or public API changed. Exact-head CI run [45738614764](https://github.com/Iam-2squared/ark-ai/actions/runs/45738614764) is **IN PROGRESS** (2/6 jobs completed GREEN; 4/6 in progress at checkpoint time).

2. **Atomic pre-action intent/audit native-COMMIT hard exit — Draft PR #639.**
   - Branch `research/run1451-atomic-preaction-native-commit-hard-exit-20261126`; exact child HEAD `ec46e63d3997366d5869d894a1e59b726ff46c35`; targets only PR #8.
   - Adds a test-only spawned-process exit immediately after `DisconnectedAtomicPreactionLedger.reserve()` commits the paired intent/audit rows, before close or retained witness return. Cold recovery checks one exact pair, schema v1/quick_check, stale-genesis rejection, duplicate-occurrence rejection, and false-only dispatch/replay/external-effect/trusted-approval/independent-custody flags.
   - No production source, schema, or public API changed. Exact-head CI run [45738913572](https://github.com/Iam-2squared/ark-ai/actions/runs/45738913572) is **IN PROGRESS** (6/6 jobs in progress at checkpoint time).

3. **Personal Context revocation native-COMMIT hard exit — Draft PR #640.**
   - Branch `research/run1452-personal-context-revocation-native-commit-hard-exit-20261126`; exact child HEAD `30c21f6382e92d6cb936434d6f1381e663c96785`; targets only PR #8.
   - Adds a test-only spawned-process exit immediately after `SyntheticContextRevocationLedger.revoke()` commits, before source recheck or receipt return. Cold reconstruction must retain the scope-digest/time veto, validate schema v1/quick_check and retained-prefix extension, and deny direct and higher-level context projection. The veto database/sidecars must not contain synthetic owner, namespace, or Memory content.
   - No production source, schema, or public API changed. Exact-head CI run [45739164978](https://github.com/Iam-2squared/ark-ai/actions/runs/45739164978) is **IN PROGRESS** (6/6 jobs in progress at checkpoint time).

4. **Previously launched child evidence rechecked.**
   - PR #636 Memory delete native-COMMIT hard-exit: exact child HEAD `9f4af6e41ece8c54cf651636435525a7f45e08dc`; run [45733987136](https://github.com/Iam-2squared/ark-ai/actions/runs/45733987136) **GREEN 6/6**.
   - PR #637 V3 free-guard source reconciliation: exact child HEAD `669055a3502ccbbc832bc41be2cb75a88642c652`; run [45734462849](https://github.com/Iam-2squared/ark-ai/actions/runs/45734462849) **GREEN 6/6**. This is a read-only documentation reconciliation, not a V3 PASS.

## Tests, CI and evidence

- PR #8 work-basis HEAD `1cf7b725fcf3c32ff5ffd59bda04ef03d140324b`: run 45734650593 **GREEN 6/6**.
- PR #636 exact child HEAD `9f4af6e41ece8c54cf651636435525a7f45e08dc`: run 45733987136 **GREEN 6/6**.
- PR #637 exact child HEAD `669055a3502ccbbc832bc41be2cb75a88642c652`: run 45734462849 **GREEN 6/6**.
- PR #638 exact child HEAD `4f57e4c282cd739d7bf2453177e1430f7e4c12d4`: run 45738614764 **IN PROGRESS** (2/6 completed GREEN; 4 in progress).
- PR #639 exact child HEAD `ec46e63d3997366d5869d894a1e59b726ff46c35`: run 45738913572 **IN PROGRESS** (6/6 in progress).
- PR #640 exact child HEAD `30c21f6382e92d6cb936434d6f1381e663c96785`: run 45739164978 **IN PROGRESS** (6/6 in progress).
- PR #5 exact source HEAD `ea373c3496d06e2789cee5bb58836054ef35ed28`: run [45668716864](https://github.com/Iam-2squared/ark-ai/actions/runs/45668716864) remains **FAIL** at Ruff I001 in three merge-ref test paths absent from PR #5's own head branch and supplied by its base merge ref.
- No local pytest/Ruff execution, physical-PC verification, live personal-data access, real-model runtime, GPU query, V3 preflight/training, protected evaluation, live observation capture, or production dispatch is claimed.

## Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1, and Launcher/Gate Runner evidence remain frozen.
- Memory v1 DDL/schema/retention, PlannerJournal v1 DDL/event/hash/CAS, ActionAudit v1 DDL/event fields, ToolCall/PermissionGate public contracts, Observation Envelope v1, Personal Context privacy/consent boundaries, startup readiness contracts, and V3 Contract 1 remain unchanged.
- PR #5 remains gated Draft/unmerged; PR #8 remains Draft/unmerged; PR #9 remains untouched. PRs #636–#640 remain isolated Draft children targeting PR #8; none is integrated. No main write or merge occurred.
- No UI/frontend feature, polish, test, or integration work occurred.

## Blockers and authorization boundaries

- **PR #5 / main ownership boundary:** the PR #5 merge-ref Ruff failure remains tied to three test paths absent from its head. PR #276's pytest collection failure confirms the related missing JARVIS module on `main`. Do not alter `main`, disable Ruff/tests, copy isolated foundation modules into V3, or open the protected gate.
- **Draft integration gate:** PRs #636 and #637 are exact-head GREEN but remain Draft and isolated pending the normal review/readiness gate. PRs #638–#640 remain Draft and isolated with CI in progress. No ready-for-review transition or merge bypass is attempted. PR #8 remains Draft/unmerged.
- **Free-only:** no paid/external GPU, paid API/service, subscription, purchase, or potentially billable action was started.
- No real Candidate adapter/weight generation, V3 preflight/training, protected V2 final-evaluation opening, Candidate promotion, new credentials/secrets/account connection, unavailable physical-PC action, destructive operation, or irreversible data change occurred.
- Synthetic process/SQLite tests do not prove fsync/power-loss durability, trusted time, authenticated consent, independent custody, cross-store atomicity, physical erasure, or exactly-once external effects. A recovered Planner RUNNING step remains ambiguous and is never automatically replayed; ActionAudit and pre-action rows are local evidence only; a Personal Context revocation marker is a local veto, not proof of consent or erasure.
- No frozen-contract change or human-review decision is inferred from CI.

## Next plan / 今後の方針

1. Revisit exact-head CI for PRs #638–#640 when useful; do not poll repeatedly or duplicate workflows. If a concrete failure appears, make the smallest semantics-preserving correction, launch fresh exact-head CI, then switch to a non-conflicting lane.
2. Keep PRs #636–#640 Draft and isolated until exact-head CI and the normal review/readiness gate permit integration. Do not merge to `main`.
3. Continue Memory WAL/SHM lifecycle, delete/recreate ABA, expiry/CAS, coherent snapshots, and manual-only COMMIT-UNKNOWN recovery without changing schema v1.
4. Continue PlannerJournal retained-prefix/recovery, terminal propagation, and ambiguous RUNNING quarantine; never auto-replay.
5. Continue restart-safe one-shot authorization, occurrence/replay protection, trusted-clock audit-before-action, and disconnected/mock execution without connecting real backends.
6. Continue privacy-safe Personal Context, proactive restart state, Observation fixture lifecycle, ToolRegistry/PermissionGate identity, and startup readiness.
7. Continue free-only V3 approval/path/identity/reproducibility guards. Preserve the PR #5 merge-ref ownership blocker; no preflight, training, torch/CUDA, GPU query, protected evaluation, or Candidate promotion.
8. Keep all UI/frontend work paused; PR #9 and Local UI freezes remain untouched.



---

## LATEST

- **Saved at:** 2026-11-26 10:02:57 JST (Asia/Tokyo).
- **Branch / PR:** `research/jarvis-foundations` / Draft PR #8; isolated research branch, not `main`.
- **Exact work-basis HEAD:** `d3f69747b27b8197bf01342701d1808a34e8786b` (PR #8 head re-read immediately before this checkpoint; includes the Run1443 gap-matrix reconciliation and the 08:55:53 JST checkpoint).
- **Checkpoint-result HEAD:** the GitHub commit returned by this `docs/PROJECT_STATUS.md` update; its exact SHA is reported in the invocation summary. This file intentionally does not self-reference its own commit.
- **Overall ARK state:** V1 Local Core, V2 real-model baseline, Local UI v1, and Launcher/Gate Runner retain frozen evidence. Memory, Planner, ToolRegistry, PermissionGate, ActionAudit, Personal Context, proactive state, Observation, disconnected/mock execution, and free-only V3 guard work remain isolated local-first foundations. **ARK/JARVIS overall remains NOT_PASSED.**
- **PR #8 exact-head CI:** run [45725095260](https://github.com/Iam-2squared/ark-ai/actions/runs/45725095260) (run 7805) on `d3f69747b27b8197bf01342701d1808a34e8786b` is **GREEN 6/6**.
- **Main / UI boundary:** PR #5 remains gated Draft/unmerged. PR #8 remains Draft/unmerged. PR #9 remains untouched and Draft/unmerged. All new UI/frontend development remains paused. No main write or merge occurred.

## NEW work this invocation

1. **Personal Context replay import-group correction — Draft PR #630.**
   - Branch `research/run1442-context-replay-two-process-cas-20261126`; exact child HEAD `77df496e06a91e1b470c64591c2533ed46914802`; targets only PR #8.
   - The earlier exact-head CI runs [45724103264](https://github.com/Iam-2squared/ark-ai/actions/runs/45724103264) and [45724637568](https://github.com/Iam-2squared/ark-ai/actions/runs/45724637568) failed Ruff I001. Re-read the actual current test file and corrected the missing import-group separator using the normal GitHub file-update path; no source, schema, privacy contract, or test semantics changed.
   - Fresh exact-head run [45730740088](https://github.com/Iam-2squared/ark-ai/actions/runs/45730740088) (run 7806) is **IN PROGRESS**: 4/6 jobs completed GREEN; 2 Windows jobs remain in progress. Completed Ubuntu 3.13 log confirms `ruff check .` passed and pytest ran; the workflow has not yet completed 6/6.

2. **PlannerJournal cross-process transition CAS — Draft PR #632.**
   - Branch `research/run1444-planner-journal-process-cas-20261126`; exact child HEAD `494d7d5e21e5dbf929bef38d32c1a4df316ec543`; targets only PR #8.
   - Adds a spawned-process race where two independent journal handles recover the same genesis frontier and attempt the same RUNNING transition with revision 0 / sequence 0. The expected result is one committed transition and one domain CAS conflict; cold recovery preserves one ambiguous RUNNING step, an unrelated PENDING step, one event/meta frontier, and no dispatch or automatic replay authority. Synthetic ToolCall plaintext must not be persisted.
   - Exact-head run [45731310220](https://github.com/Iam-2squared/ark-ai/actions/runs/45731310220) (run 7807) is **IN PROGRESS**: 3/6 Ubuntu jobs completed GREEN; 3 Windows jobs remain in progress.

3. **PermissionGate exact-type and registry-bound custody — Draft PR #633.**
   - Branch `research/run1445-permission-gate-exact-type-custody-20261126`; exact child HEAD `ddd6c02694814058da4ee9a453b44cfeaeecbd62`; targets only PR #8.
   - Test-only current-head coverage for lookup-hook substitution/absence, hook-inventory and sentinel identity, hostile subclasses, reflective token/lock replacement before grant iteration, and registry-derived WRITE effect with a one-shot token. The inert backend is never invoked; no durable authorization is claimed.
   - Exact-head run [45732256741](https://github.com/Iam-2squared/ark-ai/actions/runs/45732256741) (run 7808) is **IN PROGRESS**: 1/6 jobs completed GREEN; 5 jobs remain in progress.

4. **Disconnected mock executor cross-process occurrence race — Draft PR #634.**
   - Branch `research/run1446-disconnected-executor-cross-process-race-20261126`; exact child HEAD `a33222450893c2a7853602160bb15abd2e7cbe0a`; targets only PR #8.
   - Adds two spawned executor stacks with separate registries, gates, backends, ActionAudit handles, and occurrence-store handles contending for one synthetic WRITE request/token/occurrence. Expected: one durable reservation, one process-local token consumption, one mock call, and one pre-action/completion audit pair; loser is denied before token spend/audit/dispatch. Stores are initialized before the race, so this is not first-open evidence.
   - Exact-head run [45732560414](https://github.com/Iam-2squared/ark-ai/actions/runs/45732560414) (run 7809) is **IN PROGRESS**; no job failure has been reported at checkpoint time.

5. **Proactive state native-COMMIT hard-exit recovery — Draft PR #635.**
   - Branch `research/run1447-proactive-state-commit-hard-exit-20261126`; exact child HEAD `a13fe5be6531815ab7bc7a17bddc632546a16409`; targets only PR #8.
   - Adds a spawned-process exit immediately after SQLite `Connection.commit()` returns from synthetic proactive `evaluate`, before the state receipt returns. Cold recovery must find one revision-1 ELIGIBLE_PREVIEW row, retain all notification/dispatch/trusted-clock/consent/replay denials, and reject a blind stale genesis retry. No timer or notification is introduced.
   - Exact-head run [45732963533](https://github.com/Iam-2squared/ark-ai/actions/runs/45732963533) (run 7810) is **IN PROGRESS / partially QUEUED**; no job failure has been reported at checkpoint time.

6. **Previously launched child evidence rechecked.**
   - PR #627 disconnected executor two-handle race: run [45716635322](https://github.com/Iam-2squared/ark-ai/actions/runs/45716635322) **GREEN 6/6**.
   - PR #628 PlannerJournal diamond RUNNING-barrier recovery: run [45716909855](https://github.com/Iam-2squared/ark-ai/actions/runs/45716909855) **GREEN 6/6**.
   - PR #629 proactive state process-level first-open/CAS: run [45723833690](https://github.com/Iam-2squared/ark-ai/actions/runs/45723833690) **GREEN 6/6**.
   - PR #631 ActionAudit process-level first-open/append: run [45724216924](https://github.com/Iam-2squared/ark-ai/actions/runs/45724216924) **GREEN 6/6**.
   - PR #623 local HF snapshot staging: run [45708896479](https://github.com/Iam-2squared/ark-ai/actions/runs/45708896479) **GREEN 6/6**; PR #624 V3 gap reconciliation: run [45708528169](https://github.com/Iam-2squared/ark-ai/actions/runs/45708528169) **GREEN 6/6**; PR #625 attempt/finalization ledger: run [45716697765](https://github.com/Iam-2squared/ark-ai/actions/runs/45716697765) **GREEN 6/6**; PR #626 atomic run manifest: run [45716706277](https://github.com/Iam-2squared/ark-ai/actions/runs/45716706277) **GREEN 6/6**.

## Tests, CI and evidence

- PR #8 source/checkpoint basis `d3f69747b27b8197bf01342701d1808a34e8786b`: run 45725095260, **GREEN 6/6**.
- PR #627: 45716635322 **GREEN 6/6**; PR #628: 45716909855 **GREEN 6/6**.
- PR #629: 45723833690 **GREEN 6/6**; PR #631: 45724216924 **GREEN 6/6**.
- PR #630: 45724103264 **FAIL** Ruff I001; 45724637568 **FAIL** Ruff I001; corrected exact child HEAD `77df496e06a91e1b470c64591c2533ed46914802`, fresh run 45730740088 **IN PROGRESS** (4/6 completed GREEN).
- PR #632: 45731310220 **IN PROGRESS** (3/6 completed GREEN).
- PR #633: 45732256741 **IN PROGRESS** (1/6 completed GREEN).
- PR #634: 45732560414 **IN PROGRESS**.
- PR #635: 45732963533 **IN PROGRESS / partially QUEUED**.
- PR #5 exact source HEAD `ea373c3496d06e2789cee5bb58836054ef35ed28`: run [45668716864](https://github.com/Iam-2squared/ark-ai/actions/runs/45668716864) remains **FAIL** at Ruff I001 in three merge-ref test paths absent from PR #5's own head branch and supplied by the base merge ref.
- PR #276 exact head `5f9f801901480873653b5dcaa79dc91d402e2d85`: run [45026667524](https://github.com/Iam-2squared/ark-ai/actions/runs/45026667524) remains **FAIL** at pytest collection after Ruff passed; `ark.personal_context_offline_preview` is not present on `main`.
- No local pytest/Ruff execution, physical-PC verification, live personal-data access, real-model runtime, GPU query, V3 preflight/training, protected evaluation, live observation capture, or production dispatch is claimed.

## Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1, and Launcher/Gate Runner evidence remain frozen.
- Memory v1 DDL/schema/retention, PlannerJournal v1 DDL/event/hash/CAS, ActionAudit v1 DDL/event fields, ToolCall/PermissionGate public contracts, Observation Envelope v1, Personal Context privacy/consent boundaries, and V3 Contract 1 remain unchanged.
- PR #5 remains gated Draft/unmerged; PR #8 remains Draft/unmerged; PR #9 remains untouched. PRs #627–#635 remain isolated Draft children targeting PR #8; none has been integrated. No main write or merge occurred.
- No UI/frontend feature, polish, test, or integration work occurred.

## Blockers and authorization boundaries

- **PR #5 / main ownership boundary:** PR #5's merge-ref Ruff failures are in tests absent from PR #5's head. PR #276 demonstrates that correcting import grouping alone exposes pytest collection failure because `ark.personal_context_offline_preview` is not on `main`. Do not alter `main`, disable Ruff/tests, copy isolated foundation modules into V3, or open the protected gate.
- **Draft integration gate:** PRs #627–#635 remain Draft and target only PR #8. No ready-for-review transition or merge bypass is attempted. PR #8 remains Draft/unmerged.
- **Free-only:** no paid/external GPU, paid API/service, subscription, purchase, or potentially billable action was started.
- No real Candidate adapter/weight generation, V3 preflight/training, protected V2 final-evaluation opening, Candidate promotion, new credentials/secrets/account connection, unavailable physical-PC action, destructive operation, or irreversible data change occurred.
- Synthetic process/SQLite tests do not prove fsync/power-loss durability, trusted time, authenticated consent, independent custody, cross-store atomicity, or exactly-once external effects. Personal Context receipts remain denial-only; proactive state remains synthetic and non-notifying; ActionAudit evidence is local only.
- No frozen-contract change or human-review decision is inferred from CI.

## Next plan / 今後の方針

1. Inspect the five in-flight exact-head CI runs only when useful; fix concrete semantics-preserving failures, then switch to a non-conflicting lane while corrected CI runs. Do not duplicate equivalent workflow runs.
2. After PR #632's CAS evidence, continue production PlannerJournal crash recovery, especially native-COMMIT ambiguity for RUNNING transitions and concurrent first-open/genesis behavior, without changing DDL v1 or enabling replay.
3. Reconcile PR #630's corrected import grouping and retain the process-level replay CAS test only with fresh exact-head GREEN evidence.
4. Keep PRs #627–#635 Draft and isolated until the normal review/readiness gate permits integration. Do not promote them or merge to `main`.
5. Continue Memory row/event integrity, WAL/ABA, expiry/CAS, and coherent snapshots; do not change schema v1.
6. Continue durable one-shot authorization, occurrence/replay protection, audit-before-action, privacy-safe Personal Context, proactive state, Observation fixture lifecycle, ToolRegistry/PermissionGate identity, and startup readiness.
7. Continue free-only V3 approval/path/identity/reproducibility guards. Keep PR #5 Draft/unmerged; no protected evaluation, training, or Candidate promotion.
8. Keep all UI/frontend work paused; PR #9 and Local UI freezes remain untouched.

---
## Historical checkpoint — saved at 2026-11-26 08:55:53 JST (superseded)

- **Saved at:** 2026-11-26 08:55:53 JST (Asia/Tokyo).
- **Branch / PR:** `research/jarvis-foundations` / Draft PR #8; isolated research branch, not `main`.
- **Exact work-basis HEAD:** `a42d711e3cb00f00ea6b87cc317c33ffbb0446a5` (PR #8 head re-read immediately before this checkpoint; includes the Run1443 V3 gap-matrix reconciliation and prior status checkpoint).
- **Checkpoint-result HEAD:** the GitHub commit created by this `docs/PROJECT_STATUS.md` update; its exact returned SHA is confirmed after the write and reported in the invocation summary. This file intentionally does not self-reference its own commit.
- **Overall ARK state:** V1 Local Core, V2 real-model baseline, Local UI v1, and Launcher/Gate Runner retain frozen evidence. Memory, Planner, ToolRegistry, PermissionGate, ActionAudit, Personal Context, proactive state, Observation, disconnected/mock execution, and free-only V3 guard work remain isolated local-first foundations. **ARK/JARVIS overall remains NOT_PASSED.**
- **PR #8 exact-head CI:** run [45724727952](https://github.com/Iam-2squared/ark-ai/actions/runs/45724727952) (run 7803) on `a42d711e3cb00f00ea6b87cc317c33ffbb0446a5` is **IN PROGRESS**.
- **Main / UI boundary:** PR #5 remains gated Draft/unmerged. PR #8 remains Draft/unmerged. PR #9 remains untouched and Draft/unmerged. All new UI/frontend development remains paused. No main write or merge occurred.

## NEW work this invocation

1. **Proactive state process-level first-open and CAS races — Draft PR #629.**
   - Branch `research/run1441-proactive-state-two-handle-cas-20261126`; exact child HEAD `6ce42bc7e26ffe1a2dfa9696cac4df488d5b4b83`; targets only PR #8.
   - Adds spawned-process tests for concurrent first-open schema convergence, genesis `expected_revision=0` contention, and same-revision update contention. Intended invariant: one durable winner and one domain-level CAS conflict. No production source, schema, or policy vocabulary changed.
   - Exact-head run [45723833690](https://github.com/Iam-2squared/ark-ai/actions/runs/45723833690) (run 7797) is **IN PROGRESS**.

2. **Personal Context replay process-level CAS — Draft PR #630.**
   - Branch `research/run1442-context-replay-two-process-cas-20261126`; current exact child HEAD `da135cfa9951be1d0780ed0aa5d0ca4fdb20879d`; targets only PR #8.
   - Adds two-process races for identical request identity and disjoint requests sharing a retained genesis witness. The losing disjoint request must cold-read the new prefix before a separate reservation; receipts remain denial-only and fixture plaintext is not stored.
   - Initial run [45724103264](https://github.com/Iam-2squared/ark-ai/actions/runs/45724103264) (run 7798) failed Ruff I001. First import correction at `a817595d06365acdfde3b1c8b0c68dd884165758` was insufficient; run [45724637568](https://github.com/Iam-2squared/ark-ai/actions/runs/45724637568) (run 7802) still failed I001 because the import block retained an extra blank line after the final import. The exact blank-line correction is at `da135cfa9951be1d0780ed0aa5d0ca4fdb20879d`; fresh run [45724925359](https://github.com/Iam-2squared/ark-ai/actions/runs/45724925359) (run 7804) is **QUEUED**.

3. **Action Audit process-level first-open and append sequencing — Draft PR #631.**
   - Branch `research/run1443-action-audit-process-first-open-20261126`; exact child HEAD `ad6328cc121b558cf960e65e5805d73c57a2527c`; targets only PR #8.
   - Adds a spawned-process concurrent WAL/bootstrap regression followed by one synthetic append per process. A cold reader checks schema version 1, SQLite quick_check, dense event IDs 1–2, and absence of raw private marker values. No production source, schema, or executor integration changed.
   - Exact-head run [45724216924](https://github.com/Iam-2squared/ark-ai/actions/runs/45724216924) (run 7799) is **IN PROGRESS**.

4. **V3 gap-matrix live reconciliation — parent PR #8 commit `9af4fc3d7911cafb9a6d8ed542e7449eb19f57dc`.**
   - Records PR #5 exact source HEAD `ea373c3496d06e2789cee5bb58836054ef35ed28` and exact-head run [45668716864](https://github.com/Iam-2squared/ark-ai/actions/runs/45668716864) (run 7744), which fails all six matrix jobs at Ruff I001 in three test paths absent from PR #5's own head branch and supplied by the base merge ref.
   - Marks Run1346's strict duplicate/non-finite parser and nested symlink-grandparent gaps as superseded by the exact PR #5 source and PR #624 reconciliation (run 45708528169 GREEN 6/6). PR #623, #625, and #626 retain their previously recorded exact-head GREEN evidence.

5. **Main merge-ref ownership diagnosis — read-only.**
   - Existing Draft PR #276 branch `fix/main-ruff-personal-context-imports-run1111`, exact HEAD `5f9f801901480873653b5dcaa79dc91d402e2d85`, run [45026667524](https://github.com/Iam-2squared/ark-ai/actions/runs/45026667524) (run 7085) passes Ruff after its one-file import-group correction but fails pytest collection with `ModuleNotFoundError: ark.personal_context_offline_preview` on `main`.
   - Confirms that correcting merge-ref import ordering alone exposes a missing JARVIS foundation module on `main`. No write to PR #276 or `main`, no test deletion, and no copying of isolated foundation modules was attempted.

## Tests, CI and evidence

- PR #8 current exact head `a42d711e3cb00f00ea6b87cc317c33ffbb0446a5`: run 45724727952, **IN PROGRESS**.
- PR #627 disconnected mock executor two-handle WRITE race: run 45716635322, **GREEN 6/6**.
- PR #628 PlannerJournal diamond RUNNING-barrier recovery: run 45716909855, **GREEN 6/6**.
- PR #629 proactive state process-level first-open/CAS: run 45723833690, **IN PROGRESS**.
- PR #630 Personal Context replay process-level CAS: run 45724103264 **FAIL** Ruff I001; run 45724637568 **FAIL** Ruff I001; corrected exact child HEAD `da135cfa9951be1d0780ed0aa5d0ca4fdb20879d`, run 45724925359 **QUEUED**.
- PR #631 Action Audit process-level first-open/append: run 45724216924, **IN PROGRESS**.
- PR #5 exact source HEAD `ea373c3496d06e2789cee5bb58836054ef35ed28`: run 45668716864 **FAIL** Ruff I001 in the three merge-ref test paths recorded above.
- PR #276 exact head `5f9f801901480873653b5dcaa79dc91d402e2d85`: run 45026667524 **FAIL** at pytest collection after Ruff passed; missing `ark.personal_context_offline_preview` on `main`.
- PR #623: run 45708896479 **GREEN 6/6**; PR #624: run 45708528169 **GREEN 6/6**; PR #625: run 45716697765 **GREEN 6/6**; PR #626: run 45716706277 **GREEN 6/6**.
- No local pytest/Ruff execution, physical-PC verification, live personal-data access, real-model runtime, GPU query, V3 preflight/training, protected evaluation, live observation capture, or production dispatch is claimed.

## Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1, and Launcher/Gate Runner evidence remain frozen.
- Memory v1 DDL/schema/retention, PlannerJournal v1 DDL/event/hash/CAS, ActionAudit v1 DDL/event fields, ToolCall/PermissionGate public contracts, Observation Envelope v1, Personal Context privacy/consent boundaries, and V3 Contract 1 remain unchanged.
- PR #5 remains gated Draft/unmerged; PR #8 remains Draft/unmerged; PR #9 remains untouched. PRs #627–#631 remain isolated Draft children; none has been integrated. No main write or merge occurred.
- No UI/frontend feature, polish, test, or integration work occurred.

## Blockers and authorization boundaries

- **PR #5 / main ownership boundary:** PR #5's merge-ref Ruff failures are in tests absent from PR #5's head. PR #276 demonstrates that fixing the Personal Context import grouping alone leads to pytest collection failure because `ark.personal_context_offline_preview` is not on `main`. Do not alter `main`, disable Ruff/tests, copy isolated foundation modules into V3, or open the protected gate. The Planner/ToolRegistry import-order findings remain unmodified.
- **Draft integration gate:** PRs #627–#631 remain Draft and target only PR #8. No ready-for-review transition or merge bypass is attempted. PR #8 remains Draft/unmerged.
- **Free-only:** no paid/external GPU, paid API/service, subscription, purchase, or potentially billable action was started.
- No real Candidate adapter/weight generation, V3 preflight/training, protected V2 final-evaluation opening, Candidate promotion, new credentials/secrets/account connection, unavailable physical-PC action, destructive operation, or irreversible data change occurred.
- Synthetic process/SQLite tests do not prove fsync/power-loss durability, trusted time, authenticated consent, independent custody, cross-store atomicity, or exactly-once external effects. Personal Context receipts remain denial-only; proactive state remains synthetic and non-notifying; ActionAudit evidence is local only.
- No frozen-contract change or human-review decision is inferred from CI.

## Next plan / 今後の方針

1. Inspect exact-head CI for PRs #629–#631 and the current PR #8 checkpoint once useful results are available. Fix only concrete semantics-preserving failures, then switch immediately to an independent non-conflicting lane while corrected CI runs.
2. Keep PRs #627–#631 Draft and isolated until the normal review/readiness gate permits integration. Do not promote them or merge to `main`.
3. Preserve the PR #5 / PR #276 merge-ref ownership blocker. Do not copy JARVIS-only modules into `main` or V3 merely to force CI green; resolve source ownership and integration order through the normal review gate.
4. Continue Memory row/event integrity, WAL/ABA, expiry/CAS, coherent snapshots, and manual-only COMMIT-UNKNOWN recovery without changing schema v1.
5. Continue Planner terminal/COMMIT-UNKNOWN recovery, durable one-shot authorization, occurrence/replay protection, and audit-before-action over disconnected mocks; do not claim a trusted clock without a trusted source.
6. Continue privacy-safe Personal Context, proactive restart/occurrence state, Observation fixture lifecycle, ToolRegistry/PermissionGate identity, and startup readiness.
7. Continue free-only V3 approval/path/identity/reproducibility guards. Keep PR #5 Draft/unmerged; no protected evaluation, training, or Candidate promotion.
8. Keep all UI/frontend work paused; PR #9 and Local UI freezes remain untouched.

---
## Historical checkpoint — saved at 2026-11-26 08:52:39 JST (superseded)

- **Saved at:** 2026-11-26 08:52:39 JST (Asia/Tokyo).
- **Branch / PR:** `research/jarvis-foundations` / Draft PR #8; isolated research branch, not `main`.
- **Exact work-basis HEAD:** `9af4fc3d7911cafb9a6d8ed542e7449eb19f57dc` (PR #8 head re-read immediately before this checkpoint; includes the Run1443 V3 gate-reconciliation note in `docs/JARVIS_FOUNDATION_GAP_MATRIX.md`).
- **Checkpoint-result HEAD:** the GitHub commit created by this `docs/PROJECT_STATUS.md` update; its exact returned SHA is confirmed after the write and reported in the invocation summary. This file intentionally does not self-reference its own commit.
- **Overall ARK state:** V1 Local Core, V2 real-model baseline, Local UI v1, and Launcher/Gate Runner retain frozen evidence. Memory, Planner, ToolRegistry, PermissionGate, ActionAudit, Personal Context, proactive state, Observation, disconnected/mock execution, and free-only V3 guard work remain isolated local-first foundations. **ARK/JARVIS overall remains NOT_PASSED.**
- **PR #8 source-basis CI:** run [45717115355](https://github.com/Iam-2squared/ark-ai/actions/runs/45717115355) on prior source HEAD `963e8e67c63b36a376208d29efe06e23cb87be7b`, **GREEN 6/6**. The current PR #8 head `9af4fc3d7911cafb9a6d8ed542e7449eb19f57dc` contains documentation-only gap-matrix reconciliation; no workflow run was returned for this exact docs head at the checkpoint lookup.
- **Main / UI boundary:** PR #5 remains gated Draft/unmerged. PR #8 remains Draft/unmerged. PR #9 remains untouched and Draft/unmerged. All new UI/frontend development remains paused. No main write or merge occurred.

## NEW work this invocation

1. **Proactive state process-level first-open and CAS races — Draft PR #629.**
   - Branch `research/run1441-proactive-state-two-handle-cas-20261126`; exact child HEAD `6ce42bc7e26ffe1a2dfa9696cac4df488d5b4b83`; targets only PR #8.
   - Adds spawned-process tests for concurrent first-open schema convergence, genesis `expected_revision=0` contention, and same-revision update contention. The intended invariant is one durable winner and one domain-level CAS conflict; no production source, schema, or policy vocabulary changed.
   - Exact-head run [45723833690](https://github.com/Iam-2squared/ark-ai/actions/runs/45723833690) (run 7797) is **IN PROGRESS**. No local pytest/Ruff run is claimed.

2. **Personal Context replay process-level CAS — Draft PR #630.**
   - Branch `research/run1442-context-replay-two-process-cas-20261126`; current exact child HEAD `d81efcd86a78ba138b73c5401c0ccc1e5abce6ef`; targets only PR #8.
   - Adds two-process races for identical request identity and disjoint requests sharing a retained genesis witness. The losing disjoint request must cold-read the new prefix before a separate reservation; receipts remain denial-only and fixture plaintext is not stored.
   - Initial exact-head run [45724103264](https://github.com/Iam-2squared/ark-ai/actions/runs/45724103264) (run 7798) failed Ruff I001 because a blank line separated `pytest` from the repository's third-party `ark` import group. The smallest import-group correction is at `d81efcd86a78ba138b73c5401c0ccc1e5abce6ef`; fresh exact-head run [45724637568](https://github.com/Iam-2squared/ark-ai/actions/runs/45724637568) (run 7802) is **QUEUED**.

3. **Action Audit process-level first-open and append sequencing — Draft PR #631.**
   - Branch `research/run1443-action-audit-process-first-open-20261126`; exact child HEAD `ad6328cc121b558cf960e65e5805d73c57a2527c`; targets only PR #8.
   - Adds a spawned-process concurrent WAL/bootstrap regression followed by one synthetic append per process. A cold reader checks schema version 1, SQLite quick_check, dense event IDs 1–2, and absence of raw private marker values. No production source, schema, or executor integration changed.
   - Exact-head run [45724216924](https://github.com/Iam-2squared/ark-ai/actions/runs/45724216924) (run 7799) is **IN PROGRESS**.

4. **V3 gap-matrix live reconciliation — parent PR #8 documentation commit `9af4fc3d7911cafb9a6d8ed542e7449eb19f57dc`.**
   - Records PR #5 exact source HEAD `ea373c3496d06e2789cee5bb58836054ef35ed28` and its exact-head run [45668716864](https://github.com/Iam-2squared/ark-ai/actions/runs/45668716864) (run 7744), which fails all six matrix jobs at Ruff I001 in three test paths absent from the PR #5 head branch and present through the base merge ref. No `main` change, test deletion, JARVIS module copy, or gate bypass was attempted.
   - Marks Run1346's strict duplicate/non-finite parser and nested symlink-grandparent gaps as superseded by the exact PR #5 source and PR #624 reconciliation (run 45708528169 GREEN 6/6). PR #623, #625, and #626 retain their previously recorded exact-head GREEN evidence.

## Tests, CI and evidence

- PR #8 prior source HEAD `963e8e67c63b36a376208d29efe06e23cb87be7b`: run 45717115355, **GREEN 6/6**. Current docs-only checkpoint/matrix head `9af4fc3d7911cafb9a6d8ed542e7449eb19f57dc`: no exact-head workflow run returned at lookup.
- PR #627 disconnected mock executor two-handle WRITE race: run 45716635322, **GREEN 6/6**.
- PR #628 PlannerJournal diamond RUNNING-barrier recovery: run 45716909855, **GREEN 6/6**.
- PR #629 proactive state process-level first-open/CAS: run 45723833690, **IN PROGRESS**.
- PR #630 Personal Context replay process-level CAS: run 45724103264 **FAIL** at Ruff I001; corrected exact child HEAD `d81efcd86a78ba138b73c5401c0ccc1e5abce6ef`, run 45724637568 **QUEUED**.
- PR #631 Action Audit process-level first-open/append: run 45724216924, **IN PROGRESS**.
- PR #5 exact source HEAD `ea373c3496d06e2789cee5bb58836054ef35ed28`: run 45668716864 **FAIL** at Ruff I001 in the three merge-ref test paths recorded above. This is not a green V3 gate.
- PR #623: run 45708896479 **GREEN 6/6**; PR #624: run 45708528169 **GREEN 6/6**; PR #625: run 45716697765 **GREEN 6/6**; PR #626: run 45716706277 **GREEN 6/6**.
- No local pytest/Ruff execution, physical-PC verification, live personal-data access, real-model runtime, GPU query, V3 preflight/training, protected evaluation, live observation capture, or production dispatch is claimed.

## Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1, and Launcher/Gate Runner evidence remain frozen.
- Memory v1 DDL/schema/retention, PlannerJournal v1 DDL/event/hash/CAS, ActionAudit v1 DDL/event fields, ToolCall/PermissionGate public contracts, Observation Envelope v1, Personal Context privacy/consent boundaries, and V3 Contract 1 remain unchanged.
- PR #5 remains gated Draft/unmerged; PR #8 remains Draft/unmerged; PR #9 remains untouched. PRs #627–#631 remain isolated Draft children; none has been integrated. No main write or merge occurred.
- No UI/frontend feature, polish, test, or integration work occurred.

## Blockers and authorization boundaries

- **PR #5 merge-ref ownership/lint blocker:** exact-head run 45668716864 fails Ruff I001 in three test paths that are not present at PR #5's own head. Preserve this as a repository/base-branch issue for normal reconciliation. Do not alter `main`, disable Ruff/tests, copy foundation modules into V3, or open the protected gate.
- **Draft integration gate:** PRs #627–#631 remain Draft and target only PR #8. No ready-for-review transition or merge bypass is attempted. PR #8 remains Draft/unmerged.
- **Free-only:** no paid/external GPU, paid API/service, subscription, purchase, or potentially billable action was started.
- No real Candidate adapter/weight generation, V3 preflight/training, protected V2 final-evaluation opening, Candidate promotion, new credentials/secrets/account connection, unavailable physical-PC action, destructive operation, or irreversible data change occurred.
- Synthetic process/SQLite tests do not prove fsync/power-loss durability, trusted time, authenticated consent, independent custody, cross-store atomicity, or exactly-once external effects. Personal Context receipts remain denial-only; proactive state remains synthetic and non-notifying; ActionAudit evidence is local only.
- No frozen-contract change or human-review decision is inferred from CI.

## Next plan / 今後の方針

1. Inspect exact-head CI for PRs #629–#631 once useful results are available. Fix only concrete semantics-preserving failures, then switch immediately to an independent non-conflicting lane while corrected CI runs.
2. Keep PRs #627–#631 Draft and isolated until the normal review/readiness gate permits integration. Do not promote them or merge to `main`.
3. Continue Memory row/event integrity, WAL/ABA, expiry/CAS, coherent snapshots, and manual-only COMMIT-UNKNOWN recovery without changing schema v1.
4. Continue Planner terminal/COMMIT-UNKNOWN recovery, durable one-shot authorization, occurrence/replay protection, and audit-before-action over disconnected mocks; do not claim a trusted clock without a trusted source.
5. Continue privacy-safe Personal Context, proactive restart/occurrence state, Observation fixture lifecycle, ToolRegistry/PermissionGate identity, and startup readiness.
6. Continue free-only V3 approval/path/identity/reproducibility guards. Preserve PR #5's merge-ref lint blocker; do not open protected evaluation, train, or promote a Candidate.
7. Keep all UI/frontend work paused; PR #9 and Local UI freezes remain untouched.

---
## Historical checkpoint — saved at 2026-11-26 07:52:59 JST (superseded)

- **Saved at:** 2026-11-26 07:52:59 JST (Asia/Tokyo).
- **Branch / PR:** \`research/jarvis-foundations\` / Draft PR #8; isolated research branch, not \`main\`.
- **Exact work-basis HEAD:** \`5a344d250dd0ef2a208ccd09f5d791b10c548bbe\` (PR #8 head and branch ref re-read immediately before this checkpoint update).
- **Checkpoint-result HEAD:** the GitHub commit created by this \`docs/PROJECT_STATUS.md\` update; its exact returned SHA is confirmed after the write and reported in the invocation summary. This file intentionally does not self-reference its own commit.
- **Overall ARK state:** V1 Local Core, V2 real-model baseline, Local UI v1, and Launcher/Gate Runner retain frozen evidence. Memory, Observation, Personal Context, Planner, ToolRegistry, PermissionGate, proactive state, ActionAudit, disconnected/mock execution, and free-only V3 guard work remain isolated local-first foundations. **ARK/JARVIS overall remains NOT_PASSED.**
- **PR #8 exact-head CI:** run [45708999545](https://github.com/Iam-2squared/ark-ai/actions/runs/45708999545) on \`5a344d250dd0ef2a208ccd09f5d791b10c548bbe\`, **GREEN 6/6**.
- **Main / UI boundary:** PR #5 remains gated Draft/unmerged. PR #8 remains Draft/unmerged. PR #9 remains untouched and Draft/unmerged. All new UI/frontend development remains paused. No main write or merge occurred.

## NEW work this invocation

1. **V3 local-only attempt/finalization receipts — Draft PR #625.**
   - Branch \`research/run1437-v3-attempt-finalization-ledger-20261126\`; current exact child HEAD \`8a9fe18bf3cbb54f6e72dd372d3ac2a4e7474a3a\`; targets only gated Draft PR #5.
   - Adds an isolated SQLite append-only ledger: one reservation per execution-snapshot digest, one optional FINALIZED event, schema/foreign-key/hash-chain/reservation reconciliation, explicit COMMIT-UNKNOWN errors, cold recovery, and manual-review-required STARTED state. It has no resume/retry API and is not wired into training CLI/runtime.
   - Synthetic tests cover STARTED recovery, duplicate reservation, one-way finalization, lost COMMIT acknowledgements after both transitions, two-handle reservation races, and event tampering.
   - Initial exact-head runs [45715965778](https://github.com/Iam-2squared/ark-ai/actions/runs/45715965778) and [45716548441](https://github.com/Iam-2squared/ark-ai/actions/runs/45716548441) failed Ruff E501 only. The line-wrap-only correction is at current HEAD \`8a9fe18bf3cbb54f6e72dd372d3ac2a4e7474a3a\`; exact-head run [45716697765](https://github.com/Iam-2squared/ark-ai/actions/runs/45716697765) is **GREEN 6/6**.
   - No preflight, model/tokenizer load, GPU query, training, export, Candidate generation, protected V2 evaluation, or local pytest/Ruff execution occurred.

2. **Crash-consistent create-only V3 run-manifest publication — Draft PR #626.**
   - Branch \`research/run1438-v3-atomic-manifest-publication-20261126\`; current exact child HEAD \`e8673cc6615613ab01e2bea285bbd9ea277ecbe6\`; targets only gated Draft PR #5.
   - Changes the existing manifest writer to write canonical bytes to an exclusive temporary sibling outside the Candidate tree, handle short writes, fsync the file, publish through a same-filesystem create-only hard link, verify final inode identity, and fsync the directory on POSIX. No overwrite or weaker direct-write fallback is provided.
   - Synthetic tests cover partial writes, fsync-before-link ordering, failed-link cleanup, and preservation of an existing final file. Manifest schema and canonical bytes are unchanged.
   - Initial exact-head run [45716397812](https://github.com/Iam-2squared/ark-ai/actions/runs/45716397812) failed one test assertion because the test rebuilt a manifest after the final file correctly existed. The test now compares against its pre-publication expected manifest; exact-head run [45716706277](https://github.com/Iam-2squared/ark-ai/actions/runs/45716706277) is **GREEN 6/6**.
   - No Candidate run was created; no preflight, model/tokenizer load, GPU query, training, export, or local pytest/Ruff execution occurred. POSIX directory fsync is attempted; Windows does not claim directory-sync durability.

3. **Disconnected mock executor two-handle WRITE race — Draft PR #627.**
   - Branch \`research/run1439-disconnected-executor-two-handle-race-20261126\`; exact child HEAD \`702cd55f9686582b5734fab6b4278ed8ceefec81\`; targets only PR #8.
   - Test-only composition race: two executor instances with separate process-local PermissionGates and SQLite occurrence handles contend for the same WRITE request, one-shot token, and occurrence ID. The expected result is exactly one durable reservation, one actual gate consumption, one mock call, and one pre-action/completion audit pair; the losing executor must stop before its gate or backend.
   - Exact-head run [45716635322](https://github.com/Iam-2squared/ark-ai/actions/runs/45716635322) is **IN PROGRESS**. No production source or frozen contract changed.

4. **PlannerJournal diamond RUNNING-barrier recovery — Draft PR #628.**
   - Branch \`research/run1440-planner-journal-diamond-running-barrier-20261126\`; exact child HEAD \`07dddf801c6ab622152e5721bf52f0bdfa84e2c9\`; targets only PR #8.
   - Test-only production PlannerJournal scenario: root succeeds, both diamond branches enter RUNNING, one branch fails and blocks its pending join/leaf, while the other remains ambiguous RUNNING through cold recovery. Resolving that remaining branch cannot resurrect the terminally blocked join.
   - Exact-head run [45716909855](https://github.com/Iam-2squared/ark-ai/actions/runs/45716909855) is **IN PROGRESS**. PlannerJournal v1 DDL/event/hash/CAS and PlanStep/ToolCall contracts are unchanged.

5. **Prior V3 child reconciliation.**
   - PR #623 local HF snapshot staging, exact HEAD \`3f10e395e92b90706286ebc384dae07edbc9f09d\`, run [45708896479](https://github.com/Iam-2squared/ark-ai/actions/runs/45708896479): **GREEN 6/6**.
   - PR #624 free-only guard matrix reconciliation, exact HEAD \`06a053d33cdfb568e4cfc2d4a735ec18136934fc\`, run [45708528169](https://github.com/Iam-2squared/ark-ai/actions/runs/45708528169): **GREEN 6/6**.
   - PRs #616–#622 remain exact-head GREEN 6/6 as recorded in the preceding checkpoint; all seven remain Draft and isolated pending the normal review/readiness gate.

## Tests, CI and evidence

- PR #8 current work-basis HEAD \`5a344d250dd0ef2a208ccd09f5d791b10c548bbe\`: run 45708999545, **GREEN 6/6**.
- PR #616–#622: exact child-head CI remains **GREEN 6/6** for each, with IDs/SHAs preserved in the preceding checkpoint.
- PR #623: current exact child head \`3f10e395e92b90706286ebc384dae07edbc9f09d\`, run 45708896479, **GREEN 6/6**. Earlier failed heads remain historical only.
- PR #624: exact child head \`06a053d33cdfb568e4cfc2d4a735ec18136934fc\`, run 45708528169, **GREEN 6/6**.
- PR #625: initial runs 45715965778 and 45716548441 failed Ruff E501; corrected exact head \`8a9fe18bf3cbb54f6e72dd372d3ac2a4e7474a3a\`, run 45716697765, **GREEN 6/6**.
- PR #626: run 45716397812 failed one test assertion; corrected exact head \`e8673cc6615613ab01e2bea285bbd9ea277ecbe6\`, run 45716706277, **GREEN 6/6**.
- PR #627: exact head \`702cd55f9686582b5734fab6b4278ed8ceefec81\`, run 45716635322, **IN PROGRESS**.
- PR #628: exact head \`07dddf801c6ab622152e5721bf52f0bdfa84e2c9\`, run 45716909855, **IN PROGRESS**.
- No local pytest/Ruff execution, physical-PC verification, live personal-data access, real-model runtime, GPU query, V3 preflight/training, protected evaluation, live observation capture, or production dispatch is claimed.

## Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1, and Launcher/Gate Runner evidence remain frozen.
- Memory v1 DDL/schema/retention, PlannerJournal v1 DDL/event/hash/CAS, ActionAudit v1 DDL/event fields, ToolCall/PermissionGate public contracts, Observation Envelope v1, Personal Context privacy/consent boundaries, and V3 Contract 1 remain unchanged.
- PR #5 remains gated Draft/unmerged; PR #8 remains Draft/unmerged; PR #9 remains untouched. No UI/frontend feature, polish, test, or integration work occurred. No main write or merge occurred.
- PRs #616–#628 remain isolated Draft children; none has been integrated into PR #8, PR #5, or \`main\`.

## Blockers and authorization boundaries

- **Draft integration gate:** PRs #616–#622 remain Draft despite exact-head GREEN; the previous normal merge attempt was rejected because the child was Draft. PRs #623–#628 are also kept Draft and isolated; no ready-for-review transition or merge bypass is attempted.
- **Free-only:** no paid/external GPU, paid API/service, subscription, purchase, or potentially billable action was started.
- No real Candidate adapter/weight generation, V3 preflight/training, protected V2 final-evaluation opening, or Candidate promotion occurred. PR #5 remains gated Draft/unmerged.
- PR #5 still has unresolved external identity/review evidence and the previously documented main merge-ref ownership/lint blockers. Do not alter main, copy isolated foundation modules into V3, weaken tests, or bypass the gate.
- Attempt-ledger digests/timestamps are caller-supplied local metadata, not authenticated approval or trusted time. Successful SQLite COMMIT is not proof of fsync/power-loss durability, independent custody, cross-store atomicity, or exactly-once external effects.
- Atomic manifest publication requires same-filesystem hard-link support; POSIX directory fsync is attempted, while Windows directory-sync durability is not claimed. Unknown publication/cleanup requires inspection before retry.
- In-process class/path checks and synthetic SQLite tests are not a Python sandbox, atomic dirfd custody, authenticated consent, physical erasure, or production dispatch authorization.
- No new credentials/secrets/account connection, unavailable physical-PC action, destructive operation, irreversible data change, frozen-contract change, or main merge occurred. UI/frontend work remains paused.

## Next plan / 今後の方針

1. Inspect the exact-head CI for PRs #627 and #628 once useful results are available; fix only concrete semantics-preserving failures, then immediately switch to a non-conflicting lane while corrected CI runs.
2. Keep PRs #625–#628 Draft and isolated until the normal review/readiness gate permits integration. After that, integrate one exact-head GREEN package at a time into its parent research branch and revalidate the resulting parent head.
3. Keep PRs #616–#622 isolated until the normal review/readiness gate permits integration; do not change readiness or bypass the normal review gate.
4. Continue Memory row/event integrity, WAL/ABA, expiry/CAS, coherent snapshots, and manual-only COMMIT-UNKNOWN recovery without changing schema v1.
5. Continue Planner terminal/COMMIT-UNKNOWN recovery, durable one-shot authorization, occurrence/replay protection, and audit-before-action over disconnected mocks; do not claim a trusted clock without a trusted source.
6. Continue privacy-safe Personal Context, proactive restart/occurrence state, Observation fixture lifecycle, ToolRegistry/PermissionGate identity, and startup readiness.
7. Continue free-only V3 guard work on passive attempt/finalization receipts and crash-consistent evidence publication. Keep PR #5 gated; no preflight, training, GPU, or Candidate action.
8. Keep all UI/frontend work paused; PR #9 and Local UI freezes remain untouched.

---

## Historical checkpoint — saved at 2026-11-26 06:56:54 JST (superseded)

- **Saved at:** 2026-11-26 06:56:54 JST (Asia/Tokyo).
- **Branch / PR:** research/jarvis-foundations / Draft PR #8; isolated research branch, not main.
- **Exact work-basis HEAD:** 72bad2b15dc00075aa00bcb57289834b7ea6cf68 (PR #8 head and branch ref re-read immediately before this checkpoint update).
- **Checkpoint-result HEAD:** the GitHub commit created by this docs/PROJECT_STATUS.md update; its exact returned SHA is confirmed after the write and reported in the invocation summary. This file intentionally does not self-reference its own commit.
- **Overall ARK state:** V1 Local Core, V2 real-model baseline, Local UI v1, and Launcher/Gate Runner retain frozen evidence. Memory, Observation, Personal Context, Planner, ToolRegistry, PermissionGate, proactive state, ActionAudit, disconnected/mock execution, and free-only V3 guard work remain isolated local-first foundations. **ARK/JARVIS overall remains NOT_PASSED.**
- **PR #8 previous exact-head CI:** fee6c3cf8d6e0f34194c2f24adef4fbfc1daf360, run [45700734437](https://github.com/Iam-2squared/ark-ai/actions/runs/45700734437), **GREEN 6/6**. Current checkpoint commit is newer and has no returned workflow run at the last lookup.
- **Main / UI boundary:** PR #5 remains gated Draft/unmerged. PR #8 remains Draft/unmerged. PR #9 remains untouched and Draft/unmerged. All new UI/frontend development remains paused. No main write or merge occurred.

## NEW work this invocation

1. **V3 local HF snapshot staging — Draft PR #623.**
   - Branch research/run1435-v3-local-snapshot-staging-20261126; current exact child HEAD 3f10e395e92b90706286ebc384dae07edbc9f09d; target is only gated Draft PR #5.
   - Verifies the local source manifest against frozen base/tokenizer/probe digests; streams only manifest-listed files into a temporary tree while hashing copied bytes; re-hashes the stage; and directs both Transformers loaders to that staged path with local_files_only=True and trust_remote_code=False. The stage owner is retained through the full preflight/full-run scope and cleaned on return or exception.
   - Synthetic tests cover manifest preservation, source mutation during staging, and fake loader path isolation. The initial exact head 2ed89a59c89606a1aebbafc2c18eec2911599796 failed Ruff I001; import order was corrected at f0812464db8376f9034f1ee19739bf3b85cae809.
   - Exact-head run [45708596824](https://github.com/Iam-2squared/ark-ai/actions/runs/45708596824) then failed one synthetic test because the mutation fixture changed file length and correctly triggered the earlier size guard. The fixture now uses a same-length replacement so the test isolates digest mismatch. Current exact head 3f10e395e92b90706286ebc384dae07edbc9f09d has run [45708896479](https://github.com/Iam-2squared/ark-ai/actions/runs/45708896479) **QUEUED**; no result is claimed.
   - No local test/lint run, torch import, model load, GPU query, preflight, training, or Candidate generation occurred. This does not establish atomic dirfd custody, same-user hostile-writer isolation, platform ACL attestation, or elimination of the final rehash-to-open race.

2. **V3 free-only guard matrix reconciliation — Draft PR #624.**
   - Branch research/run1436-v3-gap-matrix-runtime-reconcile-20261126; exact child HEAD 06a053d33cdfb568e4cfc2d4a735ec18136934fc; targets only PR #8.
   - Read-only audit confirms that PR #5 already has strict duplicate/non-finite preflight-report parsing (Run1349), nested symlink-grandparent rejection before report open (Run1351), and runtime-rendered chat-template comparison with synthetic tests. Historical Run1346 claims that these three guards are absent are superseded for exact PR #5 source HEAD ea373c3496d06e2789cee5bb58836054ef35ed28.
   - Records PR #623 as the current local hash-then-stage child and reorders the remaining free-only queue around durable attempt/finalization receipts and crash-consistent evidence publication.
   - Exact-head CI run [45708528169](https://github.com/Iam-2squared/ark-ai/actions/runs/45708528169) remains **IN PROGRESS**. Documentation-only; no local test/lint execution is claimed.

3. **Exact-head GREEN child packages #616–#622.**
   - #616 ToolRegistry absent-hook custody, HEAD 597da11ce097b428ee1435a34bea1ee1ae8a5561, run 45699272456: **GREEN 6/6**.
   - #617 PlannerJournal digest epoch, HEAD f42f04d51fe1cbacb0ee83addf84ec7de67a0ce1, run 45699456768: **GREEN 6/6**.
   - #618 ActionAudit reparse-policy epoch, HEAD 1c78b8ce81ff8c388e30123a6db7cc3a39164ac9, run 45699642591: **GREEN 6/6**.
   - #619 Personal Context replay path-policy epoch, HEAD a9a0617e58ba8eb5df07e6606aa437fcc247b43b, run 45699827682: **GREEN 6/6**.
   - #620 V3 guard gap-matrix reconciliation, HEAD 139e478d51176869e6bdb43f53002adf4a25834e, run 45700074307: **GREEN 6/6**.
   - #621 proactive state absent-hook custody, HEAD feaa1eb982256b90faae4527076c36d80d58c220, run 45700262611: **GREEN 6/6**.
   - #622 proactive SQLite path-policy epoch, HEAD a30fec2ad73e9260dc5e439f7cba0e39592dae55, run 45700503587: **GREEN 6/6**.
   - These seven child PRs remain Draft and target only PR #8. The normal GitHub merge endpoint rejected the first merge attempt with HTTP 405 because PR #616 is still Draft. No ready-for-review transition, raw Git object/ref write, or bypass was attempted; all seven remain isolated pending the normal review/readiness gate.

## Tests, CI and evidence

- PR #8 prior exact-head CI: run 45700734437, GREEN 6/6; the current checkpoint commit has no returned run at the last lookup.
- PRs #616–#622: each exact child head has a GREEN 6/6 run as listed above.
- PR #623: run 45708407205 FAIL at Ruff I001 (fixed at f081); run 45708596824 FAIL at one test assertion caused by a length-changing mutation fixture; current exact head 3f10e395e92b90706286ebc384dae07edbc9f09d has run 45708896479 QUEUED.
- PR #624: exact head 06a053d33cdfb568e4cfc2d4a735ec18136934fc has run 45708528169 IN PROGRESS.
- No local pytest/Ruff execution, physical-PC verification, live personal-data access, real-model runtime, GPU query, V3 preflight/training, protected evaluation, live observation capture, or production dispatch is claimed.

## Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1, and Launcher/Gate Runner evidence remain frozen.
- Memory v1 DDL/schema/retention, PlannerJournal v1 DDL/event/hash/CAS, ActionAudit v1 DDL/event fields, ToolCall/PermissionGate public contracts, Observation Envelope v1, Personal Context privacy/consent boundaries, and V3 Contract 1 remain unchanged.
- PR #5 remains gated Draft/unmerged; PR #8 remains Draft/unmerged; PR #9 remains untouched. No UI/frontend feature, polish, test, or integration work occurred. No main write or merge occurred.
- PRs #616–#622, #623, and #624 are isolated Draft children; none has been integrated into PR #8 or main.

## Blockers and authorization boundaries

- **Draft integration gate:** PRs #616–#622 are exact-head GREEN but remain Draft; GitHub rejected the merge attempt because the PR was Draft. Keep them isolated; do not change readiness or bypass the normal review gate.
- **CI:** PR #623 has a queued corrected exact-head run; PR #624 remains in progress. Do not treat either as GREEN until the exact current head is complete.
- **Free-only:** no paid/external GPU, paid API/service, subscription, purchase, or potentially billable action was started.
- No real Candidate adapter/weight generation, V3 preflight/training, protected V2 final-evaluation opening, or Candidate promotion occurred. PR #5 remains gated Draft/unmerged.
- PR #5 still has unresolved external identity/review evidence and the previously documented main merge-ref ownership/lint blockers. Do not alter main, copy foundation modules into V3, weaken tests, or bypass the gate.
- In-process class/path-policy checks and temporary snapshot staging are not a Python sandbox, atomic dirfd custody, trusted-clock proof, independent storage custody, fsync/power-loss durability, cross-store atomicity, authenticated consent, physical erasure, or exactly-once external-effect proof.
- No new credentials/secrets/account connection, unavailable physical-PC action, destructive operation, irreversible data change, frozen-contract change, or main merge occurred. UI/frontend work remains paused.

## Next plan / 今後の方針

1. Let the queued exact-head PR #623 run and the in-progress PR #624 run complete; inspect only their actual results, fix concrete semantics-preserving failures, and switch immediately to a non-conflicting lane after each corrected CI launch.
2. Keep #616–#622 Draft and isolated until the normal review/readiness gate permits integration. After that, integrate one exact-head GREEN package at a time into PR #8 and revalidate the resulting parent head; never merge PR #8 to main without explicit approval.
3. Continue Memory row/event integrity, WAL/ABA, expiry/CAS, coherent snapshots, and manual-only COMMIT-UNKNOWN recovery without changing schema v1.
4. Continue Planner terminal/COMMIT-UNKNOWN recovery, durable one-shot authorization, occurrence/replay protection, and trusted-clock audit-before-action over disconnected mocks.
5. Continue privacy-safe Personal Context, proactive restart/occurrence state, Observation fixture lifecycle, ToolRegistry/PermissionGate identity, and startup readiness.
6. Continue free-only V3 work on durable attempt/finalization receipts and crash-consistent evidence publication. Keep PR #5 gated; no preflight, training, GPU, or Candidate action.
7. Keep all UI/frontend work paused; PR #9 and Local UI freezes remain untouched.

---


---

## Historical checkpoint — saved at 2026-11-26 06:55:33 JST (superseded)

- **Saved at:** 2026-11-26 06:55:33 JST (Asia/Tokyo).
- **Branch / PR:** research/jarvis-foundations / Draft PR #8; isolated research branch, not main.
- **Exact work-basis HEAD:** fee6c3cf8d6e0f34194c2f24adef4fbfc1daf360 (PR #8 head and branch ref re-read immediately before this checkpoint update).
- **Checkpoint-result HEAD:** the GitHub commit created by this docs/PROJECT_STATUS.md update; its exact returned SHA is confirmed after the write and reported in the invocation summary. This file intentionally does not self-reference its own commit.
- **Overall ARK state:** V1 Local Core, V2 real-model baseline, Local UI v1, and Launcher/Gate Runner retain frozen evidence. Memory, Observation, Personal Context, Planner, ToolRegistry, PermissionGate, proactive state, ActionAudit, disconnected/mock execution, and free-only V3 guard work remain isolated local-first foundations. **ARK/JARVIS overall remains NOT_PASSED.**
- **PR #8 exact-head CI:** work-basis HEAD fee6c3cf8d6e0f34194c2f24adef4fbfc1daf360, run [45700734437](https://github.com/Iam-2squared/ark-ai/actions/runs/45700734437), **GREEN 6/6**.
- **Main / UI boundary:** PR #5 remains gated Draft/unmerged. PR #8 remains Draft/unmerged. PR #9 remains untouched and Draft/unmerged. All new UI/frontend development remains paused. No main write or merge occurred.

## NEW work this invocation

1. **V3 local HF snapshot staging — Draft PR #623.**
   - Branch research/run1435-v3-local-snapshot-staging-20261126; current exact child HEAD f0812464db8376f9034f1ee19739bf3b85cae809; target is only gated Draft PR #5.
   - Verifies the local source manifest against frozen base/tokenizer/probe digests; streams only manifest-listed files into a temporary tree while hashing copied bytes; re-hashes the stage; and directs both Transformers loaders to that staged path with local_files_only=True and trust_remote_code=False.
   - Stage ownership is retained through preflight/full-run scope and cleaned on return or exception. Synthetic tests cover manifest equality, source mutation during staging, and fake loader path isolation.
   - Initial exact child HEAD 2ed89a59c89606a1aebbafc2c18eec2911599796, run [45708407205](https://github.com/Iam-2squared/ark-ai/actions/runs/45708407205), **FAIL** at Ruff I001 in the new test import block; pytest was skipped. The smallest import-order-only fix is saved at current HEAD f0812464db8376f9034f1ee19739bf3b85cae809. Fresh exact-head run [45708596824](https://github.com/Iam-2squared/ark-ai/actions/runs/45708596824) is **IN PROGRESS**.
   - No local test/lint run, torch import, model load, GPU query, preflight, training, or Candidate generation occurred. This does not establish atomic dirfd custody, same-user hostile-writer isolation, platform ACL attestation, or elimination of the final rehash-to-open race.

2. **V3 free-only guard matrix reconciliation — Draft PR #624.**
   - Branch research/run1436-v3-gap-matrix-runtime-reconcile-20261126; exact child HEAD 06a053d33cdfb568e4cfc2d4a735ec18136934fc; targets only PR #8.
   - Read-only audit confirms that PR #5 already has strict duplicate/non-finite preflight-report parsing (Run1349), nested symlink-grandparent rejection before open (Run1351), and runtime-rendered chat-template comparison with synthetic tests. Historical Run1346 claims that these three guards are absent are superseded for exact PR #5 source HEAD ea373c3496d06e2789cee5bb58836054ef35ed28.
   - Records PR #623 as the current local hash-then-stage child and reorders the remaining free-only queue around durable attempt/finalization receipts and crash-consistent evidence publication.
   - Exact-head CI run [45708528169](https://github.com/Iam-2squared/ark-ai/actions/runs/45708528169) is **IN PROGRESS**. Documentation-only; no local test/lint execution is claimed.

3. **Exact-head GREEN child packages #616–#622.**
   - #616 ToolRegistry absent-hook custody, HEAD 597da11ce097b428ee1435a34bea1ee1ae8a5561, run 45699272456: **GREEN 6/6**.
   - #617 PlannerJournal digest epoch, HEAD f42f04d51fe1cbacb0ee83addf84ec7de67a0ce1, run 45699456768: **GREEN 6/6**.
   - #618 ActionAudit reparse-policy epoch, HEAD 1c78b8ce81ff8c388e30123a6db7cc3a39164ac9, run 45699642591: **GREEN 6/6**.
   - #619 Personal Context replay path-policy epoch, HEAD a9a0617e58ba8eb5df07e6606aa437fcc247b43b, run 45699827682: **GREEN 6/6**.
   - #620 V3 guard gap-matrix reconciliation, HEAD 139e478d51176869e6bdb43f53002adf4a25834e, run 45700074307: **GREEN 6/6**.
   - #621 proactive state absent-hook custody, HEAD feaa1eb982256b90faae4527076c36d80d58c220, run 45700262611: **GREEN 6/6**.
   - #622 proactive SQLite path-policy epoch, HEAD a30fec2ad73e9260dc5e439f7cba0e39592dae55, run 45700503587: **GREEN 6/6**.
   - These seven child PRs remain Draft and target only PR #8. The normal GitHub merge endpoint rejected the first merge attempt with HTTP 405 because PR #616 is still Draft. No ready-for-review transition, raw Git object/ref write, or bypass was attempted; all seven remain isolated pending the normal review/readiness gate.

## Tests, CI and evidence

- PR #8 exact-head CI: run 45700734437, GREEN 6/6.
- PRs #616–#622: each exact child head has a GREEN 6/6 run as listed above; no predecessor run is substituted for a new head.
- PR #623: prior head run 45708407205 FAIL only at Ruff I001; corrected current head f0812464db8376f9034f1ee19739bf3b85cae809 has fresh run 45708596824 IN PROGRESS.
- PR #624: exact head 06a053d33cdfb568e4cfc2d4a735ec18136934fc has run 45708528169 IN PROGRESS.
- No local pytest/Ruff execution, physical-PC verification, live personal-data access, real-model runtime, GPU query, V3 preflight/training, protected evaluation, live observation capture, or production dispatch is claimed.

## Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1, and Launcher/Gate Runner evidence remain frozen.
- Memory v1 DDL/schema/retention, PlannerJournal v1 DDL/event/hash/CAS, ActionAudit v1 DDL/event fields, ToolCall/PermissionGate public contracts, Observation Envelope v1, Personal Context privacy/consent boundaries, and V3 Contract 1 remain unchanged.
- PR #5 remains gated Draft/unmerged; PR #8 remains Draft/unmerged; PR #9 remains untouched. No UI/frontend feature, polish, test, or integration work occurred. No main write or merge occurred.
- PRs #616–#622, #623, and #624 are isolated Draft children; none has been integrated into PR #8 or main.

## Blockers and authorization boundaries

- **Draft integration gate:** PRs #616–#622 are exact-head GREEN but remain Draft; GitHub rejected the merge attempt because the PR was Draft. Keep them isolated; do not change readiness or bypass the normal review gate.
- **Free-only:** no paid/external GPU, paid API/service, subscription, purchase, or potentially billable action was started.
- No real Candidate adapter/weight generation, V3 preflight/training, protected V2 final-evaluation opening, or Candidate promotion occurred. PR #5 remains gated Draft/unmerged.
- PR #5 still has unresolved external identity/review evidence and the previously documented main merge-ref ownership/lint blockers. Do not alter main, copy foundation modules into V3, weaken tests, or bypass the gate.
- In-process class/path-policy checks and temporary snapshot staging are not a Python sandbox, atomic dirfd custody, trusted-clock proof, independent storage custody, fsync/power-loss durability, cross-store atomicity, authenticated consent, physical erasure, or exactly-once external-effect proof.
- No new credentials/secrets/account connection, unavailable physical-PC action, destructive operation, irreversible data change, frozen-contract change, or main merge occurred. UI/frontend work remains paused.

## Next plan / 今後の方針

1. Inspect the fresh exact-head CI for #623 and #624 when useful; fix only concrete semantics-preserving failures and immediately switch to a non-conflicting lane while corrected CI runs.
2. Keep #616–#622 Draft and isolated until the normal review/readiness gate permits integration. After that, integrate one exact-head GREEN package at a time into PR #8 and revalidate the resulting parent head; never merge PR #8 to main without explicit approval.
3. Continue Memory row/event integrity, WAL/ABA, expiry/CAS, coherent snapshots, and manual-only COMMIT-UNKNOWN recovery without changing schema v1.
4. Continue Planner terminal/COMMIT-UNKNOWN recovery, durable one-shot authorization, occurrence/replay protection, and trusted-clock audit-before-action over disconnected mocks.
5. Continue privacy-safe Personal Context, proactive restart/occurrence state, Observation fixture lifecycle, ToolRegistry/PermissionGate identity, and startup readiness.
6. Continue free-only V3 work on durable attempt/finalization receipts and crash-consistent evidence publication. Keep PR #5 gated; no preflight, training, GPU, or Candidate action.
7. Keep all UI/frontend work paused; PR #9 and Local UI freezes remain untouched.

---

## Historical checkpoint — saved at 2026-11-26 06:02:43 JST (superseded)

- **Saved at:** 2026-11-26 06:02:43 JST (Asia/Tokyo).
- **Branch / PR:** `research/jarvis-foundations` / Draft PR #8; isolated research branch, not `main`.
- **Exact work-basis HEAD:** `c6ee53c5e5671b926b7625da7a7b5dfdd41ae7d3` (PR #8 head and branch ref re-read immediately before this checkpoint update).
- **Checkpoint-result HEAD:** the GitHub commit created by this `docs/PROJECT_STATUS.md` update; its exact returned SHA is confirmed after the write and reported in the invocation summary. This file intentionally does not self-reference its own commit.
- **Overall ARK state:** V1 Local Core, V2 real-model baseline, Local UI v1, and Launcher/Gate Runner retain their frozen evidence. Memory, Observation, Personal Context, Planner, ToolRegistry, PermissionGate, proactive state, ActionAudit, disconnected/mock execution, and V3 free-only guard work remain isolated local-first foundations. **ARK/JARVIS overall remains NOT_PASSED.**
- **Parent exact-head validation:** PR #8 work-basis/checkpoint-result HEAD `c6ee53c5e5671b926b7625da7a7b5dfdd41ae7d3`, workflow run [45690936602](https://github.com/Iam-2squared/ark-ai/actions/runs/45690936602), is **GREEN 6/6** (Windows/Linux × Python 3.11–3.13).
- **Main / UI boundary:** PR #5 remains gated Draft/unmerged. PR #8 remains Draft/unmerged. PR #9 remains untouched and Draft/unmerged. All new UI/frontend development remains paused. No `main` write or merge occurred.

## NEW work this invocation

Seven independent packages were rebased onto the exact PR #8 parent HEAD `c6ee53c5e5671b926b7625da7a7b5dfdd41ae7d3`. Each child branch is isolated and targets only `research/jarvis-foundations`; none is merged into PR #8 or `main`.

1. **ToolRegistry absent-hook custody — Draft PR #616.**
   - Branch `research/run1428-tool-registry-absent-hook-latest-20261126`; exact child HEAD `597da11ce097b428ee1435a34bea1ee1ae8a5561`.
   - Reapplied the absent-hook sentinel/class epoch and synthetic regressions. Parent source blob `4e1d1edf54ba383cceed87013c50c40a0d13232e` was identical to the predecessor base.
   - Exact-head CI run [45699272456](https://github.com/Iam-2squared/ark-ai/actions/runs/45699272456): **IN PROGRESS**.

2. **PlannerJournal digest dependency epoch — Draft PR #617.**
   - Branch `research/run1429-planner-digest-epoch-latest-20261126`; exact child HEAD `f42f04d51fe1cbacb0ee83addf84ec7de67a0ce1`.
   - Reapplied retained hashlib/SHA-256/json serializer epoch and joint-substitution/reentrant-serialization regressions. Parent source blob `4f8cc62d2adb31603bbb436df8ff87d6cf3ac4fd` was identical to the predecessor base.
   - Exact-head CI run [45699456768](https://github.com/Iam-2squared/ark-ai/actions/runs/45699456768): **IN PROGRESS**.

3. **ActionAudit reparse-policy epoch — Draft PR #618.**
   - Branch `research/run1430-action-audit-reparse-epoch-latest-20261126`; exact child HEAD `1c78b8ce81ff8c388e30123a6db7cc3a39164ac9`.
   - Reapplied stat/reparse dependency-epoch and post-metadata callback checks with synthetic regressions. Parent source blob `0d861227646eb502904217b1cf2eb09e770ec5e8` was identical to the predecessor base.
   - Exact-head CI run [45699642591](https://github.com/Iam-2squared/ark-ai/actions/runs/45699642591): **IN PROGRESS**.

4. **Personal Context replay path-policy epoch — Draft PR #619.**
   - Branch `research/run1431-personal-context-replay-path-epoch-latest-20261126`; exact child HEAD `a9a0617e58ba8eb5df07e6606aa437fcc247b43b`.
   - Reapplied stat/reparse/path-policy epoch and callback checks. Parent source blob `5d2bef090aaec326296a746b8b9215696007df5d` was identical to the predecessor base.
   - Exact-head CI run [45699827682](https://github.com/Iam-2squared/ark-ai/actions/runs/45699827682): **IN PROGRESS**.

5. **V3 free-only guard gap-matrix reconciliation — Draft PR #620.**
   - Branch `research/run1432-v3-gap-matrix-latest-20261126`; exact child HEAD `139e478d51176869e6bdb43f53002adf4a25834e`.
   - Prepended the Run1420 correction to the existing matrix without deleting historical audit content. Re-read gated PR #5 source HEAD `ea373c3496d06e2789cee5bb58836054ef35ed28` unchanged. Strict duplicate/non-finite preflight-report parsing and nested symlink-grandparent rejection are already present; the remaining free-only priorities are local hash-then-use staging, runtime-rendered chat-template identity, and durable attempt/finalization receipts.
   - Exact-head CI run [45700074307](https://github.com/Iam-2squared/ark-ai/actions/runs/45700074307): **QUEUED**. Documentation-only; no V3 runtime or gate opening.

6. **Proactive state absent-hook custody — Draft PR #621.**
   - Branch `research/run1433-proactive-state-absent-hook-latest-20261126`; exact child HEAD `feaa1eb982256b90faae4527076c36d80d58c220`.
   - Reapplied proactive state absent-hook sentinel/epoch guard and synthetic regressions. Parent source blob `ef8503824a03dae48d04d46bb31e6ea0943e433c` was identical to the predecessor base.
   - Exact-head CI run [45700262611](https://github.com/Iam-2squared/ark-ai/actions/runs/45700262611): **QUEUED**.

7. **Proactive SQLite path-policy epoch — Draft PR #622.**
   - Branch `research/run1434-proactive-path-policy-latest-20261126`; exact child HEAD `a30fec2ad73e9260dc5e439f7cba0e39592dae55`.
   - Reapplied stat/reparse/sidecar policy epoch, synthetic regressions, and the narrow transient-journal metadata-fixture correction. Parent source blob `eb192fac2b7642af32b91c0636a5118cefbb3dbe` and pre-correction transient-journal test blob `5d907b9d49cb877a95e40eca37726271bc8b2571` were identical to the predecessor base.
   - No PR-triggered workflow run was returned for this exact child HEAD at the last read; no CI result is claimed.

## Tests, CI and evidence

- **PR #8 exact-head:** `c6ee53c5e5671b926b7625da7a7b5dfdd41ae7d3`, run [45690936602](https://github.com/Iam-2squared/ark-ai/actions/runs/45690936602): **GREEN 6/6**.
- **Predecessor child exact-head evidence:** PR #609 run [45688812009](https://github.com/Iam-2squared/ark-ai/actions/runs/45688812009), PR #610 [45689141624](https://github.com/Iam-2squared/ark-ai/actions/runs/45689141624), PR #611 [45689545926](https://github.com/Iam-2squared/ark-ai/actions/runs/45689545926), PR #612 [45689890616](https://github.com/Iam-2squared/ark-ai/actions/runs/45689890616), PR #613 [45690053012](https://github.com/Iam-2squared/ark-ai/actions/runs/45690053012), PR #614 [45690251664](https://github.com/Iam-2squared/ark-ai/actions/runs/45690251664), and PR #615 [45690672654](https://github.com/Iam-2squared/ark-ai/actions/runs/45690672654) were each **GREEN 6/6 on their predecessor child heads only**. None transfers to the new rebased child heads.
- **New exact-head child CI:** #616 run `45699272456` IN PROGRESS; #617 `45699456768` IN PROGRESS; #618 `45699642591` IN PROGRESS; #619 `45699827682` IN PROGRESS; #620 `45700074307` QUEUED; #621 `45700262611` QUEUED; #622 no run returned at last read.
- No local pytest/Ruff execution, physical-PC verification, live personal-data access, real-model runtime, GPU query, V3 preflight/training, protected evaluation, live observation capture, or production dispatch is claimed.

## Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1, and Launcher/Gate Runner evidence remain frozen.
- Memory v1 DDL/schema/retention, PlannerJournal v1 DDL/event/hash/CAS, ActionAudit v1 DDL/event fields, ToolCall/PermissionGate public contracts, Observation Envelope v1, Personal Context privacy/consent boundaries, and V3 Contract 1 remain unchanged.
- PR #5 remains gated Draft/unmerged; PR #8 remains Draft/unmerged; PR #9 remains untouched. No UI/frontend feature, polish, test, or integration work occurred. No `main` write or merge occurred.
- All new children #616–#622 target only the isolated PR #8 foundation branch. No child has been integrated yet.

## Blockers and authorization boundaries

- **Free-only:** no paid/external GPU, paid API/service, subscription, purchase, or potentially billable action was started.
- No real Candidate adapter/weight generation, V3 preflight/training, protected V2 final-evaluation opening, or Candidate promotion occurred.
- PR #5 remains blocked by its documented base-owned Ruff I001 paths and the separate PR #483 merge-ref pytest-collection ownership issue. Do not alter `main`, copy foundation modules into V3, weaken tests, or bypass the gate.
- In-process class/path-policy checks are not a Python sandbox, atomic `dirfd` custody, trusted-clock proof, independent storage custody, fsync/power-loss durability, cross-store atomicity, authenticated consent, physical erasure, or exactly-once external-effect proof.
- No new credentials/secrets/account connection, unavailable physical-PC action, destructive operation, irreversible data change, frozen-contract change, or main merge occurred. UI/frontend work remains paused.

## Next plan / 今後の方針

1. Inspect the exact-head CI for #616–#622 once results are useful; fix only concrete semantics-preserving failures, and immediately switch to an independent lane while any corrected run executes.
2. After each child is exact-head GREEN, re-read the latest PR #8 head and integrate only non-overlapping, dependency-safe packages into the PR #8 research branch one at a time. Keep PR #8 Draft/unmerged; do not merge to `main`.
3. Continue Memory WAL/ABA, expiry/CAS, coherent snapshots, and COMMIT-UNKNOWN manual-only recovery; preserve schema v1.
4. Continue Planner terminal/COMMIT-UNKNOWN recovery, durable one-shot authorization, occurrence/replay protection, and trusted-clock audit-before-action over disconnected mocks.
5. Continue privacy-safe Personal Context, proactive restart/occurrence state, Observation fixture lifecycle, and startup readiness.
6. Continue free-only V3 guard work on local hash-then-use staging, runtime-rendered chat-template identity, and durable attempt/finalization receipts. Keep PR #5 gated.
7. Keep all UI/frontend work paused; PR #9 and Local UI freezes remain untouched.

---

## Historical checkpoint — saved at 2026-11-26 04:00:56 JST

- **Saved at:** 2026-11-26 04:00:56 JST (Asia/Tokyo).
- **Branch / PR:** `research/jarvis-foundations` / Draft PR #8; isolated research branch, not `main`.
- **Exact work-basis HEAD:** `ae3c330f11513c782bed9703febc8ac0c3a31747` (branch ref re-read immediately before this checkpoint update).
- **Checkpoint-result HEAD:** the GitHub commit created by this `docs/PROJECT_STATUS.md` update; its exact returned SHA is confirmed after the write and reported in the invocation summary. This file intentionally does not self-reference its own commit.
- **Overall ARK state:** V1 Local Core, V2 real-model baseline, Local UI v1 and Launcher/Gate Runner retain frozen evidence. Local-first JARVIS foundations continue in isolated/reversible Draft branches. **ARK/JARVIS overall remains NOT_PASSED.**
- **Main / UI boundary:** PR #5 remains gated Draft/unmerged. PR #8 remains Draft/unmerged. PR #9 remains Draft/unmerged and untouched at `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`; all new UI/frontend work remains paused. No `main` write or merge occurred.

## NEW work this invocation

1. **ToolRegistry absent-hook custody rebase — Draft PR #605.**
   - Child branch: `research/rebase-run1419-tool-registry-absent-hook-custody-20261126`; exact child HEAD: `ddd0bf52c86e2b1d5660be5a33f294c48c53eeae`.
   - Reapplied the Run1419 class-hook absence sentinel/epoch guard, regression tests and evidence note onto current PR #8 basis. The source blob was verified identical between old base `996d557f6b723229ffc201ac827b8a908e90a7ae` and current parent, so no intervening registry source was overwritten.
   - Predecessor PR #601 exact-head CI `45669883259` is GREEN 6/6 on its older child head only. New PR #605 exact-head CI `45678685362` is IN PROGRESS (Ubuntu 3/3 GREEN; Windows 3/3 running).

2. **V3 free-only gap-matrix reconciliation — Draft PR #606.**
   - Child branch: `research/run1420-v3-gap-matrix-reconcile-20261126`; exact child HEAD: `02118f0be6810fa501a53fdc9dc3c70c906c2a26`.
   - Documentation-only, read-only audit against gated PR #5 HEAD `ea373c3496d06e2789cee5bb58836054ef35ed28`. Verified Run1349 strict duplicate-key/non-finite preflight-report parsing and Run1351 nested symlink-grandparent rejection are already present; removed both from the active work queue in the matrix.
   - Recorded PR #5 exact-head CI run `45668716864` FAIL 6/6 at Ruff I001 in three files supplied by `main`, and PR #483's separate pytest-collection blocker because foundation modules are absent from `main`. No main change or V3 gate opening.

3. **PlannerJournal digest dependency epoch rebase — Draft PR #607.**
   - Child branch: `research/rebase-run1398-planner-digest-epoch-20261126`; exact child HEAD: `e18a82d2b6f55a9bac2a0b591bf455b3dd449ec1`.
   - Preserved the current PlannerJournal source and reapplied the narrow digest-module/serializer epoch guard at exact unique anchors; carried forward synthetic joint-replacement and reentrant-serialization regressions.
   - Predecessor PR #577 exact-head CI `45599174248` is GREEN 6/6 on its old child head only. New PR #607 exact-head CI `45679983575` is IN PROGRESS (6 jobs running at last read).

4. **ActionAudit reparse-policy epoch rebase — Draft PR #608.**
   - Child branch: `research/rebase-run1399-action-audit-reparse-epoch-20261126`; exact child HEAD: `52e27a2ce8f7637935890bbddc01762ed86c1e5a`.
   - Preserved current ActionAudit source and reapplied the complete stat/reparse dependency epoch plus post-metadata callback recheck at exact unique anchors; carried forward synthetic pre-lstat and reentrant metadata regressions.
   - Predecessor PR #578 exact-head CI `45599489425` is GREEN 6/6 on its old child head only. No PR-triggered workflow run was returned for the new PR #608 head at the last read; no PASS is claimed.

## Tests, CI and evidence

- **PR #8 work-basis HEAD** `ae3c330f11513c782bed9703febc8ac0c3a31747`, run `45673643495`: IN PROGRESS at last read; Ubuntu 3/3 and Windows 3.11/3.12 GREEN, Windows 3.13 still running. This run does not validate the checkpoint-result HEAD; a fresh parent run is required after this status update.
- **PR #602 Personal Context replay rebase**, exact child HEAD `d3147122dd95e4705aa793943abe53efedd2f0c9`, run `45672690179`: GREEN 6/6.
- **PR #603 Observation absent-hook rebase**, exact child HEAD `72af53e9ccbacb4e645e6db67b1c8a9edd7e6685`, run `45672998348`: GREEN 6/6.
- **PR #604 READ-journal absent-hook rebase**, exact child HEAD `48682cd3e0ad475c2141d73d6f29187bbe82ec2c`, run `45673239909`: GREEN 6/6.
- **PR #605 ToolRegistry rebase**, exact child HEAD `ddd0bf52c86e2b1d5660be5a33f294c48c53eeae`, run `45678685362`: IN PROGRESS (3/6 Ubuntu GREEN; 3/6 Windows running).
- **PR #606 V3 gap-matrix audit**, exact child HEAD `02118f0be6810fa501a53fdc9dc3c70c906c2a26`, run `45679594332`: IN PROGRESS (Ubuntu Python 3.11 GREEN; remaining 5 jobs running).
- **PR #607 PlannerJournal digest epoch**, exact child HEAD `e18a82d2b6f55a9bac2a0b591bf455b3dd449ec1`, run `45679983575`: IN PROGRESS (6/6 running at last read).
- **PR #608 ActionAudit reparse epoch**, exact child HEAD `52e27a2ce8f7637935890bbddc01762ed86c1e5a`: no run returned at last read; no PASS is claimed.
- **PR #601 predecessor** exact child run `45669883259`, **PR #577 predecessor** `45599174248`, and **PR #578 predecessor** `45599489425` are GREEN 6/6 only on their older exact heads; fresh rebased child CI is required.
- No local pytest/Ruff execution, target-PC verification, live observation capture, real-model runtime, GPU query, V3 preflight/training, protected evaluation or production dispatch is claimed.

## Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1 and Launcher/Gate Runner evidence remain frozen.
- Memory v1 DDL/schema/retention, PlannerJournal v1 DDL/event/hash/CAS, ActionAudit v1 DDL/event fields, ToolCall/PermissionGate public contracts, Observation Envelope v1, Personal Context privacy/consent boundaries and V3 Contract 1 remain unchanged.
- PR #5, #8 and #9 remain Draft/unmerged. PR #9 remains untouched. No UI/frontend feature, polish, test or integration work occurred. No `main` write or merge occurred.
- PRs #602–#608 are isolated Draft children; none has been integrated into PR #8 or `main`.

## Blockers and authorization boundaries

- **Free-only:** no paid/external GPU, paid API/service, subscription, purchase or potentially billable action was started.
- PR #5 remains gated Draft/unmerged. No real Candidate adapter/weight generation, V3 preflight/training, protected V2 final-evaluation opening or Candidate promotion occurred.
- PR #5 current-head merge-ref CI failure is the three base-owned Ruff I001 paths documented in PR #606. PR #483's import-only correction still fails pytest collection because the foundation modules are not on `main`; do not edit `main`, copy foundation modules into V3, weaken tests or merge PR #5 to bypass ownership.
- PRs #602–#604 are exact-head GREEN but not yet integrated; parent CI on `ae3c330f11513c782bed9703febc8ac0c3a31747` was still running at last read. Re-read the parent branch before every integration.
- PRs #605–#608 require fresh exact-head CI. Historical predecessor GREEN results do not transfer.
- In-process class/path-policy guards are not a Python sandbox, trusted clock, independent storage custody, fsync/power-loss durability, cross-store atomicity, authenticated consent or exactly-once external-effect proof.
- No new credentials/secrets/account connection, unavailable physical-PC action, destructive operation, irreversible data change, frozen-contract change or main merge occurred. All UI/frontend work remains paused.

## Next plan / 今後の方針

1. Inspect PR #8 run `45673643495` once it completes. If GREEN, integrate PRs #602, #603 and #604 one at a time after exact dependency review and a fresh parent-HEAD read; keep PR #8 Draft/unmerged.
2. Inspect exact-head CI for PRs #605–#608 once useful results are available; fix only concrete failures and launch one fresh run per corrected child head.
3. After fresh exact-head GREEN, integrate ToolRegistry (#605), PlannerJournal digest (#607) and ActionAudit path-policy (#608) into PR #8 in dependency-safe order. Do not infer production readiness or external execution authority.
4. Revisit Personal Context path-policy and proactive path-policy packages only after their overlapping replay/state source paths and the current #602/#597 work are reconciled.
5. Continue Memory CAS/expiry/coherent snapshots, Planner terminal/COMMIT-UNKNOWN recovery, durable one-shot authorization, audit-before-action, disconnected mock execution, startup readiness, privacy-safe Personal Context and Observation fixture lifecycle.
6. Continue free-only V3 local identity/path/provenance guard work only; no preflight, training, protected V2 evaluation or Candidate promotion.
7. Keep all UI/frontend development paused; PR #9 and Local UI freezes remain untouched.

---

## Historical checkpoint — saved at 2026-11-26 03:16:55 JST

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

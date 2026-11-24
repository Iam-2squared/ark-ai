# LATEST — ARK AI canonical current checkpoint

**Saved at:** 2026-11-24 11:48:42 JST (Asia/Tokyo)
**Canonical status authority:** `docs/PROJECT_STATUS_CURRENT.md`.
**Legacy status archive:** `docs/PROJECT_STATUS.md` is preserved unchanged (1,057,799 bytes at this checkpoint). Its size exceeds the normal GitHub Contents API update limit, so this small file is the current authoritative checkpoint; no history was truncated or rewritten.
**Branch / PR:** `research/jarvis-foundations` / Draft PR #8 (base `main`; OPEN/DRAFT/UNMERGED).
**Work-basis HEAD:** `883006bfdfbd9c9d0408b78d350b767e451d7955` — PR #8 head and branch tip re-read immediately before this checkpoint write.
**Checkpoint-result HEAD:** the documentation-only commit returned by the normal GitHub Contents API and verified against the live branch tip immediately after the write; intentionally not self-embedded.
**main HEAD:** `9767fef35eef2115138b5714ebf672dc825636c9` (read-only).
**V3 parent branch:** `research/v3-learning-evaluation` at `ce7a3498472ef1fbcfc36496817bf3c10f6d18f2` (Draft PR #5 remains OPEN/DRAFT/UNMERGED).

## Current ARK state

- ARK/JARVIS remains **NOT_PASSED**. No later-version PASS, human-review decision, trusted-clock certification, authenticated consent, physical hardware readiness, physical erasure, production dispatch or exactly-once external-effect claim is made.
- Draft PR #8 remains the isolated JARVIS/core foundation branch. PR #421 was integrated into PR #8's branch only; resulting code head is `883006bfdfbd9c9d0408b78d350b767e451d7955`. No main merge occurred.
- PR #5 remains gated Draft/unmerged. Protected V2 final evaluation remains closed; no Candidate adapter/weight generation or promotion was opened.
- PR #9 remains OPEN/DRAFT/UNMERGED at `3b49048dd70eebcb6268299b9ecef4e301bbc0fd` and untouched. All new UI/frontend development, UI integration, polish and frontend tests remain paused.
- V1/V2/Local UI/Launcher frozen evidence and all frozen contracts remain unchanged.
- No paid/external compute, credentials, new account connection, physical-PC action, external backend dispatch or destructive data operation was performed.

## NEW work this invocation

1. **Unicode privacy/identity hardening integrated into PR #8 — PR #421.**
   - Child branch `research/run1238-unicode-privacy-identity-rebase`, exact child HEAD `dadcd542bbcff6188e50b5f61f09a3ff6c1438de`.
   - Exact-head CI [45309777957](https://github.com/Iam-2squared/ark-ai/actions/runs/45309777957) **GREEN, 6/6** Windows/Linux × Python 3.11–3.13.
   - Normal squash merge integrated Unicode General Category Cf rejection and pinned classifier checks across Personal Context policy identity, disconnected Observation fixture metadata and proactive-state identity into PR #8 only. Japanese metadata/identity remains accepted. Observation Envelope v1, Memory v1, proactive CAS and frozen contracts were not changed.
   - PR #8 resulting code head: `883006bfdfbd9c9d0408b78d350b767e451d7955`. Parent CI for this new code head is separately tracked below.

2. **Production Planner terminal hard-exit regression — Draft PR #424.**
   - Branch `research/run1241-planner-terminal-hard-exit`, exact child HEAD `762395a8aa8c2b142121d1a46c2d5c36c6f94340`, based on PR #8 work-basis `883006bfdfbd9c9d0408b78d350b767e451d7955`.
   - Test-only production `PlannerJournal` coverage: a spawned process commits root FAILED and exits immediately after native SQLite COMMIT; cold recovery must retain root FAILED, dependent BLOCKED and independent PENDING with exact revisions and event prefix.
   - No Planner source/schema change, ToolBackend call, dispatch authority or automatic replay authority.

3. **Production Memory post-COMMIT hard-exit regression — Draft PR #425.**
   - Branch `research/run1242-memory-put-native-commit-hard-exit`, exact child HEAD `bab9292ecab33d4f5a52e292c83ba8823ace7acd`, based on PR #8 work-basis `883006bfdfbd9c9d0408b78d350b767e451d7955`.
   - Test-only production `SQLiteMemoryStore.put` coverage: a spawned process updates a synthetic private row and event, then exits immediately after native context-manager COMMIT before Python cleanup/record return; cold reopen must recover revision 2 and exactly one create/update event.
   - No Memory source, DDL or public API change.

4. **Read-only CI and boundary review.**
   - PR #5 remains blocked at its existing Ruff gate; no main write, main merge or protected evaluation opening was attempted.
   - PR #422 proactive process-exit test and PR #423 ToolRegistry deletion-seal test remain separate child PRs on the older PR #8 base; their green child CI does not certify the new parent head.

## Tests / CI / evidence — exact heads only

- PR #8 code head `883006bfdfbd9c9d0408b78d350b767e451d7955`: [CI 45314486627](https://github.com/Iam-2squared/ark-ai/actions/runs/45314486627) **IN_PROGRESS** at checkpoint preparation. This run is on the code head before this documentation-only checkpoint commit; it does not certify the resulting checkpoint head.
- PR #424 `762395a8aa8c2b142121d1a46c2d5c36c6f94340`: [CI 45314707305](https://github.com/Iam-2squared/ark-ai/actions/runs/45314707305) **IN_PROGRESS**.
- PR #425 `bab9292ecab33d4f5a52e292c83ba8823ace7acd`: [CI 45314873544](https://github.com/Iam-2squared/ark-ai/actions/runs/45314873544) **IN_PROGRESS**.
- PR #421 exact child `dadcd542bbcff6188e50b5f61f09a3ff6c1438de`: [CI 45309777957](https://github.com/Iam-2squared/ark-ai/actions/runs/45309777957) **GREEN, 6/6**; integrated into PR #8 branch only.
- PR #8 predecessor code head `ec91026bae7ae12b7fad924cc2971c5c8c74f351`: [CI 45307332508](https://github.com/Iam-2squared/ark-ai/actions/runs/45307332508) **GREEN, 6/6** before PR #421 integration.
- PR #422 `df26a5ffe02d65d629b8626119cdbf8fc99b8525`: [CI 45309461059](https://github.com/Iam-2squared/ark-ai/actions/runs/45309461059) **GREEN, 6/6** on its older parent.
- PR #423 `935bc8d85fd826bd138c1b4ec17c8f14b9a664e2`: [CI 45309506362](https://github.com/Iam-2squared/ark-ai/actions/runs/45309506362) **GREEN, 6/6** on its older parent.
- PR #5 `ce7a3498472ef1fbcfc36496817bf3c10f6d18f2`: [CI 45300897438](https://github.com/Iam-2squared/ark-ai/actions/runs/45300897438) **FAIL**; all six matrix jobs fail at `ruff check .`. The existing main-branch import-order correction remains approval-gated through Draft PR #276; no bypass or main write was attempted.
- Main `9767fef35eef2115138b5714ebf672dc825636c9`: [CI 45300269200](https://github.com/Iam-2squared/ark-ai/actions/runs/45300269200) **FAIL** at the existing Ruff gate. Main history was not rewritten.
- No local pytest/Ruff PASS, physical Windows/model test, paid compute, real backend dispatch, trusted-clock proof, fsync/power-loss proof, independent custody, authenticated consent/provenance, cross-store atomicity or external exactly-once result is claimed.
- A fresh exact-head CI run is required for the documentation-updated PR #8 checkpoint head; no result is inferred from the preceding code-head run.

## Frozen evidence / boundaries unchanged

- V1/V2/Local UI/Launcher evidence; Memory v1 DDL/public API; PlanStep/ToolCall v1; Observation Envelope v1; ActionAudit v1 DDL/public fields; frozen PermissionGate/ToolCall contracts; V3 Contract 1; and all protected evaluation boundaries remain unchanged.
- PR #5 and PR #8 remain OPEN/DRAFT/UNMERGED. PR #9 remains OPEN/DRAFT/UNMERGED and untouched. No UI/frontend source, tests or integration work was performed.
- No protected V2 evaluation opening, Candidate adapter/weight generation or promotion, paid/external compute, credential/account connection, physical hardware action, external ToolBackend dispatch, destructive operation, frozen-contract change, main merge or GitHub safeguard bypass occurred.
- No contamination, provenance, privacy, regression or reproducibility gate was weakened.

## Blockers / authorization boundaries

- PR #8 exact-head CI [45314486627](https://github.com/Iam-2squared/ark-ai/actions/runs/45314486627) was IN_PROGRESS on the code head before this checkpoint write. Re-read the live branch tip and require fresh exact-head GREEN before integrating another child.
- PR #424 and #425 remain isolated Draft children until their exact-head CI is GREEN. Integrate at most one child after the current parent exact-head CI is GREEN, then revalidate the parent before another integration.
- PR #422 is based on the pre-PR-421 parent and touches proactive recovery tests affected by the proactive source hardening; rebase it onto the new parent and require fresh exact-head CI before integration. PR #423 is test-only ToolRegistry coverage on the old parent; it may be considered after parent CI is GREEN, followed by parent revalidation.
- PR #5 remains Draft/unmerged. Its Ruff failure is blocked on the existing approval-gated main fix PR #276. Do not merge #276 or write to main without explicit approval.
- No paid/external compute, Candidate adapter/weights/promotion, protected V2 evaluation, credentials/new account connection, physical hardware, destructive action, frozen-contract change or UI resumption is authorized.

## Next plan / 今後の方針

1. Re-read the live PR #8 head and CI. After fresh exact-head GREEN, integrate one exact-head-GREEN child at a time; prioritize ToolRegistry PR #423 if it remains mergeable, then rerun parent CI.
2. Rebase proactive process-exit PR #422 onto the new parent because PR #421 changed proactive identity validation; rerun exact-head CI before considering integration.
3. Resolve PR #424 Planner terminal hard-exit and PR #425 Memory post-COMMIT hard-exit CI. Repair only semantics-preserving failures; do not infer PASS from in-progress runs.
4. Continue non-UI Memory CAS/expiry/coherent snapshots, Planner terminal/crash recovery, ToolRegistry/PermissionGate, durable authorization and audit-before-action, disconnected/mock execution, Personal Context privacy, proactive scheduler, Observation fixtures, startup readiness and free-only V3 guard hardening.
5. Keep PR #5/#8 Draft/unmerged, PR #9 untouched, UI/frontend paused, main read-only, and all paid/credential/hardware/destructive/frozen-contract gates closed.

**ARK/JARVIS remains NOT_PASSED.**

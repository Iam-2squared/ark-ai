# LATEST — ARK AI canonical current checkpoint

**Saved at:** 2026-11-24 11:51:54 JST (Asia/Tokyo)
**Canonical status authority:** `docs/PROJECT_STATUS_CURRENT.md`.
**Legacy archive:** `docs/PROJECT_STATUS.md` is preserved unchanged (1,057,799 bytes). It exceeds the normal GitHub Contents API update limit; this small file is the authoritative current checkpoint. No historical content was truncated or rewritten.
**Branch / PR:** `research/jarvis-foundations` / Draft PR #8 (OPEN/DRAFT/UNMERGED; base `main`).
**Work-basis HEAD:** `c0d022b11a5bdccedf458e0266b0aea8ae8541fc` — PR #8 head and branch tip re-read immediately before this checkpoint update.
**Checkpoint-result HEAD:** the normal GitHub Contents API commit returned by this update and verified against the live branch tip immediately afterward; intentionally not self-embedded.
**main HEAD:** `9767fef35eef2115138b5714ebf672dc825636c9` (read-only).
**V3 branch / PR #5:** `research/v3-learning-evaluation` at `ce7a3498472ef1fbcfc36496817bf3c10f6d18f2` (OPEN/DRAFT/UNMERGED).

## Current ARK state

- ARK/JARVIS remains **NOT_PASSED**. No later-version PASS, trusted-clock certification, authenticated consent, production dispatch, physical hardware readiness, power-loss guarantee, independent custody, or exactly-once external-effect claim is made.
- PR #8 remains the isolated JARVIS/core foundation. PR #421 was integrated into PR #8's branch only; its resulting code head was `883006bfdfbd9c9d0408b78d350b767e451d7955`. No main merge occurred.
- PR #5 remains gated Draft/unmerged. Protected V2 final evaluation remains closed; no Candidate adapter/weight generation or promotion was opened.
- PR #9 remains OPEN/DRAFT/UNMERGED at `3b49048dd70eebcb6268299b9ecef4e301bbc0fd` and untouched. All new UI/frontend work, UI integration, polish and frontend tests remain paused.
- V1/V2/Local UI/Launcher frozen evidence and all frozen contracts remain unchanged.
- No paid/external compute, credentials, new account connection, physical-PC action, external backend dispatch or destructive data operation was performed.

## NEW work this invocation

1. **Unicode privacy/identity hardening integrated into PR #8 — PR #421.**
   - Child branch `research/run1238-unicode-privacy-identity-rebase`, exact child HEAD `dadcd542bbcff6188e50b5f61f09a3ff6c1438de`.
   - [CI 45309777957](https://github.com/Iam-2squared/ark-ai/actions/runs/45309777957) **GREEN, 6/6** Windows/Linux × Python 3.11–3.13.
   - Normal squash merge into PR #8 only. Added Unicode General Category Cf rejection and pinned classifier checks across Personal Context identity, disconnected Observation fixture metadata and proactive-state identity; Japanese metadata remains accepted. No frozen contract or main branch changed.

2. **Production Planner terminal hard-exit regression — Draft PR #424.**
   - Branch `research/run1241-planner-terminal-hard-exit`, exact HEAD `762395a8aa8c2b142121d1a46c2d5c36c6f94340`, based on PR #8 code head `883006bfdfbd9c9d0408b78d350b767e451d7955`.
   - Test-only production `PlannerJournal` coverage: spawned process commits root FAILED then exits immediately after native SQLite COMMIT; cold recovery must preserve root FAILED, dependent BLOCKED and independent PENDING with exact revisions/event prefix. No backend call or replay/dispatch authority.

3. **Production Memory post-COMMIT hard-exit regression — Draft PR #425.**
   - Branch `research/run1242-memory-put-native-commit-hard-exit`, latest exact HEAD `f27ee6a22bae4f88f2eda308cb813bf324bcf057`, based on PR #8 code head `883006bfdfbd9c9d0408b78d350b767e451d7955`.
   - Test-only production `SQLiteMemoryStore.put` coverage: spawned process updates a synthetic private row/event and exits after native context-manager COMMIT before Python cleanup/record return; cold reopen checks revision 2 and exactly one create/update event.
   - CI initially failed twice on Ruff I001 in the new test import block (runs 45314873544 and 45315189735). The import block was corrected using the repository's established standard-library / pytest / first-party grouping and an explicit `Path` annotation. Latest run is tracked below; no PASS is claimed yet.

4. **Read-only boundary and child-PR review.**
   - PR #422 proactive process-exit test and PR #423 ToolRegistry deletion-seal test have green child CI on their older PR #8 base. They remain unintegrated pending the new parent exact-head GREEN.
   - PR #5 remains blocked at its existing Ruff merge-ref gate; no main write, main merge or protected evaluation opening was attempted.

## Tests / CI / evidence — exact heads only

- PR #8 code head `883006bfdfbd9c9d0408b78d350b767e451d7955`: [CI 45314486627](https://github.com/Iam-2squared/ark-ai/actions/runs/45314486627) **IN_PROGRESS** at checkpoint preparation.
- PR #8 documentation checkpoint head `c0d022b11a5bdccedf458e0266b0aea8ae8541fc`: [CI 45315092091](https://github.com/Iam-2squared/ark-ai/actions/runs/45315092091) **IN_PROGRESS**. The code-head run does not certify this newer docs head.
- PR #424 `762395a8aa8c2b142121d1a46c2d5c36c6f94340`: [CI 45314707305](https://github.com/Iam-2squared/ark-ai/actions/runs/45314707305) **IN_PROGRESS**.
- PR #425 prior heads: [CI 45314873544](https://github.com/Iam-2squared/ark-ai/actions/runs/45314873544) and [CI 45315189735](https://github.com/Iam-2squared/ark-ai/actions/runs/45315189735) **FAIL**, Ruff I001 only in the new test import block. Latest corrected head `f27ee6a22bae4f88f2eda308cb813bf324bcf057`: [CI 45315356380](https://github.com/Iam-2squared/ark-ai/actions/runs/45315356380) **IN_PROGRESS**.
- PR #421 exact child `dadcd542bbcff6188e50b5f61f09a3ff6c1438de`: [CI 45309777957](https://github.com/Iam-2squared/ark-ai/actions/runs/45309777957) **GREEN, 6/6**; merged into PR #8 branch only.
- PR #8 predecessor code head `ec91026bae7ae12b7fad924cc2971c5c8c74f351`: [CI 45307332508](https://github.com/Iam-2squared/ark-ai/actions/runs/45307332508) **GREEN, 6/6** before PR #421 integration.
- PR #422 `df26a5ffe02d65d629b8626119cdbf8fc99b8525`: [CI 45309461059](https://github.com/Iam-2squared/ark-ai/actions/runs/45309461059) **GREEN, 6/6** on older parent.
- PR #423 `935bc8d85fd826bd138c1b4ec17c8f14b9a664e2`: [CI 45309506362](https://github.com/Iam-2squared/ark-ai/actions/runs/45309506362) **GREEN, 6/6** on older parent.
- PR #5 `ce7a3498472ef1fbcfc36496817bf3c10f6d18f2`: [CI 45300897438](https://github.com/Iam-2squared/ark-ai/actions/runs/45300897438) **FAIL**; all six matrix jobs fail at `ruff check .`. The existing main import-order correction remains approval-gated through Draft PR #276; no bypass or main write was attempted.
- Main `9767fef35eef2115138b5714ebf672dc825636c9`: [CI 45300269200](https://github.com/Iam-2squared/ark-ai/actions/runs/45300269200) **FAIL** at the existing Ruff gate. Main history was not rewritten.
- No local pytest/Ruff PASS, physical Windows/model test, paid compute, real backend dispatch, trusted-clock proof, fsync/power-loss proof, independent custody, authenticated consent/provenance, cross-store atomicity or external exactly-once result is claimed.

## Frozen evidence / boundaries unchanged

V1/V2/Local UI/Launcher evidence; Memory v1 DDL/public API; PlanStep/ToolCall v1; Observation Envelope v1; ActionAudit v1 DDL/public fields; frozen PermissionGate/ToolCall contracts; V3 Contract 1; and all protected evaluation boundaries remain unchanged.

No paid/external compute, Candidate adapter/weights/promotion, protected V2 evaluation opening, credentials/account connection, physical hardware action, external ToolBackend dispatch, destructive operation, frozen-contract change, main merge, UI resumption or GitHub safeguard bypass occurred. No contamination, provenance, privacy, regression or reproducibility gate was weakened.

## Blockers / authorization boundaries

- PR #8 code head CI 45314486627 and checkpoint-doc head CI 45315092091 were IN_PROGRESS; the latter is the current exact PR #8 head. Require fresh exact-head GREEN before another child integration.
- PR #424 and #425 remain isolated Draft children until their exact-head CI is GREEN. Repair only semantics-preserving failures. Integrate at most one child after parent GREEN, then revalidate parent before another.
- PR #422 is based on the pre-PR-421 parent and touches proactive recovery tests affected by the proactive identity change; rebase it onto the new parent and require fresh exact-head CI. PR #423 is test-only ToolRegistry coverage on the older parent; reconcile mergeability after parent GREEN and rerun parent CI after integration.
- PR #5 remains Draft/unmerged. Its Ruff failure is blocked on the existing approval-gated main fix PR #276. Do not merge #276 or write to main without explicit approval.
- No paid/external compute, Candidate adapter/weights/promotion, protected V2 evaluation, credentials/new account connection, physical hardware, destructive action, frozen-contract change or UI resumption is authorized.

## Next plan / 今後の方針

1. Re-read PR #8's live head and CI. After exact-head GREEN, integrate one child at a time; consider ToolRegistry PR #423 first if mergeable, then rerun parent CI.
2. Rebase proactive PR #422 onto the new parent because PR #421 changed proactive identity validation; rerun exact-head CI before considering integration.
3. Resolve PR #424 Planner terminal hard-exit and PR #425 Memory native-commit hard-exit CI. The current Memory retry is run 45315356380; do not infer PASS until completed.
4. Continue non-UI Memory CAS/expiry/coherent snapshots, Planner terminal/crash recovery, ToolRegistry/PermissionGate, durable authorization/audit-before-action, disconnected/mock execution, Personal Context privacy, proactive scheduler, Observation fixtures, startup readiness and free-only V3 guard hardening.
5. Keep PR #5/#8 Draft/unmerged, PR #9 untouched, UI/frontend paused, main read-only, and all paid/credential/hardware/destructive/frozen-contract gates closed.

**ARK/JARVIS remains NOT_PASSED.**

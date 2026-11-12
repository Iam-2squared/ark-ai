# ARK AI Run819 — Retained Memory epoch / registry-bound UNKNOWN recovery

## Scope and irreversible boundaries

Strictly **FREE-ONLY**, **NON-UI**, isolated Draft [PR #8](https://github.com/Iam-2squared/ark-ai/pull/8) on `research/jarvis-foundations`. Initial work basis: `04b3c308d86126c98ecb28f5c6bb43fc4c2f6ee3`. This is **not** a production dispatch, trusted clock, external identity, owner consent, transaction across stores, or human approval. No Candidate, V2 final-evaluation opening, real GPU/paid API, deletion, credential connection, UI code, or main merge. Frozen V1/V2/Local UI/Launcher evidence untouched; PR #5 Draft and paused UI PR #9 remain separately gated.

## Package A — Memory retained nested expiry carriers

- `src/ark/memory/coherent_expiry_restart_bridge.py`, source commit `4c493e678b9f00cae83c3c530d8c610546ce4eeb`.
- `tests/test_coherent_expiry_retained_epoch_run819.py`, test commit `9e13083a42fa9ce587171676c75a5139825c02af`.
- The existing restart reviewer checked the retained outer tuple identity, but not mutable-by-reflection page fields or cohort fields after a separately opened SQLite callback. The source now pins each retained page's six metadata fields and its cohort's five fields across the live coherent read and detached comparison. A reentrant local SQLite open callback that changes prior count, hash, truncation, scope inventory, or caller-clock carrier must be rejected before publishing a mixed-epoch diagnostic.
- **9 new tests** (one stable baseline, eight injected persistent late mutations); no plaintext is placed in the returned receipt. No automatic Memory purge or grant of historical authenticity. **Residual:** input scope inventory and old receipt are supplied by caller; neither trusted time nor durable independent custody follows from a locally recomputed hash. A fresh SQLite epoch may immediately become stale.

## Package B — Registry-bound COMMIT-UNKNOWN and WAL manual quarantine

- `tests/test_registered_unknown_wal_recovery_run819.py`, commit `35c62ea6bcffaceeaeecc2b7cde892e6ca59b7ef`.
- Added **9** tests across the local `UNCHANGED`, `LOCALLY_RECORDED`, `PREEXISTING`, and `ADVANCED_OTHER` classifications, a colliding occurrence under a different bound request, three reentrant registry/call/retained-witness mutations during SQLite open, and a preinstalled forged authority descriptor.
- The backend fixture `NeverExecute` must stay uncalled. Even a locally present audited intent cannot attest an external action or authorize exactly-once replay; all decisions require manual review.
- Initial agency [CI #43221113204](https://github.com/Iam-2squared/ark-ai/actions/runs/43221113204) observed FAIL on Ubuntu Python 3.11 and 3.12: the new revision-drift injection triggered a raw `ValueError: registry revision carrier changed`, rather than the composite `RegisteredUnknownOutcomeRejected`. The lower-layer refusal was safe, but its error taxonomy leaked through the composite.
- Minimal semantics-preserving fix in `src/ark/agency/disconnected_registered_unknown_bridge.py` commit `117c204437c7da222b45431032c9aecfab39a0b4`: preserve and rethrow the composite rejection; normalize underlying `ValueError`/`TypeError` arising during a reentrant registry epoch check to `RegisteredUnknownOutcomeRejected`. No approval predicate, WRITE classification, audit chain or replay prohibition changed. Replacement CI [#43221643895](https://github.com/Iam-2squared/ark-ai/actions/runs/43221643895) was IN PROGRESS at report preparation; its final six-job result MUST be independently verified before a GREEN claim.

## CI / evidence, at report preparation

- Initial Run818 checkpoint HEAD `04b3c308d86126c98ecb28f5c6bb43fc4c2f6ee3`: [CI #43217156318](https://github.com/Iam-2squared/ark-ai/actions/runs/43217156318) **GREEN 6/6**, each Windows/Ubuntu × Python 3.11–3.13 job independently read in this invocation. This is *pre-Run819* evidence.
- Memory new-tests HEAD `9e13083a42fa9ce587171676c75a5139825c02af`: [CI #43220847949](https://github.com/Iam-2squared/ark-ai/actions/runs/43220847949) Ubuntu 3/3 GREEN, Windows 3 IN PROGRESS at the last verification. It is not a 6/6 PASS.
- Initial agency new-tests HEAD `35c62ea6bcffaceeaeecc2b7cde892e6ca59b7ef`: [#43221113204](https://github.com/Iam-2squared/ark-ai/actions/runs/43221113204) observed FAIL (unexpected raw exception; traced to actual pytest logs).
- Agency corrective HEAD `117c204437c7da222b45431032c9aecfab39a0b4`: [#43221643895](https://github.com/Iam-2squared/ark-ai/actions/runs/43221643895) IN PROGRESS. Do not call this head GREEN or imply a physical Windows GGUF run.
- No local full checkout, local pytest, or Ruff claimed. GitHub Contents API creates commits and ordinary PR-triggered CI. No duplicate workflow runs manually triggered.

## Next plan / integration decision

1. Confirm pending six-job exact-head CI outcomes; inspect actual fail logs, apply minimal safe corrections, and immediately use another independent lane while new CI runs.
2. Extend malformed-reflected-retained-envelope preflight so no hostile non-tuple page iterator executes before in-depth Memory validation, preserving the same no-purge fence.
3. Couple Planner UNKNOWN inventory, immutable Registry/PermissionGate and audit-before-action only through an explicitly disconnected mock/read-only gate until lower layers are exact-head GREEN. Never automatically replay an unknown WRITE.
4. Continue privacy-safe Personal Context, proactive scheduler, Observation fixtures, CAS/ABA/COMMIT-UNKNOWN reconciliation and V3 zero-spend guards in separate reversible lanes.
5. Preserve Draft/unmerged PR #5/#8/#9, frozen contracts/evidence and user-gated payment, hardware, privacy and main-merge operations. **Overall JARVIS NOT_PASSED.**

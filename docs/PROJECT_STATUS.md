# ARK AI Project Status

**LATEST**

Saved at: **2026-10-05 09:51:45 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / Draft PR #8

Work-basis HEAD: `161b785409c5332baa737b7de0bcaa9a60da9415`

Checkpoint-result HEAD: this file cannot contain the SHA of the commit that writes itself; use the commit produced by this checkpoint update.

## Current state

V1/V2/Local UI/Launcher evidence is frozen and unchanged. PR #5 remains Draft/unmerged under its frozen V3 Contract. JARVIS foundation work remains isolated/reversible and is not a roadmap PASS.

PR #8 is open, Draft, mergeable, **105 commits ahead / 0 behind** `main`.

## New work this session

- Commit `4e1317f94300ef1b502b27af98a0484fc0380dfa` saved the first Observation exact-ingress pass.
- CI #250 / run `37248448009` failed at Ruff E501 only.
- Commit `161b785409c5332baa737b7de0bcaa9a60da9415` completed the intended exact Observation ingress and fixed the lint formatting.
- Observation blob is now `f5aa17bad87a74c40f20d6151ccf4d5c1a2c4111`.
- CI #251 / run `37248842546` completed **SUCCESS, 6/6 GREEN**.
- Follow-on source/test writes for Observation adapters/regressions, PermissionGate, and several PR #5 hardening lanes were rejected by the normal repository write path and remain source-ready only.
- New focused local checks this session: **26/26 PASS** across Observation remediation, V3 export-plan hardening, training-CLI local-evidence hardening, HF/LoRA local-input hardening, and dataset exact-type hardening.

## Tests / CI / evidence

CI #251 GREEN jobs:
- Windows 3.12 `111572101212`
- Windows 3.11 `111572101329`
- Ubuntu 3.12 `111572101369`
- Ubuntu 3.13 `111572101384`
- Windows 3.13 `111572101432`
- Ubuntu 3.11 `111572101439`

PR #5 remains at `d6d4c1954a85fc716b1c593ac55c85417912418f` with prior CI #151 / run `36223644908` **SUCCESS, 6/6 GREEN**.

Local source-ready evidence is not repository evidence until its source/tests are saved and exact-head CI is GREEN.

## Frozen boundaries unchanged

No paid/external compute, real training, Candidate adapter/weight generation, protected V2 opening, Candidate promotion, new credentials/account connection, live capture, destructive action, unavailable physical-PC action, or main merge occurred.

## Blockers / authorization boundaries

The normal repository write path is intermittent. Continue using only the permitted Contents path after exact HEAD/blob re-read.

PR #5 still requires explicit authorization before any external compute, real Candidate generation, protected V2 opening, or promotion.

Populated Action Audit v1 -> occurrence-bound v2 migration and populated Memory v1 -> independently anchored event-log v2 migration remain blocked until reviewed historical mapping policies exist.

## Next plan / 今後の方針

1. Save dedicated Observation exact-type regressions, take exact-head GREEN, then save fixture-only adapters/tests.
2. Land Planner Recovery Run54.
3. Land Memory exact contracts -> integrity validator -> hardened store -> coherent snapshot -> Personal Context.
4. Land ToolRegistry -> exact PermissionGate -> durable authorization -> occurrence/audit/mock executor.
5. Land Startup Readiness -> proactive scheduler/notifications.
6. Continue PR #5 free-only closure: snapshot/validation/dataset/identity -> approval consumption -> materialization -> CandidateRegistry -> runtime/context -> attempt finalization -> run-manifest/receipt -> export/CLI/HF evidence hardening.

# V3 Run1078 — restore local Personal Context fixture dependencies

## Exact basis

- Target: gated Draft PR #5, `research/v3-learning-evaluation`.
- Exact parent HEAD: `2ddc32a69dd32541497373ac76be2c1db332f88f`.
- Child branch: `research/run1078-v3-personal-context-fixture-dependency`.
- Foundation source snapshot: `research/jarvis-foundations` at `663112db8eed74148daedc6dd78e217302c82b15`.
- Mainbase compatibility source: PR #193 child `research/run1065-v3-mainbase-ruff-compat`, exact HEAD `b8c065d8d59847f7563302f284439afbf3dcd015`.

## Finding

PR #193's branch-local copy of the inherited-main process-crash regression imports three fixture-only modules that are absent from the older V3 branch: `personal_context_offline_preview`, `personal_context_request_binding`, and `personal_context_replay_ledger`. Its exact-head run `44909562565` failed during pytest collection with `ModuleNotFoundError: ark.personal_context_offline_preview`; Ruff completed successfully.

## Change

- Copy the three dependency-free, standard-library-only fixture modules from the exact foundation source snapshot.
- Add their matching local regression suites for offline preview, request binding, and replay-ledger integrity.
- Retain the process-exit-after-native-COMMIT test from PR #193, including its import-group compatibility correction.

The preview remains explicit-fixture-only; request binding and replay remain hash-only and denial-only. No live Memory database, live personal data, disclosure, consent, scheduler dispatch, ToolBackend, or external effect is added.

## Evidence and limits

The failed PR #193 run is historical evidence only. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required for this combined child; no local pytest/Ruff PASS is claimed. This is a reversible V3-branch test/dependency compatibility package, not a main-branch write or merge.

No frozen V3 Contract 1 change, Candidate adapter/weight generation, training, paid/external compute, protected V2 evaluation, promotion, credentials, UI, or main merge is involved. PR #5 remains Draft/unmerged; V3 remains NOT_PASSED.

# Run732 — disconnected READ / privacy preaccess hardening and actual CI repair

Saved at: **2026-11-09T15:55:57.093+09:00 Asia/Tokyo/JST** (administrative time, not trusted action clock). All work is FREE-ONLY, NON-UI, synthetic/offline and reversible. Draft PR #8 `research/jarvis-foundations` only; no main merge.

## Exact evidence and work basis

- Initial exact work-basis/checkpoint HEAD: `13a6c3d4064d9057718eaff187a05afe0598b2e8` (Run731).
- Final implementation + test/CI-correction HEAD when this report was authored: `ce5362150dd2913836353ebdc8c37ae3f7af8382`. Technical-report commit will be a distinct later HEAD; canonical status will be written ONCE after re-reading latest branch.
- Prior Run731 final-checkpoint [CI #42573050253](https://github.com/Iam-2squared/ark-ai/actions/runs/42573050253) is **NOT GREEN**. Actual Ubuntu 3.11 log: **11,594 pass, 6 fail, 1 skip**, six legacy selector tests still expecting late forged getter execution/error strings instead of earlier denial. Last inspected job states: test (windows-latest, 3.11) completed/failure; test (windows-latest, 3.13) completed/failure; test (ubuntu-latest, 3.11) completed/failure; test (ubuntu-latest, 3.12) completed/failure; test (windows-latest, 3.12) completed/failure; test (ubuntu-latest, 3.13) completed/failure. These are evidence for that old HEAD only.
- Current new-source/test commit [`ce5362150dd2`](https://github.com/Iam-2squared/ark-ai/commit/ce5362150dd2913836353ebdc8c37ae3f7af8382) CI: [#42575855002](https://github.com/Iam-2squared/ark-ai/actions/runs/42575855002) was **QUEUED** at inspection; no exact-current-source 6/6 PASS claim. GitHub can queue intermediate automatic PR runs; none was manually rerun.

## A — READ-only Planner/Registry/PermissionGate preflight

- Source: `src/ark/agency/disconnected_read_preflight.py`. Import-time identities now fence SHA-256, JSON serialization, digest domain and bound size/time policy BEFORE private plan/grant reads and again across callbacks. The original domain bytes `ARK-disconnected-registered-read-preflight-v1\\0` and output shape are **preserved** (a transient erroneous source literal was corrected normally before new regression tests were saved).
- Inert receipt validation now pins all 7 field slot descriptors and 3 lookup/constructor hooks, as well as the existing False-only authority descriptors. Replaced class getters may not access a private fingerprint before rejection.
- New [22 parameter-expanded tests](https://github.com/Iam-2squared/ark-ai/blob/ce5362150dd2913836353ebdc8c37ae3f7af8382/tests/test_registered_read_preflight_digest_report_fence_run732.py): 8 codec/budget/domain, 10 fields/hooks, 3 late registry-bind substitutions, 1 honest READ-only/no-dispatch control. No backend dispatch, no external auth, no real clock.

## B — local Personal Context request privacy

- Source: `src/ark/personal_context_request_binding.py`. Detects substituted SHA, JSON loads/dumps, regex compiler and compiled parsers, domain-byte carriers before reading a private offline preview. Rechecks across JSON decode, serialization and hash boundaries. No change to canonical valid binding digest or retention/consent semantics.
- New [13 parameter-expanded tests](https://github.com/Iam-2squared/ark-ai/blob/ce5362150dd2913836353ebdc8c37ae3f7af8382/tests/test_context_binding_private_codec_preaccess_run732.py): 12 preinstalled hostile codec/regex/domain cases demanding zero intercepted private data, plus 1 deterministic denial-only output.
- Updated inherited JSON parse tests `test_personal_context_request_binding_run480.py` (1) and `test_personal_context_binding_slot_preaccess_run649.py` (2) to require **zero replaced-parser calls**, not late mutated-preview diagnostics. Production checks were not relaxed.

## C — Run731 CI failure repair

- Legacy `test_synthetic_lane_selection_authority_run498.py` had 6 actual failures on the Run731 old HEAD. Fixed expected **early** `work lane parser, codec or denial authority changed` outcome, preserved fail-closed source behavior, and asserted hostile getters are never invoked. No selector production changes in this package.
- This is *repair authored*, **not** verified multi-platform GREEN until an exact-head workflow completes.

## Explicitly unchanged and blocked

- No PR #5 V3 protected gate/Contract 1 edits, no protected V2 final evaluation or candidate adapters/weights, no PR #9 UI/frontend work, no V1/V2/Local UI/Launcher frozen evidence change, no paid/external compute/API, no credentials/new connection, no real ToolBackend dispatch, no destructive or irreversible repair, no main merge.
- Hash/codec identity checks and synthetic fixture digests are NOT authenticated identity/consent/provenance, trustworthy wall-clock evidence, actual exactly-once side-effect evidence or sandbox guarantees. ARK/JARVIS/V3 remain **NOT_PASSED**.

## Next plan / 今後の方針

1. Inspect actual exact-head six-matrix CI; fix remaining cases narrowly based on real logs without weakening early refusal.
2. Memory CAS/ABA, row/event coherence, expiry and manual-only COMMIT-UNKNOWN review; independent retained witnesses remain required.
3. Planner READ journal/manifest crash-safe custody and terminal recovery/unknown quarantine.
4. Connect registry-bound exact-type gate to occurrence/audit-before-action and disconnected mock ONLY after exact-head lower-layer evidence; do not dispatch external WRITE.
5. Continue isolated privacy/proactive/observation/V3 free-only guard work, keeping Draft #5/#9 and frozen contracts unchanged.

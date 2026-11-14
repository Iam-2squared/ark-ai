# Run598 — Non-UI permission entry, Personal Context recovery, Memory manual triage

**Scope:** Draft PR #8 `research/jarvis-foundations`, starting from the previously confirmed Run597 checkpoint `4e741dd6efb2313ee8f086e2228412a100a49141`. This is an implementation/provenance note, **not** a PASS attestation or a new normative contract.

## A. Disconnected plan READ permission entry

- Source: `src/ark/agency/disconnected_read_preflight.py`, commit `c8463ce0fd8cfb7671ad2e0d460bb39e2ebdb447`.
- New regression: `tests/test_read_preflight_original_gate_before_call_run598.py`, commit `cd46ccfd43a9108840352e4169e245730cfbbb32`, **5 authored parameter-expanded cases**.
- Previously `preview_registered_read_plan` checked the original registry-bound `PermissionGate.authorize_registered` only **after** invoking it. A class- or instance-level forged implementation could run before the denial, despite returning a value-equal `BoundAction`. The preflight now checks the import-time method at entry, across stable-plan/registry callback epochs and immediately before invocation.
- Tests explicitly count counterfeit gate calls (expected **zero**) for preinstalled and registry-bind callback substitutions; the ordinary result remains inert. This is process-local code-drift detection, **not** independent code identity or durable authorization.

## B. Personal Context restart/replay recovery authority

- Source: `src/ark/personal_context_replay_recovery.py`, commit `ba013177a3f95e6bada760fe9a336e9bcae5f4fc`.
- Regression: `tests/test_context_recovery_original_denials_run598.py`, commit `770e132e1940a3ca5de52fbb12ea5b2e25dcab20`, **10 authored cases**.
- The report's seven False-only authority descriptors are now pinned against preinstalled and callback-installed replacements, even replacements still returning False. The retained replay witness's `independent_custody_proven` descriptor is also checked before its first getter. A local SQLite hash chain remains neither external consent nor independent custody.
- No real context data, consent source, export, notification, or ToolBackend is connected.

## C. Memory uncertain-COMMIT manual witness

- Source: `src/ark/memory/postcommit_uncertainty_review.py`, implementation `5edfa6d2e7ec516082dd930c4bd6de85d8a4cedf`, import-order follow-up `c6b1becd15a37becbb1e1c8b81207054d4e04a57`.
- Regression: `tests/test_memory_triage_token_original_authority_run598.py`, commit `ba84c0ea31d4b3f9da6a1f9dd281106d958d5cdc`, **7 authored cases**.
- Read-only COMMIT ambiguity triage now pins the originally defined token denial properties before consulting any retained token, rechecks their identity and false-only return after each relevant callback, and refuses reflected substitution even if a replacement getter returns False.
- `LOCAL_UNCHANGED` does **not** prove rollback or authorize retry. `ONE_MATCHING_UPDATE_VISIBLE` does **not** attribute the writer or prove exactly-once effects. `INDETERMINATE` requires manual review. No automatic write/replay is added.

## CI/evidence bounds and independent integration audit

The preceding exact Run597 HEAD `4e741dd6efb2313ee8f086e2228412a100a49141` is **six-job GREEN** on GitHub Actions [run #41769697611](https://github.com/Iam-2squared/ark-ai/actions/runs/41769697611): Ubuntu/Windows Python 3.11/3.12/3.13. This evidence predates Run598 changes and cannot certify them. Newly triggered source/test workflows must be checked by their exact commit SHA; **22 authored cases are definitions, not independently verified PASS counts**. No external GPU, paid service, hardware, live backend, or protected evaluation has run.

**Read-only dependency audit:** `src/ark/agency/disconnected_read_cycle.py` separately calls `gate.authorize_registered` during its independent READ-wave rebind, after a preflight callback. Its direct gate method boundary needs its own import-time identity and pre-invocation check. Do **not** connect that path or treat the upstream repair as covering downstream code. Advance that change only after prerequisite exact-head GREEN, then test callback-driven class/instance gate replacement without any backend call.

**Existing controls unchanged:** frozen Memory/Planner/V1/V2/Local UI/Launcher contracts and evaluation gates; Draft/unmerged PR #5 (V3 protected evaluation) and PR #9 (UI paused); no main merge, Candidate generation/promotion, credentials, authenticated consent, trusted clock, or real execution claims.

## Next plan / 今後の方針

1. Check newest exact HEAD Actions six-job results. Repair only observed failures through the normal Contents API; do not weaken refusals or duplicate workflow launches.
2. After lower-level GREEN, harden downstream disconnected READ cycle's independent permission call boundary and add no-dispatch tests.
3. Expand bounded Memory COMMIT-UNKNOWN evidence/restart cases and Planner FAILED/BLOCKED/RUNNING persistence fixtures, with no blind retry.
4. Build disabled-by-default audit-before-mock-action/occurrence integration only with prerequisite GREEN and a separate approved trusted-identity/clock/consent design. Keep V3 free-only checks isolated and UI untouched.

# Run468 — Disconnected READ preflight, privacy/observation result custody

Status: **SOURCE/TEST SAVED; NEW EXACT-HEAD CI PENDING**. Local-first, no-dispatch,
no-real-user-data engineering evidence; **not** release authorization or complete JARVIS.

## Exact work basis and CI

Initial PR #8 HEAD: 2dddc4cd95ae9e8d198d3d6e08963d61ce716d7e.
The unchanged Run467 checkpoint CI #1467, run 40984181901, completed **SUCCESS
on all SIX** Ubuntu/Windows Python 3.11–3.13 matrix jobs (Ruff, pytest, UI,
smoke, CLI). Ubuntu 3.11 log showed **4497 passed, 1 skipped**. That is baseline
evidence only. New source/test HEAD, before this document:
152312d42d923d9dc9633d63c06aa4d87895ac7c.
Exact-head CI #1476 / run 40988304821 was **QUEUED** at inspection; no
duplicate manual run, cancellation, or paid compute. The isolated development
container had no complete ARK checkout due GitHub DNS failure, so new pytest
cases are committed but **not claimed locally PASS**.

## Package A: diagnostic registered READ-only Planner preflight

Created:
- src/ark/agency/disconnected_read_preflight.py; Git blob e163e4e57727d6e3a27560effef6dbd2a07924e4
- tests/test_disconnected_read_preflight_run468.py; blob 6535fa9c161eba70773d39e8ccc6884942986b52

The opt-in preview_registered_read_plan integrates the existing PlanGraph,
ToolRegistry and PermissionGate *only* as a bounded, disconnected diagnostic.
It accepts at most 24 graph steps and 128 exact capability grants, checks
topology/status/registry and original grant carriers against reentrancy,
binds all steps and refuses any registered WRITE (even a not-ready descendant),
and grant-checks only ready READ steps. It never invokes ToolBackend.execute
or any OS/network service. The output is only content-free digests and
ready step/binding IDs with all permission-to-dispatch, replay, external
outcome, authenticated-clock and consent claims explicitly false.

The clock is caller-supplied and unauthenticated. No real executor, durable
permission token, scheduler, consent verifier or external exactly-once effect
is implemented.

## Package B: privacy and Personal Context detached-result type custody

Strengthened existing deny-only fixture modules to pin the original DTO type
independently of exported constructor symbols; existing field, scope, expiry
and content-integrity checks are not weakened. This rejects a substituted
constructor that mimics expected field values while claiming consent,
disclosure or export authority.

- src/ark/offline_context_redaction.py: 9fe4961828160c531d5d3225eb15283ba7ab5ac3
- src/ark/offline_context_membership_guard.py: c8db51affe0f7ac9346f7f1de6d0d71d74da772b
- src/ark/personal_context_offline_preview.py: 2871156bce50f4f7b9f8f78fe3c1fcda41803f4f
- tests/test_private_preview_result_type_run468.py: fc78d049078b17074a8ce8ca9b9c54d0f53d6573

Fixtures have NO actual personal-data connector or consent/authentication
authority, and return no permission to release, export, erase or dispatch.

## Package C: Observation lineage and cached-reuse constructor custody

Pinned original lineage/reuse DTO classes, including cached, historical and
current witnesses, without modifying existing source/privacy/time/parent
checks. No microphone, camera, screen, ToolBackend, notification or media
processing was accessed.

- src/ark/observation_lineage_review.py: d35dc0e69e92a0311ed7767d56247895f21c76f2
- src/ark/observation_reuse_review.py: cb9ce8b147b326a08ff8415c60e20259f6a0a3e3
- tests/test_observation_result_type_run468.py: 841cd11fb7a38e1a41d8a483be1b35175685f60a

## Provenance, scope, blockers

Nine ordinary Contents source/test commits in three coherent packages;
all nine blob hashes above independently verified against new source/test
HEAD. Tests are written, but latest exact-head six-matrix CI is not yet
GREEN. V1/V2/Local UI/Launcher frozen evidence, Memory v1 schema,
ActionAudit, V3 Contract 1 and protected final evaluation remain unchanged.
PR #5 and PR #8 remain Draft/open/unmerged. No paid/external GPU/API,
real Candidate, training, promotion, protected V2 opening, credentials,
physical PC operation, actual user data, irreversible effect, or main merge.

V3 pre-paid audit reaffirmed unresolved immutable HF revision and base bytes,
120/30 human-approved dataset and contamination decisions, environment
and conversion-tool identities, provider billing evidence, GPU and JPY limits,
and explicit approvals. No facts were invented to close these gates.

## Next independent gates

1. Obtain exact-head #1476 six-environment GREEN or inspect failures and
   correct narrowly without weakening tests or duplicating workflows.
2. Keep the READ preflight non-executable until independently authenticated
   ToolRegistry, consent, trusted clock and audit-before-action exist.
3. Advance Memory CAS/event/expiry/coherent snapshots and Planner durable
   UNKNOWN/WRITE quarantine independently; no automatic replay.
4. Keep PRs Draft and all protected evaluation/payment boundaries unchanged.

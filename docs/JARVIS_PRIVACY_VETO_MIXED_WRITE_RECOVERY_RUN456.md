# ARK Run456 — Offline privacy veto and mixed-plan recovery fencing

**Branch:** `research/jarvis-foundations`, PR #8 remains Draft/open/unmerged.
**Invocation work-basis HEAD:** `729738dd10e87ba177e9de9cad3395ddd27230f8` (Run455 checkpoint).
**Final new source/test HEAD:** `e7119dbaeb8a8f7382b82f94ecbfbcb6e3812f37`.
**Status:** Two independent, disconnected modules; local tests GREEN; GitHub Actions exact-head matrix NOT GREEN/NOT VERIFIED.

## 1. Synthetic privacy veto: persistent denial, never consent

- `src/ark/disconnected_privacy_veto.py` Git blob `6f42302ad0b2e7a85f914d00856c05ac9cb2cc50`.
- `tests/test_disconnected_privacy_veto_run456.py` Git blob `017d1b45efbde02a0391c68b6040a5c0f306033a`.
- Local SQLite fixture stores **only claimed owner/scope SHA-256 values**, monotonically appended local veto markers, and a caller-asserted observation time. It does not read real Memory or grant any user consent, identity, deletion, retention exemption, context reuse, export, or Tool access.
- `BEGIN IMMEDIATE` and expected prior `OfflinePrivacyVetoWitness` provide within-ledger CAS; a stale or concurrent writer is refused. Reopen/duplicate/scope separation, wrong types, reversed local clock, SQLite row/schema changes, missing file and symlink paths are rejected. Read-only `review` never recreates storage.
- Local complete-ledger rollback **cannot** be caught by its own recomputed hash. An *earlier independently retained* witness is required, and supplying a matching witness alone does not authenticate its origin. SQLite does not establish an external trust anchor or user identity. Caller-injected clock is not trusted.
- Presence of a veto is **deny-only**. Absence is **never proof of opt-in**. Even a matching review returns `consent_verified=False`, `user_identity_authenticated=False`, `context_release_authorized=False`. This synthetic table is not authoritative revocation lifecycle for real user data.
- This is a local database-creation fixture; no destructive operation on user-owned files or modification of existing Memory tables was performed. A filesystem race or hardlink substitution is not externally attested: no production provenance/secure-open claim.

## 2. Mixed READ/WRITE recovery triage: zero replay authority

- `src/ark/agency/disconnected_write_recovery_fence.py` Git blob `fad64577b20f78802dac3bdf94308fb996dcf9a9`.
- `tests/test_disconnected_write_recovery_fence_run456.py` Git blob `32970264b64e6c4126bbac3ed57b61e9ba882f57`.
- A pure bounded, topologically ordered, exact-type claim review (maximum 24 steps) classifies PENDING/RUNNING/UNKNOWN/SUCCEEDED/FAILED/CANCELLED/BLOCKED with explicit READ/WRITE effects and optional claimed WRITE reservation identity.
- A reserved PENDING WRITE returns `QUARANTINE_RESERVED_WRITE`; RUNNING/UNKNOWN WRITE returns `QUARANTINE_WRITE_UNKNOWN`; unreserved PENDING WRITE remains `HELD_WRITE_APPROVAL`. Descendant HOLD states propagate. Contradictory success/running dependencies are rejected. Independent PENDING READ can be labeled `READY_MOCK_ONLY`, **not** authorized for actual execution.
- All caller-supplied state/digest/reservation information is unverified. A `COMPLETE_UNVERIFIED` result is not external outcome proof, and the digest is not a signature or trustworthy history. No PlanGraph, actual ToolRegistry, SQLite journal, executor, PC, network, clock or external storage is connected. `dispatch_authorized`, `automatic_replay_authorized`, `write_authorized` and `external_outcome_verified` are always false.

## Evidence and exact HEAD / CI

Python 3.13.5 + pytest 9.0.2 local isolated tests against **the exact bytes saved to GitHub**:
**59 PASSED** (27 privacy-veto + 32 mixed-plan recovery). Local `compileall` PASS;
all new source line widths <=100 characters. Four exact local `git hash-object`
blob SHA values above were re-fetched and matched the saved GitHub files.

Additional independent, **not committed as pytest cases**: 2,000 seeded
topology/recovery determinism, quarantine and no-WRITE-ready oracle cases;
one 64-thread competing-veto CAS probe with exactly one winner. PASS locally.
These do not prove cross-machine or production correctness.

GitHub Actions source/test HEAD #1379, run `40363780665`, was **QUEUED**
when checked (also #1378/#1377/#1376 QUEUED). Historical Run455 checkpoint
#1375, run `40352748781`, still had all six jobs QUEUED. At inspection
**135 queued / 6 in-progress** workflow runs were reported. No manual
reruns, cancellations, paid runners or duplicated workflows were started.
Whole-repo Ruff/pytest, Windows/Ubuntu Python 3.11-3.13 six-cell GREEN,
installed package/UI smoke and this document/checkpoint HEAD CI are
**NOT confirmed**; container cannot resolve github.com to full-clone.

## Frozen gates and next steps

Frozen V1/V2/Local UI/Launcher evidence, Memory V1 Schema, ActionAudit V1,
V3 Contract 1 and evaluation boundaries are unchanged; PR #5 remains
Draft/unmerged. No paid compute/GPU/API, subscriptions, Candidate/adapter/
weight generation, protected V2 final evaluation, promotion, new secrets,
hardware capture, real tool, real user data operations, destructive action
or main merge.

**Next plan / 今後の方針**

1. Inspect naturally progressing Actions by exact source/test HEAD, diagnose
   actual failures and CI runner backlog; never infer all-six GREEN from local
   tests or alter/cancel workflow checks solely to fabricate success.
2. Validate cross-process privacy veto CAS/clock/event boundaries and hardlink/
   filesystem source identity before any possible lifecycle integration;
   independently authenticated opt-out custody and revocation rights are still
   missing. A missing local veto must *never* become consent.
3. Retain mixed-plan WRITE nonreplay quarantine, terminal propagation and
   trusted Registry/PermissionGate/audit prerequisites. No integration until
   lower-layer exact-head GREEN and reviewed approvals/trusted-clock/issuer.
4. Continue independent Memory CAS/expiry/event coherence, Planner multi-WRITE
   recovery and startup readiness. Do not cross frozen/paid/user-approval gates.

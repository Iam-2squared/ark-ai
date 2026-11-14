# ARK AI Run863 — bounded SQLite diagnostics and abrupt Planner recovery (non-UI)

**Observed work window:** 2026-11-14, Asia/Tokyo/JST. **Overall ARK/JARVIS: NOT_PASSED.** All work is free-only, disconnected, local and reversible. This report documents source/test changes, not a PASS gate or authority to execute tools.

## Basis and verified prior evidence

- Initial branch/PR #8 HEAD: `d673d09b09e8d586ce4a3b63f7e83cf5b24a4320`; Draft/open/unmerged.
- Run862 checkpoint HEAD `d673d09b`: [GitHub Actions #43553826606](https://github.com/Iam-2squared/ark-ai/actions/runs/43553826606) **GREEN 6/6** (Windows and Ubuntu, Python 3.11–3.13). This certifies **only** the prior HEAD.
- PR #5 and PR #9 were confirmed Draft/open/unmerged. UI/Frontend development remains fully paused.

## NEW source and regression packages

1. **Memory v1 bounded integrity diagnostics** — source commit `1013df5b2dab57aad9698ac4cee0a080ed72dc3a`. Change only `PRAGMA quick_check` result hydration from `fetchall()` to `fetchmany(2)` before schema comparison. A single `('ok',)` result still admits clean v1 schema; zero, extra, or non-ok rows fail closed. Frozen DDL, user_version checks, schema catalog budgets, migrations, and event semantics are unchanged.
2. **ActionAudit v1 bounded integrity diagnostics** — source commit `d4587af316635b1f0a0b2763afa1392da35bc6b7`. Apply the same two-row read bound while retaining existing exact-v1 DDL and denial on malformed quick-check output. No permissions, grants, timestamps, actions or event replay modified.
3. **Memory/ActionAudit synthetic regression suite** — `4c96ce969247f803077a74ff8347df777a795206`; **8 parametrized cases AUTHORED**. Disposable on-disk canonical schemas and an intercepting synthetic quick-check cursor assert explicit `fetchmany(2)`, forbid `fetchall()`, exercise ordinary `ok`, malformed diagnostic, `ok` plus extra diagnostic and multiple bad diagnostics, and verify the test does not change the stored schema. Ruff line-length follow-up `f9ba6103cd848bc122f38d3362969fdc2048bb68`.
4. **Planner abrupt spawned-process termination** — `6427ca5c2758d10a34b49ab48997bd22472c392d`; **4 parametrized cases AUTHORED**. A disposable spawned interpreter `os._exit(0)` after a committed RUNNING, SUCCEEDED, FAILED or CANCELLED SQLite journal record, without sending the parent a receipt or running Python cleanup. Independent cold recovery asserts event count, terminal/dependent state, persistent ambiguous RUNNING, stale revision rejection, and explicit `dispatch_authorized=False` / `automatic_replay_authorized=False`. This tests local journal restart behavior; it cannot prove a real external tool was executed exactly once. Ruff line-length follow-up `e32a6c79479933fa987622104cdb7fbe342c1669`.
5. **Personal Context private replay bounded integrity diagnostics** — source `9e9381544bb96a8e0944f6f397d50d00d91336b0`, new regression `3f920f9bbccd963382f91c1cce9c677f2adf60fd`; **3 parametrized cases AUTHORED**. Existing SQLite schema-admission and private metadata bounds stay intact; `PRAGMA quick_check` now reads at most two diagnostics and fails closed on extras. Synthetic cursor prevents bulk hydration, with on-disk schema invariance checks; no personal data disclosed or real consent inferred.

**Total: 15 authored regression cases (8 + 4 + 3)**, plus semantics-preserving test formatting corrections. Local Python syntax compilation passed for authored tests before upload. GitHub-read tests subsequently had maximum line lengths 84, 88 and 81 after formatting. Full local pytest/Ruff and physical-machine/GGUF testing **NOT RUN**. The newest source and test CI matrix is **not yet GREEN-certified**; all claimed case counts mean *authored*, not *passed*.

## CI pipeline / evidence at reporting snapshot

- Prior checkpoint `d673d09b`: GREEN **6/6**, #43553826606.
- Memory source `1013df5b`: [#43558011078](https://github.com/Iam-2squared/ark-ai/actions/runs/43558011078) IN PROGRESS when inspected.
- Audit source `d4587af3`: [#43558031068](https://github.com/Iam-2squared/ark-ai/actions/runs/43558031068) IN PROGRESS when inspected.
- First shared regression `4c96ce96`: [#43558106657](https://github.com/Iam-2squared/ark-ai/actions/runs/43558106657) IN PROGRESS when inspected.
- Planner formatting head `e32a6c79`: [#43558244340](https://github.com/Iam-2squared/ark-ai/actions/runs/43558244340) QUEUED when inspected.
- Personal Context test head `3f920f9b`: [#43558354078](https://github.com/Iam-2squared/ark-ai/actions/runs/43558354078) QUEUED when inspected. Do **not** treat partial or earlier-GREEN runs as this commit's result.
- Automatic CI only; no equivalent manual duplicate workflows launched. No paid/external compute.

## Independent read-only continuation audit

The latest branch still exposes `fetchall()` for `PRAGMA quick_check` in independent components: `agency/planner_journal_review.py`, `agency/disconnected_write_slot_ledger.py`, and `agency/disconnected_atomic_preaction_ledger.py`. These are candidate **independent** bounded-read hardening lanes, not changes made by this run. The proactive scheduler already uses `fetchmany(2)`. Review each store's admission order and retained contracts before changing them; avoid invalidating any in-flight source-path CI.

## Safety boundaries and unfinished invariants

V1/V2/Local UI/Launcher frozen schemas and evidence untouched. No UI source/test/PR #9 changes. PR #5 and PR #8 stay Draft/unmerged. No paid API, external GPU, Candidate generation/adapter/weights, promotion, protected evaluation, new credentials, user-specific data access, trusted approval, real ToolBackend execution, irreversible operation, or main merge.

**NOT PROVEN:** WAL/SHM last-client-close versus name/FD custody, pathname-to-open atomicity, independently authenticated Memory COMMIT-UNKNOWN provenance, cross-store atomicity, trusted time or issuer, durable exactly-once approval, safe audit-before-action effect coupling, or exactly-once external tool effects. Quick-check read bounds limit Python error-result hydration; they do not eliminate SQLite's internal work, make corruption diagnostic messages trustworthy, or authenticate database origin.

## Next plan / 今後の方針

1. Determine final exact-head six-job CI; fix any failure minimally while retaining fail-closed behavior and working an independent lane during CI.
2. Extend bounded quick-check diagnostics to disconnected Planner, WRITE Slot Ledger and atomic preaction paths, only with new synthetic tests and exact-head GREEN, without touching frozen contracts.
3. Investigate disposable Memory/ActionAudit WAL/SHM last-close and open-name races; never auto-replay UNKNOWN effects.
4. Continue Planner/manual-only UNKNOWN durable separation, Memory CAS/coherent snapshots, Personal Context privacy expiry/revocation and isolated scheduler/observation fixtures.
5. Integrate ToolRegistry, exact-type PermissionGate, immutable approval occurrence, audit-before-action and disconnected Mock Executor *only* after their lower-level invariant matrices are exact-head GREEN. Real tool authorization stays unavailable.

# Run401 — bounded admission, original privacy-veto scopes, coherent Memory scan budget

> **Offline synthetic foundation only.** This document describes intended
> failure boundaries and fixtures, not real consent, verified external WRITE,
> model capability, erasure evidence, or Candidate training.

## Basis, isolation and scope

Work started from `253417b96d7c6b2344a1b7e6166060db67df2de5`
(PR #8, `research/jarvis-foundations`; Run400 checkpoint). The changes
are reversible in this draft branch. Neither main nor V3 PR #5 is merged.
Frozen V1/V2/Local UI/Launcher evidence, Memory v1 SQL DDL, protected V2
FINAL, V3 Contract 1 and Candidate boundaries remain unchanged.

### Package A — bounded PermissionGate grant iterables

File: `src/ark/agency/policy.py`.
Regression: `tests/test_permission_grant_budget_run401.py` (6 parametrized cases).

**Threat:** a caller-supplied generator that never terminates can keep
registered or unregistered authorization stuck in materialization. No
one-shot token should be consumed in this admission failure, and the
presence of one matching grant early in the stream must not bypass
complete, bounded validation.

**Intended invariant:** admit at most 1,024 exact grant objects; detect
the 1,025th yield and refuse it before any token spend or backend
dispatch. This bound is checked on both direct and registry-authoritative
paths. Existing grant identity, registry rebind and locked token checks
continue to apply. Tests cover READ/WRITE, direct/registered,
`_MAX_GRANTS + 1` failure with preserved reusable WRITE token, and
exact-limit acceptance without invoking an executor. Iteration itself
is still caller-supplied code and cannot be assumed side-effect-free.

### Package B — Personal Context original-veto scope custody

File: `src/ark/personal_context_revocation_review.py`.
Regression: `tests/test_personal_context_veto_scope_epoch_run401.py`
(6 cases).

**Threat:** `assert_not_revoked(scopes)` receives mutable-by-reflection
`MemoryScope` instances built from the Memory request. A reentrant
veto hook can change a scope owner/namespace to an unrevoked decoy;
checking only the original request permits Memory for the originally
revoked owner/namespace to be selected under a different veto.

**Intended invariant:** pin each original veto scope's identity and
owner/namespace immediately upon construction. After each independent
continuity, veto, Memory and selection phase, reject scope drift and
equal-value replacement of the request's namespace tuple. Tests inject
first-veto bypass attempts against a truly revoked fixture, second-veto
drift, same-value namespace-carrier replacement and stable inert output.
No authenticated permission or atomic Memory/veto snapshot results from
these checks.

### Package C — bounded coherent Memory row hydration

File: `src/ark/memory/coherent_snapshot_review.py`.
Regression: `tests/test_memory_snapshot_scan_budget_run401.py`
(5 parametrized cases).

**Threat:** `SELECT * ... fetchall()` materializes unbounded SQLite rows
even when a caller selects only one top-ranked Memory. Query relevance
must consider the selected namespace, but no caller-controlled Memory
database should be allowed to cause unlimited Python hydration.

**Intended invariant:** per-namespace row scan is capped at 10,000
physical candidate rows with `fetchmany(cap + 1)`. The 10,001st row
rejects the *whole* read-only snapshot, not a silently truncated or
mis-ranked privacy-sensitive result. Successful requests within the cap
retain existing ranking, selection, clock and content-free digest
semantics. Tests reduce the cap in fixtures to check overflow,
read-only failure, exact-bound success and independent namespace
budgets. No Memory row, event, schema or expiry mutation is authorized.

## CI and evidence interpretation

The exact source/test/document SHA and six-job Ubuntu/Windows
Python 3.11–3.13 matrix **must be observed independently**. A predecessor
commit's GREEN does not prove a later source/test commit. The canonical
`docs/PROJECT_STATUS.md` records exact job/run conclusions after
observation; it must distinguish CI FAIL from IN PROGRESS and from GREEN.
No meaningful real-world authorization, signed outcome, protected
evaluation or Candidate PASS may be inferred from pytest or Ruff.

## Explicitly unresolved

- No authenticated issuer, external trusted clock, live ToolBackend,
  filesystem inode custody, cross-SQLite atomicity or external exactly-once
  execution proof. `UNKNOWN WRITE` stays UNKNOWN and may not auto-replay.
- A row-count cap bounds Python hydration, not SQLite scanning cost,
  untrusted database file size, time spent inside callbacks or external
  privacy leakage. A single in-process source identity check is not a
  filesystem custody mechanism.
- Veto checks and Memory reads use separate SQLite files; revocation can
  race after the final check. Even a locally coherent projection carries
  **no consent to use it**, call a model, export, notify or dispatch tools.
- The grant bound is a reversible offline policy safeguard, not durable
  restart-safe one-shot authorization. A malicious Python generator can
  still perform side effects during its already-consumed yields.

## Next dependency-aware work

1. Independently verify the exact final source/test HEAD across all six CI
   jobs and correct real regressions without relaxing safety semantics.
2. Compose Planner, immutable Registry, PermissionGate, durable occurrence,
   ActionAudit and disconnected/mock executor under fault injection, with
   `RUNNING/UNKNOWN` recovery permanently non-replayable.
3. Review Memory CAS/revision and expiry transaction boundaries, guard
   Personal Context revocation lifecycle, and investigate OS-file custody.
4. Specify trusted-clock and authenticated approval ports as disconnected
   contracts; keep all physical, financial, privacy and frozen gates closed.

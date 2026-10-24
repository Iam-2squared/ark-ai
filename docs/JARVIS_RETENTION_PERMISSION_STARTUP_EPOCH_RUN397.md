# JARVIS local review evidence: privacy, permission, and startup epochs — Run397

**Scope:** Free-only, isolated synthetic/mock foundations on Draft PR #8
(`research/jarvis-foundations`). The exact work-basis GitHub HEAD was
`c4c9ae0df2258fbb383e65fff292710ee10845b3`, whose PR CI
#791 / run 40109895217 completed GREEN in all six Linux/Windows Python
3.11–3.13 jobs before these changes. Run396 already contained independent
Memory/coherent-snapshot, detached recovery archive, privacy veto, and
proactive retained-witness work at the basis HEAD; those earlier commits
are **not** relabeled as new Run397 work. Canonical PROJECT_STATUS was
still Run395 at this run's start.

## Four compatible implementation and regression packages

| Domain | Production source | Focused synthetic regression | New cases |
| --- | --- | --- | ---: |
| Privacy-retention recheck | `src/ark/personal_context_retention_recheck_review.py` | `tests/test_retention_recheck_carrier_epoch_run397.py` | 4 |
| Capability PermissionGate | `src/ark/agency/policy.py` | `tests/test_permission_grant_yield_epoch_run397.py` | 10 |
| Registered PermissionGate materialization | `src/ark/agency/policy.py` | `tests/test_registered_materialization_yield_epoch_run397.py` | 7 |
| Startup evaluation | `src/ark/startup_readiness_review.py` | `tests/test_startup_probe_input_epoch_run397.py` | 6 |

### Retention: original carrier custody and later-result custody

A retained inventory and its independently supplied revocation witness may be
`frozen` Python dataclasses, yet privileged in-process reflection can replace
their `items` or `rows` tuple with a value-equal copy. Pure equality checks
would allow a changed evidence carrier to pass a later read. The recheck now
pins the original cached item tuple, each original item object, and the
original revocation rows tuple **before the first SQLite/cross-store review**.
It refuses a value-equal substitution after each independent review.

The later current-time retention inventory is also pinned before the
third/fourth independent observations. Its returned items cannot silently
be replaced by value-equal new carriers while those later callbacks run.
No deletion, data export, legal-consent inference, or authenticated erasure
claim is performed. Cross-SQLite reads are still NOT globally atomic.

### PermissionGate: check at *each generator yield*

A caller-provided grant generator can yield a valid grant, briefly mutate an
earlier grant, `ToolCall`, `ToolSpec.effect`, or one-shot token before the
next yield, and restore the value before `StopIteration`. Checking epochs only
at generator exhaustion misses this observed intermediate drift and could
incorrectly spend a process-local synthetic one-shot token.

`authorize()` now rechecks all previously yielded grants plus the original
action/spec/token epoch on **every yielded grant**, before considering the new
yield for a match. The original final epoch check and under-lock WRITE spend
check remain intact. Focused negative tests cover five WRITE mutation
variants, three READ diagnostic variants, and two unchanged positive paths.
A PermissionGate result does not authenticate a human issuer and never
dispatches a real backend.

### Registered grant materialization: scope checks cannot be delayed

`authorize_registered()` first binds a registry-authenticated local
`ToolCall`, then materializes a caller-supplied grant iterable before
delegating to `authorize()`. Merely doing `tuple(grants)` and re-binding
the registry at the end missed reflected intermediate alterations of
previous grants, registry registration identity, the call or token that
were restored before iteration ended. The registry-bound materialization
now rechecks the original call/token, pinned registration revision, and
every previously observed exact grant after **each** yield, including a
final recheck at iterator exhaustion. No backend runs. Five negative
WRITE fixtures and two unchanged READ/WRITE fixtures exercise the path.

### Startup: bind probe inputs before validation callbacks

`evaluate_startup_readiness()` used to clone successive
`StartupComponent` probes without rechecking earlier original objects.
A later component's `__post_init__` validation can execute reentrant
code that edits an earlier frozen probe. The output could then represent
a mixture of epochs. The evaluator now pins exact earlier probe values
and dependency tuple identities before validating/cloning components,
checking the original inputs immediately after each component clone,
before final output construction, and after digest formation.

Regression fixtures exercise the original probe's component ID, local
readiness state, a value-equal dependency tuple replacement, failure code,
schema revision, and transient mutation that is restored during a still
later component callback. READY/BLOCKED remain unauthenticated supplied
diagnostics, not activation authority.

## Verification boundaries and known non-proofs

The four implementation/test packages were written using GitHub's ordinary Contents
API, re-reading PR #8 HEAD immediately before every write. Existing automatic
public-repository PR CI runs test Ruff and the Ubuntu/Windows Python matrix;
no duplicate workflow was manually dispatched. **Each CI verdict applies
only to its exact HEAD**; this document is not itself proof of a GREEN run.
The canonical status checkpoint will cite observed run IDs and outstanding
jobs, including intermediate failures if any, after direct inspection.

Reflected Python object-identity checks and local hashes are not OS
file-descriptor custody, signed history, memory isolation, trusted time,
user consent, a durable cross-process authorization record, or exactly-once
external execution. A privileged actor may still alter unobserved inputs,
recompute local hashes, or mutate evidence after the last comparison.
UNKNOWN external WRITE is never auto-replayed. The actual ToolBackend,
camera/microphone/screen capture, scheduler notifications, protected V2
FINAL, V3 Candidate training/promotion, main merge, paid GPU/APIs and
irreversible privacy actions remain disabled/out of scope. Frozen
V1/V2/Local UI/Launcher evidence, Memory v1 DDL and Draft V3 PR #5
contracts are unchanged.

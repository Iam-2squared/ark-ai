# ARK AI — Run642 non-UI CAS outcome, Planner race and scope isolation

## Scope and immutable boundaries

Work basis: Draft PR #8 `research/jarvis-foundations` HEAD
`5d84f363b3e0405c96589313fd58d852f50aa5d6`.
That HEAD's GitHub Actions run [#42098379536](https://github.com/Iam-2squared/ark-ai/actions/runs/42098379536)
finished **six GREEN jobs** (Ubuntu/Windows × Python 3.11/3.12/3.13).

This invocation changes only reversible, isolated JARVIS non-UI work. The
frozen Memory v1 SQLite schema, V1/V2/evaluation contracts, Local UI/Launcher
evidence, `main`, PR #5 and PR #9 remain outside its write scope.
No external execution, real tools, model weights, paid service, candidate,
credentials, protected final evaluation, or promotion is authorized.

## Package A — preaccess result-carrier integrity

`src/ark/memory/generation_cas_outcome_review.py` pins the original
`MemoryCASOutcomeReview` six slotted field descriptors plus
`__new__`, `__getattribute__` and `__getattr__` hooks, in addition to
the already checked class identity, constructor and False-only authority
descriptors. The guard checks exact class-dictionary members before the
first private SQLite read, after callback boundaries and before constructing
or reading a result. This closes an executable descriptor/lookup hole:
unchanged False-only permission properties were insufficient.

`tests/test_memory_cas_outcome_preaccess_carriers_run642.py` adds nine
parameterized/synthetic cases: six replaced result slots, two lookup hooks
and one mutation inside a read-only snapshot callback. They assert denial
without invoking the injected getter or accessing private SQLite when
the replacement is preinstalled; a late replacement is manual-only.
This is **not** trusted identity/consent or permission to replay.

## Package B — Planner competing start

`tests/test_planner_journal_same_step_race_run642.py` adds three cases.
Two separate SQLite journal handles synchronize competing RUNNING starts
at the same expected revision; one wins and one must lose. Subsequent
restart recovery must preserve a single RUNNING/UNKNOWN event and both
no-dispatch/no-replay denials. An older timestamp and a stale revision are
rejected without appending an extra durable transition. No backend runs.

## Package C — independent Memory scope custody

`tests/test_memory_ambiguity_namespace_isolation_run642.py` adds four
cases spanning another owner and another namespace, with unchanged or
independently matching target updates. Mutating the unrelated local
scope must not masquerade as this caller's own COMMIT. Retained and observed
target prefixes remain scoped; an identical payload is **never** attributed
to the calling invocation. All reports remain manual-only.

## CI and limitations

Newly authored cases: **16** (9 + 3 + 4); this is not a pytest PASS count.
Normal GitHub Contents writes resulted in source commit
`5871fdbc1d934008daba3f3b9bdba0d43613d173`,
tests `38fe975916f999f75dc6350945576b21d7825cce`,
`b2ba12c501b2b7dfbaa6542cffabd0e77b8fdffd`, and
`97dfce64e8da586e724a49ca07cf3fef6c75299f`.
The initial source+test [CI #42105615665](https://github.com/Iam-2squared/ark-ai/actions/runs/42105615665)
and Planner [CI #42105732228](https://github.com/Iam-2squared/ark-ai/actions/runs/42105732228)
failed at Ruff `I001` in the new CAS outcome test import block.
The smallest formatting-only fix was saved at
`35b329ec58bf889bc23214fc1becfefe6711791b`.
The latest corrected run [#42106130428](https://github.com/Iam-2squared/ark-ai/actions/runs/42106130428)
was **QUEUED** at report preparation time; full 6/6 GREEN is **not claimed**.
Do not conflate an earlier validated HEAD with the latest one.

Local GitHub clone was unavailable due to DNS resolution failure; local
pytest and Ruff were not run. Actual CI logs determine success/failure.
The independent SQLite stores used by Planner, occurrence and audit lack
cross-store atomicity, and a local SHA-256 witness does not prove identity,
trusted time, human consent or exactly-once real-world effects.

## Next plan / 今後の方針

1. Confirm the corrected commit's exact-head Ubuntu/Windows 6-job CI.
   If FAIL, use job logs and make the minimum semantics-preserving repair.
2. Extend Memory ambiguous COMMIT/event-history reconciliation, and Planner
   UNKNOWN crash recovery under concurrent state changes.
3. Integrate ToolRegistry/PermissionGate/one-shot authorization with
   audit-before-action and occurrence replay prevention in a **disconnected
   mock executor only**, after lower-level exact-head GREEN.
4. Maintain PR #5 Draft, PR #9 Draft and UI pause; never cross free-only,
   frozen-contract, Candidate, V2 final-evaluation or main-merge gates.

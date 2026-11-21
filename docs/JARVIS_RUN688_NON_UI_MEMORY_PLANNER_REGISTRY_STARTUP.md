# ARK AI Run688 — Non-UI Cross-Store Safety Regression Packages

## Classification and exact work basis

**FREE-ONLY / DISCONNECTED / NON-UI / NO REAL TOOL ACTION.** Work on
[Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8),
`research/jarvis-foundations`. Initial exact basis was Run687 checkpoint
HEAD `386f3a80131bb2b0843cd19616ab2e368881ab09`.

The incoming checkpoint
[CI #42379447405](https://github.com/Iam-2squared/ark-ai/actions/runs/42379447405)
was independently checked **6/6 GREEN** on Windows/Ubuntu × Python
3.11–3.13 before these packages. That evidence is for **Run687 HEAD only**;
it does not establish Run688 HEAD as passing.

This invocation wrote **5 new focused test files and 24 parameterized cases**.
No production modules, frozen V1/V2/Local UI/Launcher contracts, main branch,
Draft PR #5/#9 or UI/front-end were modified. These checks remain diagnostic
and simulated rather than user-authorizing.

## A — CAS COMMIT ambiguity + scoped privacy veto (4 cases)

`tests/test_memory_cas_ambiguity_privacy_cross_scope_run688.py` at
`9abbed88d07c08457e1f516f68612583ebdb4b83` combines
`generation_fenced_memory_update`,
`review_memory_ambiguous_commit_pair` and an independent SQLite
`SyntheticContextRevocationLedger` under four second-writer cases:
no write, same bytes, different bytes and unrelated owner write.
Manual-only dispositions may differ; none attributes a commit to its caller,
grants retry, authenticates a clock or overrides an independently persisted
privacy veto. The test checks detached inventories before and after a cold
reopen, verifies no private payload in diagnostic representations and checks
that reviews append no Memory events.

## B — Planner diamond terminal + disjoint work after restart (4 cases)

`tests/test_planner_terminal_diamond_disjoint_restart_run688.py` at
`7d6f3b2584fc5447fd11c4af3b6fabea423824e0` exercises FAILED and
CANCELLED root outcomes against independent SUCCEEDED and FAILED outcomes.
Two SQLite journal handles must preserve exactly revised BLOCKED descendants,
reject stale RUNNING for them and keep unrelated root transitions available.
Cold readers must agree on the terminal status digest; no backend runs and
neither dispatch nor automatic replay can be inferred.

## C — Immutable Registry order + one-shot occurrence restart (6 cases)

`tests/test_registry_reordered_occurrence_restart_run688.py` at
`b5d9a38ac981db35c303e56b41a97af5776ce0b5` confirms registry
revision identity across reordered READ/WRITE registrations. A second
`SyntheticOccurrenceStore` opening the same SQLite file must reject
duplicated token, duplicated occurrence, mismatched request, expired token
and noninteger clock cases. The first committed reservation remains the
only entry, even though the second read-only registry order differs. This
is local replay protection, **not authenticated permission**.

## D — Cross-connection startup schema probe (5 cases)

`tests/test_disconnected_cross_connection_schema_readiness_run688.py` at
`6dc961ff60a102151a332cd7798f543d065204e1` binds a query-only
startup probe to a retained SQLite schema seal. An independent writer
introduces a new table, index, view or trigger, which the startup reviewer
must deny as changed schema. A data-only INSERT should preserve schema-based
diagnostic identity. The registered READ backend is a deliberately failing
non-executor and must remain uncalled. Even an unchanged review is never
startup or external action authority.

## E — Window freshness is not closed Observation provenance (5 cases)

`tests/test_observation_window_closed_chain_separation_run688.py` at
`73105fbea1d4405397bd359ea0798dea89f2057f` contrasts a legitimate
`ObservationWindowReview` age/privacy-scope freshness check with the stricter
`review_disconnected_fixture_chain` linear-history requirement. A fresh
window must not launder four malformed closed histories (skipped immediate
parent, duplicate content digest, non-increasing timestamps or source drift).
The valid two-envelope fixture remains deterministic and denial-only.
Both validators operate entirely on synthetic metadata; no media acquisition
or personal-content disclosure is implemented.

## CI, evidence quality and remaining blockers

New GitHub Actions runs were automatically triggered by each normal
Contents API write. At the first sampling they were **IN PROGRESS**,
not PASS: A [#42382785233](https://github.com/Iam-2squared/ark-ai/actions/runs/42382785233),
B [#42382825183](https://github.com/Iam-2squared/ark-ai/actions/runs/42382825183),
C [#42382899200](https://github.com/Iam-2squared/ark-ai/actions/runs/42382899200),
D [#42383025835](https://github.com/Iam-2squared/ark-ai/actions/runs/42383025835),
E [#42383426514](https://github.com/Iam-2squared/ark-ai/actions/runs/42383426514).
All 24 test definitions are **authored, not exact-head all-platform
PASS-attested**. If any job fails, inspect the exact failed job and make the
smallest legitimate correction; do not relax production invariants or bypass
GitHub safeguards.

The simulated SQLite ledger, hash digests, synthetic tokens and caller
clocks do **not** authenticate a reviewer, original data provenance, durable
user consent, hardware readiness, real tool effects, global erasure or
cross-database atomicity. A COMMIT-UNKNOWN WRITE always remains
**NO AUTOMATIC REPLAY**. No paid APIs/compute, external GPU, accounts,
credentials, real Candidate adapter/weights, protected V2 evaluation,
Candidate promotion, destructive changes or main merge occurred.

[Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5)
remains under its separate free/paid hard gate. Read-only inspection of
`docs/v3/PRE_PAID_COMPUTE_GATE.md` on its branch confirms unresolved
immutable base/tool hashes, reviewed 120/30 provenance/rights/contamination,
concrete compute/software/hardware identities, cost/time caps and
separate user authorizations. [UI Draft PR #9](https://github.com/Iam-2squared/ark-ai/pull/9)
remains untouched and paused. Overall **ARK/JARVIS/V3 NOT_PASSED**.

## Next plan / 今後の方針

1. Establish 6/6 GREEN for the **actual checkpoint-result HEAD**, not just
   a package ancestor; inspect and repair any precise failed job.
2. After that lower-level evidence, deepen real-offline Planner step READ
   receipt recovery and terminal state witness integration, preserving the
   no-retry rule after unknown WRITE.
3. Advance Memory COMMIT-UNKNOWN/CAS/ABA/expiry/WAL coherent snapshots and
   independent privacy veto/retention lifecycle without private payload logs.
4. Continue disconnected startup and proactive/observation backend contracts;
   leave UI paused and all external paid/frozen review gates closed.

# Run813 — Disconnected Planner inventory/recovery and Memory expiry restart reconciliation

## Boundaries

Two independent **FREE-ONLY / NON-UI** source+test packages saved to Draft PR #8 using GitHub Contents API. Both remain strictly disconnected; all authorization properties return False. They do NOT dispatch tools, retry ambiguous WRITE, purge Memory, authenticate provenance or time, verify independent inventory completeness, prove cross-store atomicity, open protected V2 evaluation, create a Candidate, authorize training, use external GPU, or incur new paid services. All V1/V2/Local UI/Launcher freezes, V3 PR #5 gate, and UI pause on PR #9 were preserved. ARK/JARVIS NOT_PASSED.

Initial work-basis HEAD: b5fc76a65746ba0f5f1e293b7c3563db3aeefee3; its final Run812 [CI #43170653561](https://github.com/Iam-2squared/ark-ai/actions/runs/43170653561) was independently confirmed **GREEN 6/6** (Windows/Ubuntu, Python 3.11–3.13).

## A — Planner receipt, WRITE inventory, and restart UNKNOWN cross-bind

- Source: src/ark/agency/disconnected_restart_receipt_inventory_bundle.py; commit c7ac4b0aaefdaa25cd23b7e0e04a1ecdf514b10f.
- Tests: tests/test_disconnected_restart_receipt_inventory_bundle_run813.py; commit c78b05ae34cf55e9d2cd370609f3b24e74d07690; **21 submitted cases** (1 expected, 18 adverse, 2 original-callback/authority).
- Replays original disconnected WRITE inventory/matrix+quarantine, checks every canonical projection field, rechecks exact DAG receipt bytes, joins recovered journal tail and RUNNING/UNKNOWN quarantine, then repeats the WRITE inventory review to detect interim source drift. The local binding digest never enables execution.
- Caller-supplied WRITE inventory and independent-source claims can still be incomplete; there is no authenticated event source or atomic cross-store snapshot.
- CI: [#43178428488](https://github.com/Iam-2squared/ark-ai/actions/runs/43178428488) source; [#43178588894](https://github.com/Iam-2squared/ark-ai/actions/runs/43178588894) source+tests. Latest observed source+test jobs were **IN PROGRESS**, not 6/6 GREEN.

## B — Memory expiry retained-summary/page-epoch reconciliation

- Source: src/ark/memory/expiry_restart_receipt_review.py; commit a999d8c63c3670e6d5edc271087f1a1f19b392b0.
- Tests: tests/test_memory_expiry_restart_receipt_run813.py; commit 6b7a49a8175b94ac4819e95748247f6b0ba59d5a; **27 submitted cases** (1 expected, 5 transitions, 19 stale/invalid, 2 custody).
- Recomputes a prior cohort from exact supplied per-scope pages and compares it with a retained prior summary, reconstructs observed pages under the same bounded scope inventory, compares clock/count/truncation, and replays both page epochs for drift. Returned data is content-free hashes/counts.
- No physical SQLite read, cross-scope atomicity, authenticated owner consent, trusted time, deletion, or data export.
- CI: [#43178678753](https://github.com/Iam-2squared/ark-ai/actions/runs/43178678753) source; [#43178755197](https://github.com/Iam-2squared/ark-ai/actions/runs/43178755197) source+tests. Exact newer run **IN PROGRESS**, not GREEN.

## Read-only independent revocation CI diagnosis

Reviewed historical [CI #43165560549](https://github.com/Iam-2squared/ark-ai/actions/runs/43165560549) failed job 131006498501 (Ubuntu Python 3.12). In the cross-process revocation test, one child printed REVOKED with a 64-char digest. The other entered the caught SyntheticContextRevocationRejected branch, but the subprocess failed its assertion that the exception message contained "already revoked". The exception message was **not logged**, so the underlying reject reason is **UNDETERMINED**; no fix or loosened test is claimed. The next diagnostic should capture the exact rejection while preserving the fail-closed behavior.

## Next plan

Confirm all six CI jobs for the exact latest source+test/checkpoint HEAD; inspect any failing job logs before minimal semantics-preserving corrections. Continue durable Planner crash/UNKNOWN quarantine, Memory CAS/ABA and COMMIT-UNKNOWN/manual recovery, registry-bound PermissionGate, audit-before-action, privacy-safe Personal Context, and free-only V3 path/reproducibility guards. Respect user authorization gates, PR Draft states, and paused UI throughout.

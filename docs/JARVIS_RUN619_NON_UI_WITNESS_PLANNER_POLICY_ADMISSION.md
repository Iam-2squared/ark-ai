# ARK AI — Run619 non-UI local safety foundations

**Scope:** Only reversible source/tests on Draft PR #8 (`research/jarvis-foundations`). Work-basis commit: `243a47ef90eb5f6bb79a8572907fc1aef325fa9f`. No front-end work. All evidence is local/synthetic and does not establish user consent, trusted time, backend effects, independently authenticated witnesses, or exactly-once execution.

## Package A — synthetic occurrence retained-witness method custody

- Source: `src/ark/agency/synthetic_occurrence_continuity_review.py` at `0b1c50f17587fb2aa3ae1ca61af9fc434802c974`.
- Pin the import-original `SyntheticLedgerWitness` type, constructor, and `assert_integrity` implementation before reading a locally retained witness, during read-only SQLite snapshot checks, and after reentrant digest/commit/close boundaries.
- Reject a preinstalled no-op integrity method or forged constructor *before invocation*. A valid digest plus a replaced validator is not evidence of integrity.
- New offline tests: `tests/test_occurrence_original_witness_code_run619.py` (5 parameter-expanded cases). Two existing fault-fixture files were revised to keep their **reentrant mutation and post-COMMIT/close coverage** while observing via digest/attribute hooks, rather than replacing the validator being protected: `tests/test_synthetic_ledger_retained_snapshot_run407.py` and `tests/test_occurrence_witness_commit_custody_run422.py`. No backing ToolBackend execution.

## Package B — PlanGraph prepublish cascade staging

- Source: `src/ark/agency/planner.py` at `1a05f3a1f6159c0e899f361bdb075b82c73a346b`.
- Build the terminal transition and every derived BLOCKED descendant status **off to the side**. Recheck authoritative topology and status epochs; reject noncanonical staged statuses. Only then publish the batch into the graph's in-process state mapping.
- Previously, a failed Python `dataclasses.replace` on the second/third descendant could leave a partially written in-memory cascade with a stale status epoch. The new staging rule avoids partial publication when constructors fail without mutating the original graph.
- New offline tests: `tests/test_planner_staged_cascade_run619.py` (6 parameter-expanded cases): interruption at each of four construction stages, forged staged result rejection, and a valid complete cascade. This is **not** a durable cross-process transaction, restart-safe execution coordinator, or external-effect proof.

## Package C — PermissionGate under-lock postcallback admission

- Source: `src/ark/agency/policy.py` at `f2444a0c2e6cc966ec7010875191321a9e1396f6`.
- Recheck the originally captured ToolSpec, ToolCall, grant, and one-shot-token epoch after the optional reentrant `_registered_recheck` callback, still under the local token lock, and **before** spending the one-shot token.
- This closes the gap in which a caller-accessible callback could mutate a previously accepted grant/scope or token after the earlier under-lock validation but before local token consumption.
- New offline tests: `tests/test_permission_recheck_final_custody_run619.py` (5 parameter-expanded cases), checking forged scope, expiry, effect, equal-value argument-carrier swap, and token expiry. A denied attempt leaves the local token unspent. No real tool dispatch and no durable authorization claim.

## Package D — Memory expiry preview constructor custody

- Source: `src/ark/memory/expiry_candidate_preview.py` at `783559649447a54f7bddc92386f84666e98d8387`.
- Pin the import-original `MemoryExpiryPreview.__init__` in the existing non-authorizing authority check; recheck immediately before instantiating the content-free preview. A swapped constructor is refused before SQLite access when preinstalled and before any attacker constructor call when rebound during row hydration or final fingerprinting.
- New offline tests: `tests/test_memory_expiry_constructor_custody_run619.py` (5 parameter-expanded cases): preinstalled preview/reverify refusal, row/final-hash reentrancy refusal, and a normal read-only no-erasure control. No automatic purge, physical erasure proof, owner consent, or trusted clock.

## Validation, limitations, and safety controls

- **21 newly authored parameter-expanded pytest cases** across four files (5 + 6 + 5 + 5), plus two retained legacy fixture adaptations (five parametrized existing scenarios). This is not a local executed PASS count.
- Earlier checkpoint commit `243a47ef90eb5f6bb79a8572907fc1aef325fa9f`: GitHub Actions run [#41938198055](https://github.com/Iam-2squared/ark-ai/actions/runs/41938198055) **six-job GREEN** (Ubuntu/Windows, Python 3.11–3.13).
- Intermediate occurrence/Planner source-head CI [#41944012381](https://github.com/Iam-2squared/ark-ai/actions/runs/41944012381) and [#41944165366](https://github.com/Iam-2squared/ark-ai/actions/runs/41944165366) exposed **five expected legacy fault-fixture failures** from the new validator pinning; repairs were saved through normal GitHub Contents writes. These **intermediate FAILs are not final-head PASS evidence**.
- The earlier source+test head `9000392eba0078c02a7df12821ab632af525fd80` had [CI #41944668619](https://github.com/Iam-2squared/ark-ai/actions/runs/41944668619) QUEUED at initial observation; the new Memory source/test head `1b47dfec0392213b9fbd845f1434764230c81c64` is separately awaiting exact-head CI. Exact latest-head six-job success must be independently verified.
- No local GitHub clone or pytest was executed: the available container could not resolve `github.com` DNS. GitHub Actions is the actual test source, and authored test counts are **not** PASS counts.
- Frozen V1/V2/Local UI/Launcher contracts/evidence, protected evaluation, main, and Draft PR #5/#9 are untouched. Do not promote Candidate weights, dispatch real Tools, open V2 final evaluation, merge any protected PR, require credentials or create billable activity. UI remains paused.
- PR #5 V3 learning remains gated and NOT_PASSED. ARK/JARVIS overall remains **NOT_PASSED**.

**Next:** inspect the complete exact-head six-job CI, repair only logged failures by ordinary permitted writes, then proceed to Memory COMMIT-UNKNOWN manual-only reconciliation, Planner journal recovery with authorized/disconnected action lifecycle, and privacy-safe Personal Context/Observation fixtures. Always preserve no automatic WRITE replay.

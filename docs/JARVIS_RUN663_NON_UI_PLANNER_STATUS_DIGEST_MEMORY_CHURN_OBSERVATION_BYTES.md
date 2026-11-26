# ARK AI — Run663 non-UI core: Planner recovery status binding, Memory lifetime isolation, observation byte fidelity

## Work basis and scope

- Initial repository PR #8 HEAD: `960b9ecf570f569de791d36b9003c0be6b0b415d` on `research/jarvis-foundations`, OPEN / Draft / unmerged. Its exact-head Actions [#42230595773](https://github.com/Iam-2squared/ark-ai/actions/runs/42230595773) completed **6/6 GREEN** (Ubuntu/Windows × Python 3.11–3.13), confirmed from individual jobs at this invocation's start.
- Four coherent packages were committed through **ordinary GitHub Contents API** after a fresh PR HEAD read for every write. No main, PR #5, PR #9, UI/frontend, frozen V1/V2/Local UI/Launcher evidence/contract, protected evaluation or real backend action is modified.
- All new tests use disconnected fixture-only inputs, disposable SQLite, synthetic clock values, and memory-local media bytes. No actual consent, authenticated clock/writer, real sensors, trained weights, tool dispatch, cloud GPU, new credential, paid service, network I/O or notification.

## Package A — bind recovered Planner statuses to journal tail

**Production source** `src/ark/agency/disconnected_planner_fence_projection.py`, commit `673d52fe9700a16f92aded64076faa3de79a6d28`.

Prior to this change, the adapter checked the supplied replay tail's topology and validated the shape/membership of `SyntheticPlanRecovery.step_statuses`, but did **not** verify that the complete status/revision image hashed to `tail.status_digest`. A caller could use `dataclasses.replace` to change a frozen recovery object's tuple while keeping its retained tail and present an inconsistent synthetic status snapshot for an inert `READY_MOCK_ONLY` disposition.

The projection now recomputes exactly the Planner's canonical `pstate_` status digest over the topology identity, all exact step IDs, states and revisions (in sorted order) and refuses mismatches before creating the recovery-fence claims. It performs the existing original-carrier/epoch check after hashing. It does not attempt to authenticate independent journal custody or grant execution.

**Focused new tests** `tests/test_planner_projection_replay_digest_run663.py`, commit `a7074856795c95eb41025a710c6b5e668f14d137`: **4 authored cases**. Three `dataclasses.replace` scenarios forge pending revision, terminal state or RUNNING membership while retaining the old tail; each must reject without appending a journal event. A legitimately replayed failed step must still map to a terminal false-only review. A matching local digest remains a consistency test, not trusted provenance or backend permission.

## Package B — disjoint Memory lifetime ABA versus target CAS

**New tests** `tests/test_memory_disjoint_lifetime_churn_run663.py`, commit `40dd5aec828f0b092237322be12a00e3e151072f`: **3 authored parameterized cases**. An independent SQLite connection creates, deletes and recreates a separate lifetime (same source ID in another owner or namespace, or a distinct source in the target scope). This must leave an originally retained **target** generation token usable for its separately requested local update. Event high-water and row-event alignment are examined after the resulting five-event sequence. Contrasts with Run662's target-row expiry/recreate ABA, which must reject the old token.

This is an opt-in local Memory mutation, **not** an authorization to share private information, infer writer identity or silently retry a COMMIT-UNKNOWN effect. Frozen v1 Memory surface/schema remains unchanged.

## Package C — Observation byte identity and minimization

**New tests** `tests/test_observation_fixture_byte_identity_run663.py`, commit `d732db606cf0e644fbf087c9b0992b9e64590d96`: **6 authored cases**. Text adapter preserves exact UTF-8 byte digests even when NFC-equivalent Unicode strings look the same; parent linkage changes envelope identity without changing content bytes; IMAGE/SCREEN synthetic binaries with embedded zero bytes retain only hashes; an unpaired surrogate is rejected; and a multibyte text whose character count is below the cap but encoded length exceeds 4 MiB is refused.

No private raw payload, device acquisition, model inference, externally authenticated observation origin or real modality consent is added.

## CI and caveats

- Baseline [#42230595773](https://github.com/Iam-2squared/ark-ai/actions/runs/42230595773) at `960b9ecf...`: **6/6 GREEN confirmed**.
- Planner production-source [#42236602183](https://github.com/Iam-2squared/ark-ai/actions/runs/42236602183) at `673d52f...`: running at report preparation, **Ubuntu 3.11/3.12/3.13 GREEN**, Windows jobs not yet confirmed.
- Memory tests [#42236808766](https://github.com/Iam-2squared/ark-ai/actions/runs/42236808766) at `40dd5ae...`: in progress at report preparation; intermediate-head evidence only.
- Observation tests [#42237000845](https://github.com/Iam-2squared/ark-ai/actions/runs/42237000845) at `d732db6...`: in progress at report preparation; intermediate-head evidence only.
- Planner regression tests [#42237240005](https://github.com/Iam-2squared/ark-ai/actions/runs/42237240005) at `a707485...`: in progress at report preparation; intermediate-head evidence only.
- **13 authored cases are not an independently certified PASS count.** Latest final technical-report/checkpoint HEAD must be checked separately across all six CI jobs. No local full pytest/Ruff or target-PC GGUF evidence is claimed.

## Boundaries and next dependencies

1. Resolve actual CI job outcomes, especially all Windows environments and latest exact HEAD; if any FAIL, inspect real logs and repair the smallest semantics-preserving path using the normal GitHub safety route.
2. Extend coherent Planner replay + independently retained RESULT receipt verification before admitting `SUCCEEDED` to an inert fence. Keep unverified or missing receipts blocked.
3. Continue target Memory COMMIT-UNKNOWN/ABA/expiry/concurrency review and strict separation of local diagnosis from external action authority.
4. After exact-head GREEN prerequisites, consider immutable ToolRegistry, exact-type PermissionGate and audit-before-action/occurrence/false-only mock execution integration. Independently advance privacy-safe Personal Context, proactive restart quarantine and free V3 path/provenance/identity gates. PR #5 and its real training/protected V2 evaluation authorization remain closed; PR #9 and all UI/frontend development remain paused.

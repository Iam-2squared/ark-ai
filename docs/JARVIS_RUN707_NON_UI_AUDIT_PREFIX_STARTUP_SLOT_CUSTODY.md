# ARK AI — Run707 Free-Only Non-UI Core Evidence

**Scope:** isolated, reversible audit-before-action and startup-readiness defensive hardening on `research/jarvis-foundations` / Draft PR #8, without external backend execution. **Initial work-basis HEAD:** `c4a8149070acac283cc03191f82523705721f68b`. **Evidence-report-write-basis HEAD:** `ce070076391b0297128dec4c7226838e6c42d94b`. No frozen schema/contract change, no main merge or UI change.

## Package A — full local audit prefix validation before append

- Source [`a578a168`](https://github.com/Iam-2squared/ark-ai/commit/a578a1684f6cd0d42beffb16e94f3d8eebf6189f): `src/ark/agency/audit.py` validates all existing persisted audit rows' exact types, ID derivation and chronological ordering **inside the existing SQLite BEGIN IMMEDIATE transaction** and **before sampling the append clock**. Dense IDs and a valid last row alone do not detect a prior overwritten first/middle event.
- Tests [`048f4773`](https://github.com/Iam-2squared/ark-ai/commit/048f47735128f150d8e73bf7b84feecec0605922): **14 authored test cases** (2 historical row positions × 6 corruptions; one earlier chronology rollback; one healthy append). The rejection fixtures assert no new row, no advance of local SQLite high-water and no user-supplied clock callback on malformed prefixes.
- Limitations: The new per-append O(N) prefix scan trades bounded throughput for local historical consistency and may require a reviewed independent retention/custody design before high-volume use. SQLite contents/high-water are mutable together by privileged local actors: this scan is **not** an authenticated audit chain, external exactly-once effect evidence, legal erasure evidence or a trusted-clock certificate. No automatic retry after COMMIT-UNKNOWN.

## Package B — startup exact original carrier descriptor custody

- Source [`a4f05c57`](https://github.com/Iam-2squared/ark-ai/commit/a4f05c5728080a5bb3cf2f3f79acbba4b5d495bf): `src/ark/startup_readiness_review.py` pins import-original field slots and `__new__`/`__getattribute__`/`__getattr__` hooks of `StartupComponent`, `ComponentResult` and `StartupSnapshot`. Input `__post_init__`, evaluation entry/reentry and cached snapshot integrity checks deny changed class definitions **before** reading affected provenance or readiness state.
- Tests [`ce070076`](https://github.com/Iam-2squared/ark-ai/commit/ce070076391b0297128dec4c7226838e6c42d94b): **17 authored cases**, including 16 separate subprocess-isolated hostile descriptor/getter modifications and a healthy blocked dependency graph. Process isolation avoids CPython type slot cache cross-test contamination.
- Limitations: This guards import-original Python class custody in a disconnected/mock diagnostic, **not** process isolation from malicious Python code, independent hardware readiness attestation, user permission, real tool execution or notification delivery.

## CI, truthful scope, and blocking gates

- Run706 source/test variants previously failed some actual CI from changed diagnostic earliness; the preceding Run705 initial exact work-basis [#42456694488](https://github.com/Iam-2squared/ark-ai/actions/runs/42456694488) was reported **6/6 GREEN** in the previous canonical checkpoint. The Run706 amended report [#42461121973](https://github.com/Iam-2squared/ark-ai/actions/runs/42461121973) still had unfinished jobs during Run707 initial checks.
- The new Run707 combined source/test at HEAD `ce070076391b0297128dec4c7226838e6c42d94b` associated with [CI #42461995306](https://github.com/Iam-2squared/ark-ai/actions/runs/42461995306), **QUEUED** when first reviewed. **No latest Run707 Windows/Ubuntu × Python 3.11/3.12/3.13 6/6 PASS, local pytest or Ruff PASS is claimed yet.** Resolve any actual diagnostic/format failure from real logs without relaxing safety.
- All UI/frontend development remains paused. PR #5 (protected V3) and PR #9 (UI) stay untouched, Draft/unmerged. Frozen V1/V2/Local UI/Launcher contracts/evidence unchanged; no protected final evaluation, paid GPU/API/service, real Candidate/model weights, new credentials, physical PC action, irreversible cleanup, real action execution, new secrets, trusted-clock or human-review claim.

## Next plan / 今後の方針

1. Inspect **exact latest-HEAD** CI and actual six job conclusions; repair only demonstrated failures with semantics-preserving edits and no duplicate equivalent CI launch.
2. Audit append complexity and independent retained historical prefix witness design **without** changing frozen DDL or claiming independently authenticated evidence; retain COMMIT-UNKNOWN manual resolution.
3. Verify startup original descriptors at external readiness/lease callsites before accepting synthetic READY as any basis for capability activation (currently prohibited); use disconnected tests and read-only analysis.
4. Independently progress Memory CAS/ABA, Planner step READ persistence/recovery, durable token/occurrence and observation/Personal Context privacy fixtures after lower-layer exact-head GREEN. Keep PR #5/#8/#9 Draft/unmerged and UI paused.

# ARK AI Run768 — non-UI registry, atomic WAL and frozen observation compatibility

**Work basis:** `83e4658d1c0ea7d8b25da95a5469e93a669dcd41` (previous Run767 canonical checkpoint). **Branch/PR:** `research/jarvis-foundations` / Draft PR #8 (OPEN/DRAFT/unmerged). All data are synthetic/local. No frontend development.

## A. Atomic pre-action: interrupted second reservation

- Test file `tests/test_atomic_preaction_two_row_wal_crash_run768.py`; source/test commit `55201f61216097c6da0f7cabfa3f9be8b76527bc`, **3 cases**.
- Independent child Python process is terminated in a second SQLite reservation after intent INSERT or after both intent/audit INSERT, before COMMIT. A second test terminates after the second reservation COMMIT but before returning a response.
- The tests inspect the previously committed witness, reject a stale CAS witness, and preserve deny-only flags for tool dispatch, replay and independently authenticated approval. No backend invocation or real external effects. This is **single-store** atomicity, not cross-store or external exactly-once.

## B. ToolRegistry NUL identity ingress

- `src/ark/agency/registry.py`, source commit `036a6663ecace9821c19af20e78ef119c5d4c660`: exact tool-registration name, capability and backend ID now reject embedded U+0000 during `_text()` preflight, before backend descriptor inspection or registry revision serialization.
- `tests/test_registry_nul_identity_run768.py`, test commit `b15489ba33b92efb2367df529d7299e1fea7cbe0`: **4 cases** (3 rejected identity fields, 1 Unicode/revision/no backend call).
- No new external tool connector, execution permission, human consent or trusted provenance was introduced.

## C. Frozen ObservationEnvelope v1 contract PRESERVED

- An initial exploratory edit to `src/ark/observations.py` (`50c6d70c748e2bb3507b9f78e39eb9db57b50497`, then an escape correction `fdfb1826864c72c4f16d2337a81c8c0860a509a2`) attempted to reject direct-envelope NUL labels. GitHub CI showed it violated existing **frozen v1 envelope compatibility**, because v1 intentionally allows such labels while the newer fixture adapter rejects them.
- **The source change was fully reverted using the ordinary GitHub Contents API** at `d0bc3f246f5f618df525513e7eb4f560c9b9543a`; resulting source Blob SHA is exactly the initial `373ddb5085afb09d1c451239a7e75afb34d8c2e0`. No frozen contract change remains.
- The new test `tests/test_observation_direct_nul_identity_run768.py` was corrected at `816df19af91dc0bf733969e7a38e0fc72a7415f4` to verify the unchanged v1 constructor/digest contract, the strictly rejecting **optional fixture adapter** boundary, and stable Unicode. **6 cases**.
- Compare against initial basis after correction: only `src/ark/agency/registry.py`, the three new test files, and this technical report differ. `src/ark/observations.py` is byte-identical to the baseline. No sensor capture/media access.

## Actual CI and failure chronology

- Previous baseline `83e4658d1c0ea7d8b25da95a5469e93a669dcd41`: [CI #42839474821](https://github.com/Iam-2squared/ark-ai/actions/runs/42839474821) **6/6 GREEN**, Windows/Ubuntu × Python 3.11/3.12/3.13. Not evidence for the present changes.
- [CI #42848695875](https://github.com/Iam-2squared/ark-ai/actions/runs/42848695875) on initial exploratory Observation source, [#42849081745](https://github.com/Iam-2squared/ark-ai/actions/runs/42849081745) on atomic WAL tests: Ubuntu 3/3 GREEN, Windows in progress at recorded sample.
- [CI #42849260230](https://github.com/Iam-2squared/ark-ai/actions/runs/42849260230) at intermediate Observation test SHA `16e884c3...`: **Ubuntu 3 FAIL** from double-escaped NUL in exploratory source; later source correction `fdfb182` addressed the escape.
- [CI #42849914931](https://github.com/Iam-2squared/ark-ai/actions/runs/42849914931) on `b15489ba...` **Ubuntu 3 FAIL** after the escape correction because existing `test_observation_fixture_nul_framing_run745.py` explicitly relies on direct v1 NUL labels. One Ubuntu 3.11 run also showed a pre-existing intermittent independent-process Memory CAS readiness assertion failure. **The frozen-contract regression was fixed by restoring the original source and updating the new tests** (source `d0bc3f2`, test `816df19`). Do not weaken the old tests to force PASS.
- **Corrected latest source/test HEAD:** `816df19af91dc0bf733969e7a38e0fc72a7415f4`. Its exact-head CI is **NOT YET VERIFIED ALL-SIX GREEN** as of this report; do not inherit any earlier run result. The subsequent report/checkpoint commits also produce distinct HEADs.
- **Current meaningful changes:** one backend source module (ToolRegistry), three new test files, **13 parameterized cases** (3 WAL + 4 registry + 6 observation compatibility). GitHub Actions is the execution evidence; local container cannot clone public GitHub due DNS isolation, and no fabricated local PASS is asserted.

## Frozen and free-only boundaries

- `main` `7a843f17eb96ed13d66f23b58b06406b3002e405` unchanged. Draft PR #5 `805b377697472268db02650a89c7a94b1c5337c8` remains protected/unmerged; Draft UI PR #9 `3b49048dd70eebcb6268299b9ecef4e301bbc0fd` remains paused/untouched/unmerged. Frozen V1/V2/Local UI/Launcher and observation v1 are preserved.
- No paid GPU/API/subscription, Candidate artifact, protected V2 evaluation, new secrets/accounts, physical device action, live notification, real ToolBackend dispatch, destructive action, main merge, raw-object bypass or force push.
- Local hashes/SQLite do not prove signed consent, trusted clock, immutable custody, source attestation, cross-store transactions, or external exactly-once effects. Ambiguous external WRITE stays **UNKNOWN/manual quarantine, never automatically replay**.

## Next plan / 今後の方針

1. Confirm corrected final HEAD CI across all six matrix jobs; if failure inspect actual job logs. Diagnose intermittent cross-process Memory test without weakening concurrency/corruption gates.
2. Memory CAS/ABA and durable history witnesses, Planner journal recovery and dependency-terminal propagation, then registry-bound PermissionGate + independent audit-before-action mock executor.
3. Maintain privacy-veto retention, proactive scheduler state/clock fences, observation fixture-only boundaries and V3 free approval/path/identity guards in separate reversible lanes. UI remains paused; no protected evaluation or paid work.

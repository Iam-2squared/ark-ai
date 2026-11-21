# ARK AI Run505 — detached receipt custody and V3 offline identity guards

**Scope:** free-only, reversible source/tests on two Draft/unmerged PRs. All
synthetic data, fixture observations and local digests are untrusted evidence;
none authenticates human consent, execution time, external identity, spend,
Candidate generation, physical erasure or permission for any Tool dispatch.

## Initial exact work basis

- JARVIS PR #8 `research/jarvis-foundations`: `adc1bec29c2364dcc8094c96507c29dc08db8389`.
- V3 PR #5 `research/v3-learning-evaluation`: `d10807e3493b390af6778b186f6cf837860fbafb`.
- Main `7a843f17eb96ed13d66f23b58b06406b3002e405`; no merge.
- Prior Run504 checkpoint remained intact; CI of its checkpoint:
  [41203534505](https://github.com/Iam-2squared/ark-ai/actions/runs/41203534505),
  six of six GREEN. Run504 source CI:
  [41203273094](https://github.com/Iam-2squared/ark-ai/actions/runs/41203273094),
  six of six GREEN.

## NEW: five independent, source-and-test packages

1. **Memory read-only expiry preview receipt**:
   `src/ark/memory/expiry_candidate_preview.py` and
   `tests/test_memory_expiry_verification_epoch_run505.py`.
   Verify all fields by exact primitive type/value rather than replaceable
   dataclass equality, recheck after denial getters, and re-read the bounded
   SQLite expiry page to detect routine post-validation drift. The report
   cannot authorize erasure or attest a trusted clock. **10 authored tests**.
   Source commit `81a80bb22781c9eaa1f984d54a70edf5a3551ea5`;
   test commit `259cefca5bd8379c7847b1f2c390303fde5e4408`.
2. **Planner failure-aware detached mock fixture**:
   `src/ark/agency/disconnected_batch_failure_fixture.py` and
   `tests/test_disconnected_failure_fixture_denial_epoch_run505.py`.
   Pin produced result-digest tuple, reject spoofed receipt equality and
   validate the same synthetic DAG after final authority callbacks. No
   ToolBackend, WRITE dispatch or real failure authentication. **10 tests**.
   Source `2b24fd82ffae37eedda8d41f7660f7820f505af8`;
   test `d4fa9451b905c2455c4291c3c8579f6c7cf62408`.
3. **Personal Context independently retained offline preview**:
   `src/ark/personal_context_offline_preview.py` and
   `tests/test_personal_context_detached_verify_run505.py`.
   New non-disclosing verifier rederives scoped, time-bounded synthetic
   content from explicit fixture inputs, rejects altered payloads and
   post-denial mutations, then rechecks source fixtures. This is *not*
   authenticated consent, live Memory review or export authorization.
   **16 tests**. Source `21597be90286f217873d95352219274376922e37`;
   test `d338d0b7febdfacf02c37bd70757e7ed317d9032`.
4. **V3 local identity bundle**:
   `src/ark/learning/identity_bundle_verify.py` and
   `tests/v3/test_identity_bundle_denial_epoch_run505.py`.
   Replace witness and bundle dataclass equality with exact-field
   comparisons, guard post-denial report/pin/file changes, and do a final
   bounded local-file recheck. Hashes are untrusted without independent
   custody; no execution permission. **10 tests**. Source
   `03602b1289fbcb3f0ad25a99a70c0a1448cdae34`;
   tests `0aaab9dff202580d38084f512c028ad6e5a225f2`.
5. **V3 local identity artifact witness**:
   `src/ark/learning/identity_artifact_verify.py` and
   `tests/v3/test_identity_artifact_denial_epoch_run505.py`.
   Recheck exact report identity and on-disk custody after final denial
   callbacks. A local JSON SHA is neither source provenance nor authorization.
   **7 tests**. Source `1e695e133826a54731046b27d04fc9efad3df6e1`;
   tests `fec9146b932c192a645e3790cb746aa542cc5171`.

**53 authored pytest cases, five packages.** Authored is not a claim that
the new cases have passed in independent local pytest. Source/test heads:
PR #8 `d338d0b7febdfacf02c37bd70757e7ed317d9032`;
PR #5 `fec9146b932c192a645e3790cb746aa542cc5171`.

## Validation boundaries

- At initial post-write inspection, PR #8 CI
  [41207337019](https://github.com/Iam-2squared/ark-ai/actions/runs/41207337019)
  and [41207705833](https://github.com/Iam-2squared/ark-ai/actions/runs/41207705833)
  had not yet established latest-source six-of-six GREEN.
- PR #5 bundle tests CI
  [41207523660](https://github.com/Iam-2squared/ark-ai/actions/runs/41207523660)
  was completed SUCCESS; newest artifact tests CI
  [41207808839](https://github.com/Iam-2squared/ark-ai/actions/runs/41207808839)
  was QUEUED at that inspection.
- Independent local pytest/Ruff remains NOT VERIFIED. No validation
  from prior HEAD may be inherited by a newer exact-head change.
- Existing frozen blobs verified unchanged:
  `src/ark/memory/contracts.py` =
  `b6e93821ecd69270a7634aceb20775dc36e9953c`;
  `src/ark/agency/contracts.py` =
  `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`;
  `docs/v3/CONTRACT.md` =
  `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`.

## Hard stops and next engineering order

Keep PR #5 and #8 Draft/unmerged, main and frozen V1/V2/UI/Launcher
evidence unchanged. No real Candidate, adapter or weights; no protected V2
final evaluation, paid/external GPU or API, credentials, automatic promotion,
external tool/device effects or destructive operations.

Next: establish per-job GREEN on the final exact source heads and fix only
observed failures; then prioritize Memory CAS/coherent snapshot and bounded
expiry transitions, Planner UNKNOWN WRITE quarantine/recovery, immutable
registry and exact-type permissions, trusted-clock audit-before-action,
Scheduler occurrence/replay protection, Personal Context revocation and
observation fixture contracts. Integration requires exact-head evidence,
explicit approval where gated, and is never implied by a synthetic hash.

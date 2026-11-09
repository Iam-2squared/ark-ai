# ARK AI — Run746 non-UI privacy and READ binding custody evidence

**Scope:** strictly zero-new-cost, locally synthetic/disconnected invariants only; no UI, Candidate/training, external compute, real tools, sensor collection, user grant, protected evaluation, frozen contract change, or main merge.

## Exact basis and three work packages

- Initial independently read work-basis HEAD: `f84b5cf847ac97d1845c6620b21e4652e22ce2c5`. Its exact [CI #42677310403](https://github.com/Iam-2squared/ark-ai/actions/runs/42677310403) completed **GREEN across six Windows/Ubuntu Python 3.11–3.13 jobs**. This is NOT a verdict on new work.
- **A / privacy retention dependency custody:** `src/ark/personal_context_retention_review.py` now pins original Memory row decoding, SQLite v1 schema check, revocation continuity, scope digest and JSON/SHA implementations before reading caller-private Memory, then rechecks around SQLite and row callbacks. `tests/test_retention_dependency_preaccess_run746.py` adds **8 authored cases**: six preinstalled callback substitutions, one reentrant path-access swap, and one existing behavior/no-authorization control. This does NOT sandbox arbitrary in-process Python, erase data, authenticate user identity, or make independent SQLite snapshots atomic.
- **B / Planner detached READ exact-input custody:** `src/ark/agency/disconnected_read_input_binding_review.py` rejects substituted receipt, witness, snapshot and recovery DTO lookup hooks before accepting caller-retained evidence. It additionally pins the recovered receipt identity, step fields, witness counters and successful input binding through digest and denial-only result callbacks, and checks the report against expected values rather than accepting constructor output as a new baseline. `tests/test_read_input_carrier_preaccess_run746.py` adds **5 authored cases**: four hostile getter substitutions + one valid nonauthorizing receipt. This remains fixture-only: no backend, independent input provenance, real result attestation, automatic replay or grant.
- **C / privacy erasure evidence:** `src/ark/privacy_erasure_evidence_review.py` now binds its import-original JSON/SHA, hex grammar, domain and five admissible evidence vocabularies before processing an owner scope claim. `tests/test_erasure_codec_preaccess_run746.py` adds **10 authored cases**: nine modified dependency/equal-valued carrier substitutions + one never-authorizing optimistic assessment. Prior source behavior permitting a substituted SHA to mutate input and then rejecting it is replaced by earlier refusal, with the original public erasure conclusion unchanged. This cannot prove physical erasure, WAL reclamation, backup elimination, user consent or authorized cleanup.

Total **23 newly authored synthetic regression cases** in three new test files; three non-UI source modules changed. No baseline frozen V1/V2, Local UI/Launcher, V3 Contract 1, or PR #5/#9 source was edited.

## CI and failure evidence (at report creation)

- A prior automatic run for `ba9222bb9ec7741da3241a23ec73e0e77b93a0fa`, [#42688032017](https://github.com/Iam-2squared/ark-ai/actions/runs/42688032017), **FAILED six jobs at Ruff I001** before pytest. Actual Ubuntu job 129400011463 showed three import-group errors involving the READ binding source and two newly added tests; this was a formatting error, not a security policy relaxation or test assertion failure.
- The three import-only fixes were normally saved on `research/jarvis-foundations` at `380394cb282fb2141132f9686dadb0604fc49c8b`, `d5984ff64c2671eb558d58cb6cc9cfab1ed4fcc9`, and `dfdc75cfb264928947864434f5827b5380f8da27`.
- At the latest inspection, automatic [CI #42688291600](https://github.com/Iam-2squared/ark-ai/actions/runs/42688291600) on `dfdc75cfb264928947864434f5827b5380f8da27` was **IN PROGRESS, six jobs running**. Its eventual verdict must be verified by exact SHA. No duplicate manual run was triggered.
- No full local pytest, real Windows file-handle custody, physical offline GGUF evaluation, real clock attestation, or authorized action occurred.

## Controlling boundaries / open risks

- Draft PR #8 `research/jarvis-foundations` is the only branch targeted for writes here. Main `7a843f17eb96ed13d66f23b58b06406b3002e405` and Draft PR #5 (controlled V3 gate) / Draft PR #9 (paused UI) remain unmodified, unmerged. Freeze and approval gates remain binding.
- Python import-identity guards are **local tamper detection**, not a process sandbox or trusted persistence. String/hashes in a local report can be coherently forged unless an independently authenticated retained witness exists.
- Planner input join is not an exactly-once tool execution proof; actual tool use requires immutable ToolRegistry, exact-type PermissionGate, trusted clock, durable action audit before invocation, and durable occurrence reservation across crash boundaries.
- Privacy retention does not equate expiry with deletion, and separately read SQLite stores cannot prove cross-store atomicity. Preserve privacy revocation, erasure and retention blockers.
- V3 training/preflight remains blocked by true immutable model/tool bytes, rights/provenance/human review, separate scoped user approval, device/driver identities and spending authorization. Do not start paid/external GPU or Candidate generation.

## Next plan / 今後の方針

1. Read the **six job logs of the latest source/test HEAD**; fix only reproducible failures through the normal GitHub Contents API and never label an older SHA's GREEN as the new source's PASS.
2. Continue coherent Memory CAS/ABA/expiry and manual-only COMMIT-UNKNOWN triage with durable retained history, independently witnessed event high-water and verified WAL snapshots.
3. Advance Planner exact successful READ manifests/terminal propagation, restart recovery, immutable registry/exact-type permissions and a disconnected mock executor only after lower-level exact-head GREEN evidence.
4. Continue private-context revocation/retention and proactive observation scheduling as independently reversible lanes; maintain V3 free-only rights/approval reproducibility guards without opening protected gates.

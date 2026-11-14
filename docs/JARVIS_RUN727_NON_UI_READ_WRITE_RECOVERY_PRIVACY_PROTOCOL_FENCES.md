# ARK AI — Run727 Non-UI Protocol Custody Hardening (FREE-ONLY)

## Basis and scope

- **Work-basis:** Run726 checkpoint HEAD `6d5e8993d4e26f31e48fd447f91bc780e32d78b8` on `research/jarvis-foundations`, Draft PR #8; initial exact-head CI [#42548984190](https://github.com/Iam-2squared/ark-ai/actions/runs/42548984190) **GREEN 6/6** across Windows/Ubuntu × Python 3.11–3.13.
- **Scope:** In-process, synthetic/offline input-contract integrity only. Existing V1/V2/Local UI/Launcher frozen boundaries, V3 Contract 1 and protected V2 evaluations are untouched. Draft PR #5/#9 untouched and unmerged; **UI development remains paused**.
- **No new capability grants:** A local digest does not authenticate consent, actor identity, trusted time, provenance, immutable custody, cross-store atomicity, crash outcome, tool execution, or exactly-once effects. No real backend, payment, GPU, Candidate/training or device access.

## Package A — Detached READ input binding

- [Production `61a3486`](https://github.com/Iam-2squared/ark-ai/commit/61a3486dfc1eef72e769cd173b572ee07adf4a1b) pins `_DOMAIN`, `_SHA`, and `_STEP` to import-time identities inside the existing early denial function. It prevents locally redefined digest domains and widened regexes from being silently treated as the reviewed input-to-receipt binding.
- [Five synthetic tests `5f99720`](https://github.com/Iam-2squared/ark-ai/commit/5f99720523e32304cbc7af19c7335657445eae59) cover three protocol mutations, an equal-value but different object identity for the domain, and the original four false-only capability flags.
- This is not independently signed expected-input custody. Disconnected recovered receipts remain diagnostic.

## Package B — Persistent disconnected WRITE slot identity

- [Production `dfcf866`](https://github.com/Iam-2squared/ark-ai/commit/dfcf866f9c3e95c495b759bbd520650ec81a12e7) pins original SHA-256 and JSON serialization, digest domain, SQLite schema DDL, and four identifier regexes. The constructor/authority fence now runs before `derive_disconnected_write_slot_id` parses claims and around each private digest serialization/callback.
- [34 synthetic tests `a70c8b9`](https://github.com/Iam-2squared/ark-ai/commit/a70c8b999077fd905495ca301b4f1dbd2d4227d2) cover six contract mutations across derive/genesis/bootstrap/inspect/reserve, poisoned SHA/JSON callback zero-call assertions, equal-value domain replacement and unchanged denial-only reservation result.
- Existing bounded capacity, write-once SQLite uniqueness, crash/COMMIT-UNKNOWN caveats and disconnected-only semantics remain unchanged. No external WRITE dispatch, authenticated authorization, trusted clock, or replay grant.

## Package C — Planner READ recovery state contract

- [Production `21e18da`](https://github.com/Iam-2squared/ark-ai/commit/21e18daf261e1e8ea51da22106836918840c0433) pins SHA-256/JSON implementation identities, digest domain, request/step/SHA regexes and the reviewed operation/state sets in the existing pre-input contract assertion.
- [Inherited test adjustment `3c98dfe`](https://github.com/Iam-2squared/ark-ai/commit/3c98dfedbfb292f2c8b89bc6dd7a48290db11bd4) now requires a substituted SHA callback **never execute**, reflecting earlier fail-closed rejection rather than weakening the graph-carrier check.
- [Ten synthetic tests `b30e35e`](https://github.com/Iam-2squared/ark-ai/commit/b30e35e48e65e22b665c05c94df007382add2bf2) cover six protocol changes, equal-value domain rebinding, poisoned SHA/JSON zero-callback handling, and the unchanged `READY_MOCK_ONLY`/no-replay surface.
- This does not implement tool dispatch, inspect real tool outputs, or allow uncertain READ retries.

## Package D — Personal Context revocation continuity

- [Production `c08c340`](https://github.com/Iam-2squared/ark-ai/commit/c08c340ecf916efeacfd087fa154198a7ff82709) makes the digest-domain byte literal an explicit unchanged `_DOMAIN` and pins its identity, witness/row digest regexes and SQLite integer timestamp bound within the existing early privacy fence.
- [Ten synthetic tests `57c5444`](https://github.com/Iam-2squared/ark-ai/commit/57c544400af14f4952f0cfa413db99ced5c813ed) cover four protocol mutations with/without retained witnesses, zero private SQLite `_connect` access, equal-value domain rebinding and unchanged prefix recheck. No erasure, sharing or privacy consent action.

## Test and CI evidence

The changes above add **59 parameter-expanded synthetic tests** (5 + 34 + 10 + 10) plus one inherited callback expectation correction, across four production modules, four new test modules and one prior test module. These are **authored tests, not yet verified PASS**. No local repository test execution or physical-PC review occurred, and no equivalent workflow was manually re-run. At report preparation the GitHub Actions run on source/test HEAD `57c544400af14f4952f0cfa413db99ced5c813ed`, [#42552827808](https://github.com/Iam-2squared/ark-ai/actions/runs/42552827808), was **QUEUED**; earlier package runs were **IN PROGRESS / QUEUED**. Exact final checkpoint-result-head Windows/Ubuntu six-job CI is **NOT VERIFIED**. Preserve any real failure logs and correct without relaxing the denial contracts.

## Next plan / 今後の方針

1. Resolve latest six-job CI; inspect real test, lint and Windows logs before any semantics-preserving correction. Do not inherit GREEN from older HEADs.
2. Memory: manual-only COMMIT-UNKNOWN, coherent cross-scope row/event snapshots and CAS/ABA witnesses, without automatic replay.
3. Planner: independent retained READ input SHA custody and crash-safe publication, terminal DAG and unknown-result propagation.
4. Registry/PermissionGate/occurrence/audit: connect to the **disconnected mock executor only** after exact-head GREEN evidence at lower layers. No live WRITE, no issuance of real approvals.
5. Personal Context privacy retention/revocation, proactive scheduler, observation fixtures and V3 **free-only** path/identity/approval guards. Maintain frozen gates and paused UI.

# ARK AI — Run715: READ dependency custody and coherent Memory event high-water

**Scope:** FREE-ONLY, non-UI, reversible diagnostic foundations on [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), `research/jarvis-foundations`. Exact starting work-basis HEAD `1cb0e4fcb8756c509ab493083d87abac493af618`. No Candidate, training, paid compute, API, live tool, private export, UI development, contract/evaluation reopening or main merge. All effects are synthetic fixtures.

## A — original detached READ reviewer dependencies

- Production [`48b6620c`](https://github.com/Iam-2squared/ark-ai/commit/48b6620c320a21c656c0d4f4d836b7d467f43e44) pins import-time `hashlib.sha256`, `json.dumps` and the existing full topological/recovered journal review function in the opt-in exact-input binding reviewer. Before processing the caller's expected input manifest, the reviewer rejects a substituted dependency, including an apparent equivalent that would run its own callback. Subsequent report-epoch checks also require originals.
- Tests [`3917bbde`](https://github.com/Iam-2squared/ark-ai/commit/3917bbde2a8634e1510f82b2a4f917dae5bfd28b) add **4 parameterized/healthy cases**: three independently replaced dependency callbacks denied without execution and one matching original denial-only review.
- Early test CI [#42496766625](https://github.com/Iam-2squared/ark-ai/actions/runs/42496766625) failed in Ubuntu with **2 fixture-setup failures**: construction of the synthetic receipt after monkeypatching global SHA/JSON executed the hostile callback from the journal's `_chain`, *outside* the guarded reviewer. Failure was confirmed in the actual Ubuntu 3.11 job log, not misreported as a production failure. Test-only [`3ace97a4`](https://github.com/Iam-2squared/ark-ai/commit/3ace97a4f83d00f45c702bee24ea57a57165120c) constructs synthetic evidence *before* applying the poison monkeypatch; it does not weaken any rejection.
- No READ execution is attested; hashes, witness and expected-input manifest remain caller-controlled, not independently authenticated. No real backend dispatch or automatic replay is authorized.

## B — global Memory append invariants in one WAL read snapshot

- Production [`9004cb4c`](https://github.com/Iam-2squared/ark-ai/commit/9004cb4c703c84909da16e915c979e3f6a92a4e7) closes a gap in `review_retained_coherent_memory`: it now checks **global dense event IDs** across all owners, and in the **same pinned SQLite read transaction** checks the `sqlite_sequence` AUTOINCREMENT high-water against the event tail (including the empty-history case). Before this, an unretained newer suffix event deleted with its live row could leave a locally plausible retained prefix.
- Tests [`6c5b76df`](https://github.com/Iam-2squared/ark-ai/commit/6c5b76dfcc99d2382e11e2d54403f09b85212709) add **4 disposable SQLite cases**: missing foreign-owner event in a new suffix, erased foreign-owner tail, erased only event after genesis, and valid foreign append. Test-only [`eebce350`](https://github.com/Iam-2squared/ark-ai/commit/eebce350cf94c77956eeeca1853430e147853b19) explicitly closes each SQLite connection to avoid Windows locked-handle cleanup failure.
- Historical rewrite of *both* event rows and `sqlite_sequence`, or forged retained witnesses, still cannot be authenticated by this local check. This is a **read-only diagnostic**, not permission for mutation, COMMIT-UNKNOWN retry, disclosure, consent or external execution.
- **Open follow-up:** the coherent reviewer currently compares live owner/namespace/revision to event lifecycles, while its current full alignment hash is compared to the old hash only for an unchanged event count. A synthetic rewrite of an existing live row's `created_at_ms` or `updated_at_ms`, followed by a legal *other-owner* event append, deserves explicit per-lifecycle timestamp reconciliation even when no optional retained-row witness was supplied. This is not claimed closed in Run715.

## CI and boundaries

- Previous exact work-basis [#42492892993](https://github.com/Iam-2squared/ark-ai/actions/runs/42492892993) **6/6 GREEN** (Ubuntu/Windows × Python 3.11–3.13).
- Intermediate source CI [#42496568801](https://github.com/Iam-2squared/ark-ai/actions/runs/42496568801) and [#42496673840](https://github.com/Iam-2squared/ark-ai/actions/runs/42496673840) launched. Early A test CI [#42496766625](https://github.com/Iam-2squared/ark-ai/actions/runs/42496766625) was **FAIL** on the now-corrected fixture setup. Corrected A test CI [#42496984172](https://github.com/Iam-2squared/ark-ai/actions/runs/42496984172) and corrected B handle CI [#42497008363](https://github.com/Iam-2squared/ark-ai/actions/runs/42497008363) had **no verified 6/6 final conclusion** during preparation. The report/status write creates additional exact-head CI; do not extrapolate from earlier heads.
- No local full pytest/Ruff and no physical-PC/GGUF verification were executed. **8 new cases authored, not certified all-environment PASS on the newest HEAD** until actual matching CI finishes.
- PR #5 remains frozen Draft/unmerged with `docs/v3/PRE_PAID_COMPUTE_GATE.md` unchanged, PR #9 Draft/unmerged and UI development paused, PR #8 Draft/unmerged. V1/V2/Local UI/Launcher frozen contracts/evidence untouched. All no-cost, legal/privacy, hardware, credential, promotion, evaluation and approval barriers remain closed.

## Next plan / 今後の方針

1. Confirm exact corrected HEAD six-job CI using real logs. Fix only evidenced failures; do not duplicate workflows.
2. Close coherent live-row/event creation/update-time matching, preserving nonmonotonic caller-clock semantics and the single-WAL-snapshot guarantee; add cross-owner synthetic corruption fixtures.
3. Strengthen caller-origin/custody of Planner per-step input manifests and terminal/UNKNOWN restart observations without claiming actual tool invocation.
4. Continue Memory generation CAS/ABA/COMMIT-UNKNOWN manual review and disconnected registry/permission/occurrence/audit-before-action integrations only after exact-head GREEN. Audit Action Audit O(N) safety/performance without weakening history checks.
5. Keep PR #5/#8/#9 Draft/unmerged, no UI, real tools, spending, frozen evaluation, Candidate promotion or main merge.

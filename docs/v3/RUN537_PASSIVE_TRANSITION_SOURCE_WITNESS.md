# Run537 — passive V3 source-report identity and callback custody

## Scope and exact working basis

Draft PR #5, `research/v3-learning-evaluation`, work-basis HEAD `410b2361202159c5f4e3877e9d453b071cb623d2`.
All work is disconnected, read-only analysis of caller-supplied **UNAPPROVED** synthetic V3 execution snapshots. This record neither performs nor authorizes preflight, training, Candidate generation, export, protected V2 evaluation, promotion, GPU allocation or paid services. The frozen Experiment 001 and evaluation contracts remain unchanged; no actual file/model identity or human signoff is asserted.

Changes:

- `src/ark/learning/offline_readiness_transition.py` at source commit `8f92281f6ef879441cd83e52066db78aafb74947` independently recomputes each shape callback's canonical snapshot SHA-256 and denies a forged, exact-class callback result with an unrelated digest. It retains the original shape-result field carriers through downstream report construction, denial getters and the final source comparison.
- The returned passive transition report now rejects value-equal **replacement objects**, not just different field values. Explicitly denied authority property descriptors remain pinned and no callback is permitted to rebind an earlier descriptor.
- `tests/v3/test_passive_transition_source_epoch_run537.py` at test commit `7a967574ee0e6ec34f1d8242a29f2ea7f1aa472e` adds **6 authored pytest cases**: replacement of equal SHA/path carriers, fabricated source-report digest, final-denial mutation of prior source report or equal tuple clone, and unchanged non-authorizing behavior.

## Evidence and limits

[Exact source+tests GitHub Actions run 41340581249](https://github.com/Iam-2squared/ark-ai/actions/runs/41340581249), HEAD `7a967574ee0e6ec34f1d8242a29f2ea7f1aa472e`: **6/6 GREEN**, six individually inspected Python/OS matrix jobs. This is not a separately executed local pytest run. This documentation commit will create another HEAD and requires its own exact-head CI before being described as GREEN.

A canonical SHA-256 computed over caller-provided JSON is **local consistency only**. It does not authenticate that supplied content reflects real artifacts, a real human review, an immutable upstream model revision, toolchain bytes, a consent or spending grant, or a trusted external source. No user approval is inferred from a disappearance of placeholders. No self-authorizing Candidate or protected evaluation path exists here.

## Next

Keep V3 passive and free-only. Reconcile real byte/path/runtime/provenance evidence only when legitimately available with independent custody. Maintain unresolved human review, provider-side billing guard and user approval as hard blockers for potentially billable execution.

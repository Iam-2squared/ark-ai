# Run520 — Direct paired V3 validation exact-carrier comparison

**Draft PR #5**, `research/v3-learning-evaluation`. Initial work basis `a5ef1aaa4dd840afd5916fa9fea32ccb83cfdc9a`. This package changes `src/ark/learning/validation.py` at `033f6858217864a0bd4ea6b2616fb19439ebc26c` and adds `tests/v3/test_validation_exact_epoch_run520.py`, combined source+test HEAD `332b41466aef0d4d909bcc2b0d52e4bbc3b5a7db`.

## Direct validation hardening

- Paired V3 validation-only reports now require exact built-in report/case/tuple/string/bool types, exactly 30 unique cases, bounded individual field sizes and a per-report aggregate text budget.
- A direct comparison pins current+candidate input identities before their potentially replaced `validate` callbacks. It rechecks exact report fields, case identities and primitive result carriers after each validation phase and before returning the same prior validation-only summary. Equal-value replacement of a frozen case tuple and reflected mutation of a candidate case cannot be silently accepted.
- The existing legitimate comparison schema and historical V2 denial fields are unchanged: `historical_v2_opened=False`, `promotion_decision=NOT_AUTHORIZED_FROM_VALIDATION`. No real model, scorer, protected V2 final evaluation, Candidate, promotion or external side effect is invoked.
- Added **18 parametrized pytest cases** covering 30-case compatibility, type/budget misuse, subclass carriers, wrong paired role, mutation during validation callbacks and detached denial-only semantics. The tests are authored definitions, not a claim of independently executed local tests.

## CI and bounds

- [Source+test CI run 41274600892](https://github.com/Iam-2squared/ark-ai/actions/runs/41274600892): **IN PROGRESS** at this document's creation. Do not claim all environments GREEN until every exact-HEAD job succeeds.
- Earlier separate mock-gate package documented at [RUN520_MOCK_EVIDENCE_EPOCH.md](RUN520_MOCK_EVIDENCE_EPOCH.md) and validated at [CI 41274334811](https://github.com/Iam-2squared/ark-ai/actions/runs/41274334811): 6/6 GREEN on its earlier source+test head. That is not automatically evidence for this later direct-comparison code.
- No independent complete local checkout pytest/Ruff, actual model download or GPU execution. These are free-only synthetic guards and retain the frozen Contract 1, V1/V2/Local UI/Launcher evidence, exact V2 scorer/gate, original approval boundaries and Draft/unmerged PR state.

## Next

Resolve exact-head CI and, if needed, correct only demonstrated errors. Continue model byte/path/reproducibility validation while the real 120/30 human-review and licensing decisions, immutable upstream revision and file hashes, device/provider identity, protected V2 opening and any monetary authorization remain explicitly blocked. No main merge.

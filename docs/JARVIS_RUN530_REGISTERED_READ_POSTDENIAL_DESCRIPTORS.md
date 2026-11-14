# Run530 — detached registered READ batch: final-child authority custody

**Scope:** PR #8 Draft/unmerged, synthetic registered READ evidence only. Source work basis `28d4a26b5ed602ec50f2a8cfee88ddfcd72e26af`. Source HEAD `42af1a3d0880e9ea7ebe855e6ba4d6b4e442f6b8`. Focused-test HEAD `b42f5543fba711eb7f3d006b532b48858d56919e`.

## Last-callback failure mode

The read-only aggregate `review_registered_batch_receipt_set` audits every synthetic DAG child, validates all digest-bound receipts and verifies result denial flags. It then **runs the child review one more time** to guard against post-denial SQLite/fixture changes. Because this final child read can itself run callbacks, a caller-controlled child callback could replace `RegisteredBatchSetReview.backend_dispatched` *after the earlier result denial checks* but before return.

The unmodified aggregator checked result fields after its last pass, but did not independently verify the originally observed authority descriptors were still the same objects. Therefore, replacing the class property with an equivalent-looking `False` descriptor could silently change the result's provenance, or with a `True` descriptor could make its returned result report a power the aggregator never granted.

## Reversible hardening

1. Pin all five `RegisteredBatchSetReview` authority descriptors at result construction, then inspect their identity in every `stable_result()` verification.
2. After the final child pass, explicitly run another bounded denial check for each result flag; preserve scalar identity and caller plan/evidence epochs after each property callback.
3. Continue returning a report with all flags literal `False` and no real backend dispatch, WRITE, execution, dependency-completion proof, or automatic replay capability.
4. Add **2 synthetic pytest cases** to `tests/test_registered_batch_receipt_set_run524.py`: a child callback that replaces the parent flag with either another `False` property or a `True` property at the final third child pass. Both must be rejected, and the mock backend must not execute or consume permission tokens.

This is not cross-database atomicity; several independent local READ journal transactions cannot prove a shared commit boundary or authenticated historical tool execution. The retained inputs are synthetic, without owner consent or trusted time. No main merge, paid action, external tool, model, protected evaluation, frozen contract change, or irreversible operation is authorized.

## Validation

Source and tests have been committed through normal GitHub Contents writes, not force-pushed. Their exact-head CI must be checked independently. This record itself has a distinct documentation HEAD/CI, which must not inherit an earlier GREEN.

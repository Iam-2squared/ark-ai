# Run540 — unapproved snapshot inventory custody in the V3 shape reviewer

**Free-only, passive, non-executing.** A syntactically plausible snapshot is never a validated model identity, approved dataset, license, human-review decision, spend ceiling, Candidate authorization, or protected V2 opening.

## Saved work and exact boundaries

- Work-basis PR #5 HEAD: `40b613518b3df515b448e224932babc7f1bfd2ba`.
- Shape review source change: `daa44f33622d5eb736f3a0f15690f89319461beb`.
- New test file: `419017c6db6f24b48954699bb878ac25c5a0ce2a`. Its initial CI [41353870025](https://github.com/Iam-2squared/ark-ai/actions/runs/41353870025) was **6/6 FAIL** because Ruff I001 required the two `ark.learning` imports to be ordered alphabetically; no core behavior failure was observed because lint failed first.
- Minimal import-only fix: `c2b15ab0b921d7d9d8dced86c0dabf2c7fed6b8e`. No frozen gate or rejection rule was relaxed.
- PR #5 remains Draft, unmerged and separate from V1/V2 historical evidence.

## Invariant and security rationale

A locally replaceable `inventory_unapproved_v3_readiness` callback may return the exact `OfflineReadinessInventory` class with a *correct snapshot SHA-256* but invent an unresolved path tuple. The pre-existing shape reviewer checked path count and hashes but relied on the callback's path classification. The shape reviewer now independently classifies the literal fields listed in `_SECTIONS` and the tokenizer revision alias, including base `UNRESOLVED` or `USER_APPROVAL_REQUIRED` propagation. It requires an exact sorted tuple match. This is a **syntactic** source-integrity check only.

A second epoch check pins the original inventory's exact field carriers and its four non-authorizing permission-property descriptors across subsequent shape work, denial callbacks and final return. It rejects reflective field replacement, including equal-valued new tuple carriers, and source report authority claims.

**14 newly authored parametrized pytest variants:** one normal template/tokenizer-alias check, six correct-digest but forged-path fixtures (including absent/duplicate/reversed/invented), four late authority-property grants, and three later path/count carrier mutations. Test count is authored cases, not independently executed local pytest PASS.

## Validation still required

The corrected source/test HEAD requires its own GitHub Actions six-environment read-back. The failed first test HEAD never constitutes a PASS. No external GPU, real HF artifact retrieval, training step, paid API, adapter generation, Candidate promotion, dataset review authorization or frozen V2 final evaluation was attempted. The immutable Hub commit, file hashes, genuine dataset approvals and billing authority remain unresolved.

**Next:** verify CI on the corrected test HEAD, further audit independent model/tool byte provenance and readiness source signatures only with free passive fixtures, and preserve Contract 1 and all approval gates.

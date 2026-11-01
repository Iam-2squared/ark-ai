# V3 Run521 — ordered paired-validation evidence (free-only)

## Basis and isolated change

[Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5),
`research/v3-learning-evaluation`, began this invocation at
`f87800744f742818dd93e9089a8f69375283ee2a`.
The frozen V3 Contract and protected V2 final-evaluation boundary are
unchanged. No real Current/Candidate runtimes, external GPU, model weights,
Adapter, protected evaluation, human scoring or provider spending is used.

The direct comparison `compare_validation()` previously compared dictionary
key views, which preserve *set membership* but not source order. The detached
byte-for-byte comparator already required the Current and Candidate case
IDs to appear in the exact same sequence. This mismatch could let a reordered
set of 30 synthetic cases pass the direct comparator and then fail the
subsequent detached evidence check.

Source `src/ark/learning/validation.py` was changed at
`f39781fbb18bb5e30fcc9f3bdcd41fdf324df850` to require
`tuple(old) == tuple(new)` after both exact reports validate and after the
existing identical-set check. This is a fail-closed strengthening that aligns
the direct and independently recomputed comparison; it does not open V2,
change the frozen scoring policy, create a Candidate, or allow promotion.

New tests `tests/v3/test_validation_order_contract_run521.py` at exact
source+test HEAD `97d6719359ed919f5cc0ca22e7d21dd86466fb59`
contain **8 authored cases**: five swaps with unchanged sets, one
same-order distinct equal case carriers, one shared unusual/reversed
ordering, and one genuinely missing identifier. No sorted global
canonical order is imposed; two reports using the *same* arbitrary order
remain comparable, preserving existing valid semantics.

## Verification (exact head)

- [Source CI 41278330036](https://github.com/Iam-2squared/ark-ai/actions/runs/41278330036)
  for `f39781fbb18bb5e30fcc9f3bdcd41fdf324df850`:
  **6/6 GREEN, SUCCESS**.
- [Source+test CI 41278352619](https://github.com/Iam-2squared/ark-ai/actions/runs/41278352619)
  for `97d6719359ed919f5cc0ca22e7d21dd86466fb59`:
  **6/6 GREEN, SUCCESS**, including Ubuntu and Windows on Python
  3.11, 3.12 and 3.13.
- No independent local pytest/Ruff checkout was run. Authored cases
  are not local PASS-count evidence.

All GitHub source/test writes used the normal Contents API after observing
the branch HEAD and fetched current file SHA. No raw object/ref update,
force-push, frozen-contract modification, review decision, Candidate
promotion or main merge occurred.

## Boundaries / future work

Exact 30-case order protects local fixture alignment but cannot authenticate
the historical model, dataset, scorer, runtime, prompts, human consent or
the trustworthiness of retained bytes. Real V3 is still **NOT_PASSED**,
requiring the independently verified immutable upstream/base/tokenizer/file
hash identities, human-reviewed rights/provenance/contamination decisions,
hardware and runtime identity, explicit spending authorization/cap, and the
protected V2 gate.

Continue non-billable, reversible path/identity/reproducibility validation
and cross-check direct vs detached mock comparisons. Real Candidate generation,
protected V2 evaluation, and promotion stay blocked pending explicit
authorization and frozen-gate satisfaction.

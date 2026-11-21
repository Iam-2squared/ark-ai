# Run1077 — V3 authorization-packet stat-predicate custody

## Exact basis

- Target: gated Draft PR #5, `research/v3-learning-evaluation`.
- Exact parent HEAD: `2ddc32a69dd32541497373ac76be2c1db332f88f`.
- Child branch: `research/run1077-v3-auth-stat-predicate-custody`.
- Source commit: `04f490d760474d86f7c3dd2e7c1bca7db72163ed`.
- Regression commit: `d5460bbbd2eeb8e2057223cc410aae475394f997`.

## Finding

The review-only authorization-packet path guard pinned the Windows reparse attribute mask but did not pin the import-original `stat` module or the `S_ISLNK` / `S_ISREG` predicates used by path admission and post-write verification. A rebound predicate could therefore change the meaning of the metadata checks without changing the already-pinned mask.

## Change

- Pin the import-original `stat` module and exact `S_ISLNK` / `S_ISREG` function objects.
- Reject module or predicate substitution before ancestor `lstat`, final-leaf inspection, or packet open.
- Recheck policy after metadata accessors and use the pinned predicates for mode classification.
- Preserve the existing packet schema, no-follow admission, exclusive-create behavior, post-write byte/identity verification, and all authorization denials.

## Regression coverage

Five synthetic regressions cover module rebinding, each mode-predicate replacement before filesystem inspection, and metadata accessors that rebind a predicate during classification. No privileged junction or real authorization packet is created.

## Limits and frozen boundaries

This is local in-process dependency-identity hardening, not a Python sandbox, atomic directory-handle custody, hostile filesystem-writer defense, approval, billing evidence, preflight authorization, Candidate authorization, or execution permission. No GPU, model, tokenizer, converter, quantizer, Candidate, training, protected V2 evaluation, promotion, frozen Contract 1, or UI branch is changed.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. PR #5 remains OPEN/DRAFT/UNMERGED; V3 remains NOT_PASSED.

A separate documentation-only copy of this Run1077 note was written to the default branch by an earlier Contents API call that omitted the branch parameter; no source code or frozen contract was changed on main.


## CI repair history

- Initial exact child HEAD `3c91b800dd8af6150cdce0d1ef6b206340233d2f`: run `44932114065` failed all six matrix jobs at Ruff `B009` before pytest. The two constant-name `getattr(info, "st_mode")` calls were replaced with direct attribute access while retaining the policy recheck after metadata access.
- The repaired exact head requires a fresh CI run; the failed run is not a PASS.

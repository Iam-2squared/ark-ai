# V3 Run1252 — bounded dataset CLI JSON ingress

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: gated Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent work-basis HEAD: `ce7a3498472ef1fbcfc36496817bf3c10f6d18f2`.
- Child branch: `research/run1252-v3-bounded-dataset-cli-ingress`.
- Scope is limited to the offline dataset CLI's local candidates/flags/decisions file reader. Contract 1, dataset schema, approval, provenance, contamination, split, reproducibility and evaluation semantics are unchanged.

## Finding and repair

The CLI used `Path.read_text()` with no byte ceiling before parsing candidates, flags or decisions. A large local file could therefore allocate unbounded input before the strict duplicate-key/non-finite-number JSON parser ran. Deeply nested JSON also reached the parser without a CLI-specific structural budget.

The CLI now:

- reads at most 64 MiB + 1 byte and rejects inputs over the 64 MiB operational ceiling before decoding/parsing;
- scans JSON structural nesting outside quoted/escaped strings and rejects depth above 64;
- decodes strict UTF-8 and translates parser recursion exhaustion into a bounded input error;
- applies the same reader to candidates, flags and decisions.

These are local CLI resource limits, not changes to the frozen schema or the exact 120/30 experiment recipe. Canonical dataset bytes and downstream parser semantics remain unchanged for inputs within the bounds.

## Regression coverage

Synthetic local files cover the exact byte boundary, oversize rejection before parser invocation for all three input classes, bracket characters inside JSON strings, nesting overflow before parser invocation, invalid UTF-8 and parser recursion failure.

## Evidence boundary

No dataset is approved by this change. It does not create human-review decisions, establish provenance/rights/independence, start real training, load weights, generate a Candidate, open protected V2 evaluation or authorize promotion. No network, external compute, paid API/service, credential or hardware is used.

Initial exact-head CI run [45335842416](https://github.com/Iam-2squared/ark-ai/actions/runs/45335842416) failed at Ruff E501 on the new test's function signature, before pytest ran. The signature was wrapped and the escaped-quote JSON fixture corrected in the follow-up test commit. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI for the corrected head is required; no pytest/Ruff PASS is claimed. PR #5 remains Draft/unmerged under its controlling gate. PR #8 and PR #9 remain untouched; UI/frontend work remains paused. ARK/JARVIS remains NOT_PASSED.

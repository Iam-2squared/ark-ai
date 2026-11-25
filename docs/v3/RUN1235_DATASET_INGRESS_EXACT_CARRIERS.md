# Run1235 — exact-carrier admission at the V3 dataset boundary

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: gated Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent HEAD: `29c4b33098798675d0e1d69e97ddc7a56591fd16`.
- Child branch: `research/run1235-dataset-ingress-exact-carriers`.
- Scope is limited to the V3 dataset-builder and contamination-review input boundary. No Contract 1, dataset schema, source rights, approval, split, contamination, or reproducibility rule is changed.

## Change

- Require an exact built-in list, exact `LearningCandidate` objects, and an exact `ContaminationGuard` before sorting, identifier hashing, or policy callbacks.
- Read candidate identifiers through `object.__getattribute__` and reject string subclasses before sorting or `strip()`.
- Validate every candidate text field as an exact built-in string before normalization, membership checks, or timestamp parsing.
- Pin and invoke the original candidate validator and contamination-review method rather than instance-shadowable methods.
- Require the guard's protected inputs, targets and reference markers to be exact immutable tuples of exact strings.
- Preserve deterministic candidate-ID ordering, duplicate-ID rejection, existing per-row rejection behavior for ordinary malformed fields, and canonical dataset bytes.

## Regression coverage

Synthetic tests cover list/candidate/guard subclasses, callback-capable string and tuple subclasses, direct contamination-review calls with mutated candidate text, and deterministic output under reversed input order. No real personal data or training examples are used.

## Evidence boundary

This is local input-integrity hardening only. It does not establish provenance, rights, independent human approval, semantic contamination absence, real training, Candidate weights, V2 evaluation or promotion. No paid/external compute, credentials, hardware, protected evaluation opening, Candidate generation, main merge, frozen-contract change or UI work is performed. PR #5 remains Draft/unmerged and its hard gates remain closed. ARK/JARVIS remains NOT_PASSED.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local test or CI result is claimed here.

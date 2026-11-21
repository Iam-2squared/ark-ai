# Run549 — unapproved V3 packet delta ASCII-space/recheck compatibility

Status: **PASSIVE / DRAFT / NOT_PASSED**. No real model, external GPU,
Candidate output, authorized preflight, protected V2 evaluation or user spend.

## Verified defect and change

The field-path producer `_leaf_bytes` in
`src/ark/learning/authorization_packet_delta_review.py` deliberately
preserves literal ASCII U+0020 spaces. It escapes ambiguous delimiters,
invisible Unicode and controls. The detached rechecker `_fields` in
`src/ark/learning/authorization_packet_delta_recheck.py` previously
rejected all ordinals below 33, including ordinary space U+0020, so a
syntactically accepted value-free path could be rejected as a retained
receipt. This was a **producer/consumer inconsistency**, not an
authorization or training bypass.

The Run549 source change at `a3617a99d050fc70f3e2538c5f8f770ca255bf1b`
changes the detached ASCII boundary from `ord(ch) < 33` to
`ord(ch) < 32`. All ASCII controls U+0000..U+001F, DEL and non-ASCII
unescaped characters are still refused. No existing digests or packet
authorization rules changed.

Test commit `f270ee9af0713a52f1c029d4ab48e0e044f14601` adds
`tests/v3/test_detached_packet_delta_ascii_spaces_run549.py` with
**14 authored parameter-expanded pytest cases**. They exercise paths
with ordinary/leading/trailing/repeated ASCII spaces, literal tilde escape,
and rejection of raw tabs, newlines, NUL, control bytes, DEL and non-ASCII
spaces. An escaped nonbreaking space remains permitted by the rechecker.
The test uses passive packets/paths only and does not open any real gate.

## Exact-head evidence

GitHub Actions run
[41395773259](https://github.com/Iam-2squared/ark-ai/actions/runs/41395773259)
for exact source-and-test HEAD
`f270ee9af0713a52f1c029d4ab48e0e044f14601`:
**6/6 GREEN**, individually checked Ubuntu/Windows Python 3.11–3.13.
The future documentation HEAD is distinct and must not inherit that
exact-HEAD certification without its own CI result.

## Non-authorization, outstanding gates

This is a passive presentation/recheck consistency correction, not proof of
packet provenance, independent custody, human review, immutable model bytes,
trusted hardware identity, legal permission, billing cap or readiness to train.
PR #5 remains Draft/unmerged. Its frozen V3 Contract, V2 final-evaluation
boundary, main branch, Candidate and paid-compute hard stops remain unchanged.

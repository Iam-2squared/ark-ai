# Run531 — unapproved V3 packet field-path change review (free-only)

**Branch:** \`research/v3-learning-evaluation\`, Draft PR #5, unmerged. **Source work basis:** \`74dc4ab7b3ceece22a6a7ec00b4ec5b69f877995\`. Source commit \`396a457fbfcbbe01c242f84bcdbe77a69a91f83f\`; source + focused tests \`260a9c75519f26404d6ee3fd8db5dadeb26e099d\`.

## Scope and concrete behavior

\`src/ark/learning/authorization_packet_delta_review.py\` provides \`review_unapproved_packet_delta\`. Given **two unapproved execution-snapshot mappings**, two separately saved local review packet paths, and independently retained SHA-256 digests, it:

1. Pins both exact JSON source trees and verifies each corresponding on-disk packet using the existing restart-safe, read-only packet-file verifier.
2. Rebuilds both unapproved packets with the already validated V3 preflight packet builder, not a caller-supplied unverified packet dict.
3. Computes a deterministic, bounded, **value-free field-path change set**. Leaf comparisons use canonical JSON bytes so Python equality does not equate \`True\` with \`1\`. Lists are indexed by position; the result contains field paths only.
4. Hashes the two retained file digests and change paths under a domain separator; revalidates both original local files and source trees after comparison.
5. Returns a diagnostic \`ReviewPacketDelta\` with four literal-denied authority properties: no external compute, Candidate, protected evaluation or main merge.

**Focused test file:** \`tests/v3/test_authorization_packet_delta_review_run531.py\` — ten pytest test functions with parametrized variants. Includes valid changed/unchanged packets, multiple identity changes, stale/invalid independent digests, source and file modification during review, actual approval flag, frozen method modification and false authority escalation.

All test snapshots and hashes are synthetic fixtures; they are not real model identities, reviewed datasets or paid authorizations. The comparison is **not** a claim of a fully race-free filesystem read, signature, reviewer identity or trusted time. It does not render the underlying V3 approval gate unnecessary. The Contract 1 hash/semantics and protected V2 suite remain frozen; no Candidate weights, model download, GPU, external compute, billing or main merge is involved.

## CI and follow-up

- Source-only workflow [41312749534](https://github.com/Iam-2squared/ark-ai/actions/runs/41312749534) succeeded on \`396a457fbfcbbe01c242f84bcdbe77a69a91f83f\`.
- Source + test workflow [41312847293](https://github.com/Iam-2squared/ark-ai/actions/runs/41312847293) was **IN PROGRESS** when this record was prepared; exact-head GREEN is **not yet certified**.
- The ten functions are **authored** tests, not independently observed local pytest PASS. No standalone local clone/pytest/Ruff: local GitHub DNS resolution was unavailable.

**Next:** resolve exact-head CI and correct any semantics-preserving lint/test mismatch. Keep PR #5 Draft, V3 NOT_PASSED and all payment/identity/human-review/contamination/reproducibility gates closed. Extend comparison only with independently verified packet identities rather than inferred approvals.

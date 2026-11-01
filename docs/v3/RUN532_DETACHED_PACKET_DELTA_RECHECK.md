# Run532 — Detached unapproved V3 packet-delta recheck (free-only)

This is a **validation-only**, **offline**, local-file review. No GPU, model,
real Candidate, protected V2 evaluation, payment, external API, human approval,
or main merge was requested or executed.

## Exact sources and test custody

- Initial work-basis PR #5 head: `4ef6bd63a88702235c46bdf417807648427333f9`.
- New `src/ark/learning/authorization_packet_delta_recheck.py`:
  `72e8288e782d239a6f462a234a31b1176f1116c2`.
- New `tests/v3/test_authorization_packet_delta_recheck_run532.py`:
  `d61fcd85e27474a2f7265e0620598b1ff2c79dfb`.
- Focused expectation-only correction (new test): `781b9ebb7ca05b569cb7298e17bdfc5189b89e12`.
- Exact original V3 Contract and experiment boundary unchanged. PR #5 remains Draft.

## Mechanism and bounded claims

`verify_detached_unapproved_packet_delta` accepts an independently retained
`ReviewPacketDelta`, two proposed-but-unapproved snapshots, two local packet
paths, and their separately retained byte hashes. It first validates the
**exact type and canonical shape** of all retained fields (including sorted,
unique, bounded field paths) and rechecks all four non-authority flags. It
then independently re-runs both saved-packet validations and the field-path-only
comparison, requiring exact report agreement. No changed JSON values are
returned; no approval is minted.

A reentrant denial getter which returns False but rewrites earlier receipt
fields or authority descriptors is rejected. A changed saved packet, swapped
hash, stale snapshot, false execution flag or mutated local witness is rejected.

**Limits:** This is not an authenticated reviewer decision, not a cryptographic
signature, not durable independent custody by itself, and not an atomic
filesystem snapshot. Matching SHA hashes do not prove a user gave consent.
Neither the existing frozen V2 gate nor V3 training authorization is opened.

## Focused cases and CI

**16 newly authored parametrized pytest cases** in eight test functions:
unchanged/changed review success (2), forged retained fields/paths (7),
modified saved files (2), stale proposal (1), swapped file hashes (1),
false-returning mutating authority getter (1), gained external-compute
authority (1), and wrong exact report type (1). These numbers describe
authored cases, not standalone local pytest PASS.

- V3 source-only CI `41317718083` on
  `72e8288e782d239a6f462a234a31b1176f1116c2`: **SUCCESS**.
- Initial tests CI `41317785868` on
  `d61fcd85e27474a2f7265e0620598b1ff2c79dfb`:
  **FAIL** (one new test omitted the legitimate
  `execution_core_sha256` changed path; all six matrices failed on that
  expectation). No source-gate relaxation.
- Corrected tests CI `41318024786` on
  `781b9ebb7ca05b569cb7298e17bdfc5189b89e12`:
  **6/6 GREEN** (Ubuntu/Windows Python 3.11/3.12/3.13).
- This technical-note commit, and a later project checkpoint, are distinct
  GitHub heads and require their own exact-head evidence.

## Continuing hard stops

PR #5 stays **Draft / NOT_PASSED**. Frozen Contract 1, V1/V2 and historical
final V2 evaluation remain untouched. Base/tokenizer byte identity, trusted
human decisions, reproducible measured runtime and a separately approved
enforceable provider-side cost cap are missing. Real training, paid compute,
Candidate output, promotion and main merge remain blocked.

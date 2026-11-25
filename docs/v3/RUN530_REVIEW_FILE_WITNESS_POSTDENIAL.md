# Run530 — detached V3 packet file: witness + post-denial custody

**Scope:** Draft PR #5, free-only read-only review. Source/test work basis `311eee866cf99cfd43077c684f7a3fe38cb1f946`. Source HEAD `b9f5282e86e6a7d7c1bec412433d150f5dc28227`; source + focused-test HEAD `9dc64697b2dc78cb82940804216b41a8e519f2ab`. The file review is not an authorization surface and does not run a model, GPU, tool or training step.

## Invariant closed

The previously added restart-safe `verify_local_authorization_packet_file` reopened its file after delegated verification, but returned the delegated witness without independently checking whether that same witness had been reflectively rewritten **during the final reopen or denial getters**. A caller must not interpret a mutated `LocalPacketBindingWitness` as the verified file's authority.

The wrapper now:

1. Pins the exact canonical parsed packet JSON tree, plus `execution_snapshot_sha256` and its internal `packet_sha256`, before delegating.
2. Checks the returned witness is the original exact carrier type, with exact-string hashes matching the independently retained full-file hash and parsed packet's two internal identities.
3. Rechecks all four non-authorizing flags (`external_compute_authorized`, `candidate_generation_authorized`, `protected_evaluation_authorized`, `main_merge_authorized`) are the literal `False`. It validates witness/packet/snapshot again **after** those getter callbacks.
4. Reopens the local packet a second time after the first denial pass, confirming the same bytes and file epoch, then repeats non-authority and identity checks before returning.
5. On any mismatch, raises `LocalPacketBindingRejected` rather than reporting an authorized outcome. The original file verifier and all frozen contracts remain unchanged.

The new focused file `tests/v3/test_authorization_packet_return_custody_run530.py` authors **7 cases**: valid detached review; late rewrite of each of three hash fields; false-valued denial getter that rewrites a hash; denial getter that mutates the source file; delegated verifier that mutates parsed JSON.

## Exact-head CI

- [Source+7 focused tests, run 41307890708](https://github.com/Iam-2squared/ark-ai/actions/runs/41307890708) completed **SUCCESS** on `9dc64697b2dc78cb82940804216b41a8e519f2ab`.
- An earlier [source-only run 41307814626](https://github.com/Iam-2squared/ark-ai/actions/runs/41307814626) completed **SUCCESS** on `b9f5282e86e6a7d7c1bec412433d150f5dc28227`.
- The 7 cases are authored cases, not a separately observed local pytest count; no independent local checkout or Ruff run is claimed. This document's own commit is distinct and requires separate exact-head CI.

## Remaining boundaries

These are local integrity checks, not authenticated human review, consent, packet ownership, immutable outside custody, trusted time, TOCTOU-free filesystem protection, provider-side cost cap or approval to spend. No Candidate/preflight, training, weight generation, protected V2 final evaluation, promotion or merge. PR #5 stays Draft and V3 stays **NOT_PASSED**. Work may continue on independent zero-cost lanes.

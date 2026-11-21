# Run522 — unambiguous V3 execution snapshot JSON

**Scope:** zero-cost, local file loading and fail-closed evidence parsing only. This is NOT an authorization, training preflight, Candidate generation, protected V2 opening, promotion, or external GPU action. PR #5 remains Draft/unmerged and V3 NOT_PASSED.

## Issue and implementation

The pre-existing `load_snapshot()` accepted bounded, finite, noncanonical JSON, but the standard parser silently kept the final occurrence of a duplicate object key. In authorization and evidence snapshots, `{"authorization": ..., "authorization": ...}` (or a duplicate nested `external_compute_authorized`) could obscure an earlier conflicting declaration before later validation, making the input's intended meaning ambiguous.

The local parser now installs `object_pairs_hook=_unique_snapshot_pairs`, rejecting repeated object member names **at any depth** before the parsed object can enter validation. The hook detects decoded-equivalent names as well as byte-for-byte repetitions. Existing byte-size and nesting limits, finite-number checks, separate scope approvals and Experiment 001 frozen contract remain unchanged. Valid noncanonical whitespace/key ordering remain accepted to preserve the prior loader contract.

Source commit: `56cdfb351cdcab6765b23977bba47e2e7db3dd87`. Eight new synthetic no-GPU cases at `tests/v3/test_execution_snapshot_duplicate_keys_run522.py` cover root duplicate authorization, nested duplicate permission, identity and dataset keys, escaped Unicode-equivalent duplicate name, a repeated object, valid noncanonical unique JSON, and the same member name in distinct objects. Final source+test HEAD: `25d5a9f1e817f03410216dc961b37bb197ccf027`. Its exact [CI 41281996563](https://github.com/Iam-2squared/ark-ai/actions/runs/41281996563) was QUEUED on first inspection; do not infer six-platform GREEN from prior revisions.

## Unchanged stops

No real HF base/tokenizer provenance or model file hash attested; no human-reviewed 120/30 dataset decision, verified physical runtime/device/GPU identities, spending ceiling/billing cap, explicit protected scorer approval, Candidate weights, or training. All remain unresolved or gated. This parser hardening makes one local serialization boundary less ambiguous; it does not establish owner permission, source authenticity, an immutable upstream Hub revision or runtime reproducibility.

**Next:** confirm final exact-HEAD CI, preserve strict independent input and artifact identity checks, and continue free-only path/bytes/authorization verification without opening any paid or frozen evaluation gate.

# Run1117 — ActionAudit immutable path fixture compatibility

## Exact basis

- Draft PR #292: `research/run1115-action-audit-path-seal`.
- Original implementation/test basis: `2ea4e50905cdedfac2f997051263061fb2967221`.
- Updated branch HEAD before this report: `e90ff8cf83d78762346f92b0b2a99e81b78f77f7`.
- Parent Draft PR #8 was at `c524935080889792b07f35c2eaefd5316c8dadb2) when last inspected; this child is isolated and unmerged pending exact-head CI and base reconciliation.

## Failure evidence

The prior exact-head run [45047099744](https://github.com/Iam-2squared/ark-ai/actions/runs/45047099744) reported 18 failed, 19,339 passed and 1 skipped on the inspected job. Failures were concentrated in inherited test fixtures that still performed ordinary `audit.path = ...` assignment or restored a value-equal but not identity-equal Path object after a reflective mutation.

The new audit implementation intentionally stores `path` and `_path_identity` in non-shadowable slots and rejects ordinary assignment/deletion. A fault-injection test must use `object.__setattr__` to simulate a reflective bypass, then restore the exact original slot object; ordinary assignment must continue to raise.

Some cross-store recovery reviewers intentionally normalize a lower-level audit failure to `incomplete or malformed synthetic recovery evidence`. Assertions now include that documented fail-closed wrapper rather than requiring a lower-level message to escape.

## Repair

- Keep the immutable slot-backed source path and exact identity validator unchanged.
- Migrate inherited fault-injection fixtures to explicit reflective mutation only where they intend to simulate an attacker bypassing `__setattr__`.
- Save and restore the actual `audit.path` slot object, not merely the constructor's value-equal input Path.
- Align parent-traversal, wrong-path-type and missing-source assertions with the earliest fail-closed validation boundary.
- Preserve the audit v1 schema, append/sequence behavior, read-only continuity semantics and manual-only recovery.

## Validation limits

The new exact-head run [45052463334](https://github.com/Iam-2squared/ark-ai/actions/runs/45052463334) was queued when this report was prepared. It is not a PASS. No SQLite schema migration, event identity change, trusted-clock change, dispatch permission, replay permission, external effect or cross-store atomicity claim is introduced. PR #292 and PR #8 remain Draft/unmerged; PR #5 remains gated Draft/unmerged; PR #9 is untouched and UI remains paused. No paid compute, Candidate generation/promotion, protected V2 evaluation, credentials, physical hardware or main merge. ARK/JARVIS remains NOT_PASSED.

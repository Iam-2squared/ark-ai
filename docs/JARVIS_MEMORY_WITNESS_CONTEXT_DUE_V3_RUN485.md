# Run485 — isolated Memory witness CAS, due/context post-COMMIT custody, and V3 JSON depth

**Scope:** Reversible, disconnected, zero-new-cost research branches. Evidence recorded 2026-10-31 JST. Neither branch has been merged. No authenticated clock, external ToolBackend, notification, GPU run, human approval or Candidate artifact has been generated.

## Evidence / exact files

| Lane | Files (GitHub blob SHA) | Scope |
|---|---|---|
| Memory | `src/ark/memory/disconnected_witness_ledger.py` `867f9f07b66812173d0d37b5da5205ee5bf8a2a9`; `tests/test_disconnected_memory_witness_ledger_run485.py` `bf5641bee4dc707fbd6424ba0b8c5db86365edd5` | Separate SQLite metadata-only append log, caller-held CAS witness, bounded scans, fail-closed DDL/rollback checks; 21 parameterized cases |
| Scheduler | `src/ark/agency/disconnected_due_reservation.py` `e33d2822e44852ac01f40630a438fc860f74a831`; `tests/test_due_witness_commit_custody_run485.py` `3087ddeb4519f151fa15b64a7c21eba041d5a9e4` | Receipt and witness validation after COMMIT, no automatic replay/notification; 5 cases |
| Personal Context | `src/ark/personal_context_replay_ledger.py` `85c462d2b7d3d6d2f75e792afb9f8af51c29ba0a`; `tests/test_context_replay_postcommit_custody_run485.py` `77a4b2f5ce4043c6033d61c3d500f09550b8a735` | Request replay witness source identity remains pinned across post-COMMIT receipt callback; 4 cases |
| V3 | PR #5 `src/ark/learning/run_manifest.py` `0c83fcc8518dbb710755fcb642794a5912b4a2a6`; `tests/v3/test_manifest_parser_failclosed_run484.py` `9d1d7af6f8a644e7ee4694b41fe2fe01d46757ad` | Platform-independent 128-level JSON container nesting cap, brackets inside strings ignored, no model/training; 8 new cases |

**Initial source basis:** PR #8 `7347f8a49e95161b36cdb34054119ccfd04c8ca5`, PR #5 `f5f4a87c6985a6c5c6992d7b14a35cc314a6741f`. PR #8 source/test after last normal-Contents fix `4ddc2f552c4ffef6503a639020c71c40173f9153`; PR #5 source/test `40c77ec0edfd2f7d268454407a8eaac2b84275e2`.

## CI / isolated failures

- PR #5 original Run484 `#1667` / Actions run `41101765576` **FAIL** on cross-Python/OS differences in JSON recursion acceptance. New V3 exact-source CI `#1671` / `41109698045` **six jobs SUCCESS** on Ubuntu and Windows, Python 3.11–3.13.
- PR #8 intermediate runs `#1672–#1677` were not green. Early failures were Ruff B904/E501 in new isolated witness fixture; after a Ruff repair, `#1678` / `41110796301` revealed one pytest case expecting domain-specific `MemoryWitnessLedgerRejected`, while inherited `MemorySchemaError` escaped during mutation detection (other 5,017 passed and one skipped on Ubuntu 3.11). A normal Contents change `4ddc2f5...` now converts that validation rejection to the fixture's explicit fail-closed domain. Its own CI is **not presumed GREEN**; check exact latest HEAD/run jobs before claiming.
- Independent local whole-repo pytest/Ruff is **not verified**: local GitHub DNS was unavailable. Created test files alone are not test results.

## What this does NOT prove

The separate SQLite ledger stores hashes/counts rather than Memory content, but is not independently writer-authenticated; a caller-controlled retained witness can detect a rollback *only if the caller actually retains it separately and it is itself authentic*. There is no cross-database atomicity, full historical append-prefix attestation or cryptographic identity of the writer. A complete malicious rewrite including the witness can evade local checks. A successfully reserved due slot or Personal Context request is not a trusted clock, consent, disclosure permission, scheduler activation, externally exactly-once effect, or execution authority. The JSON nesting guard is a parser resource cap, not a guarantee of mutable filesystem identity.

Frozen Memory v1 sqlite store `0aba6392b39563df520aa8b378d0b313f0cc0a0d`, Memory contract `b6e93821ecd69270a7634aceb20775dc36e9953c`, Agency contract `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9` stay unchanged; V3 frozen Contract 1 and protected final evaluation unchanged. Paid or potentially billable operations, external GPU, real Candidate adapter/weight generation, automatic promotion, real Tool/OS/voice actions, and approval-required main merges were NOT attempted.

## Next plan / 今後の方針

1. Verify the PR #8 source/test CI at the exact latest HEAD, address only real remaining failures using normal GitHub Contents.
2. Validate observer-retained Memory witness capacity, concurrent CAS and malformed-shape tests before considering any integration.
3. Review Planner UNKNOWN WRITE and trusted audit-before-action/occurrence replay gates with real-world dispatch hard-disabled.
4. Advance privacy retention/revocation and disconnected Observation fixtures without exposing raw content.
5. Keep V3 preflight approval, provenance, model/tool identity, and reproducibility gates under zero-new-cost controls. No genuine training, final V2 evaluation, irreversible operation or user spend authorization.

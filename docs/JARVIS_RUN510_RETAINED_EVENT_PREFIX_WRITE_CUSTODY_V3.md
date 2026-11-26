# Run510 — local historical Memory prefix, manual WRITE custody, V3 identity review

**Status:** disconnected/local-only Draft work; NOT_PASSED. This document
describes source/test work saved in two isolated Draft PR branches. It does not
change any frozen contract, approve human decisions, authorize GPU spending,
dispatch a ToolBackend, or certify a full ARK/JARVIS system integration.

## Exact local source/test identities

| Work lane | Source blob SHA | Test blob SHA | Authored pytest cases |
| --- | --- | --- | ---: |
| PR #8 manual WRITE triage nested-item custody | `f7dd5ed6754c5231fba972ece726726608dd6f76` | `63929839b294f11ece5d87c57f9a9022e6be22f5` | 8 |
| PR #8 Memory retained event-prefix check | `d71701995baf57bdb65e60830fe19925c637ebd1` | `97e226b1ba84a2a01bb02726861ededf5235c659` | 18 |
| PR #5 V3 first-pass witness custody | `ec0105f57bffb74ef2655478f83ec77476454d35` | `5f4e9e4d0d0e963af54cc7eec03df112744aa62a` | 5 |

**31 authored pytest cases** (parameter expansions counted); authored count
does not assert independent local pytest/Ruff success or final-head CI GREEN.

### A. Manual UNKNOWN WRITE packet custody (PR #8)

`offline_write_triage_recheck.py` now pins each nested
`OfflineWriteTriageItem` identity and five original fields through the
entire read-only recheck, including callbacks after the second detached
verification and during inert result construction. Previously pinning only
the outer `packet.items` tuple left a reflected change of an enclosed
frozen dataclass unchecked at return. Focused tests inject a late mutation
through the result constructor and verify fail-closed behavior.

Still **no** external outcome observation, human approval, replay,
automatic retry, real WRITE, or trusted-clock authority. An ordinary
checksum/replayed SQLite reservation cannot prove an actual outside effect.

### B. Retained Memory event-prefix continuity (PR #8)

New `sqlite_event_prefix_review.py` offers a read-only bounded capture
of **event history only** and a single-transaction comparison of the exact
old prefix against a later on-disk tail. A previously retained event-prefix
SHA-256 can now detect a historical event rewrite **even when a legitimate or
forged later event has been appended**. The reviewer checks exact storage
types, event ID monotonicity, bounded scan, per-memory revision/lifecycle and
cross-scope identity stability. The result remains content-free.

The witness must be retained separately by the caller. It has **no
independent authentication** and does not attest an adversarial writer.
This event-only review does **not** check the live `memories` table, replace
the existing same-transaction row/event alignment reviewer, prove file
snapshot isolation against the OS, or verify consent/retention/erasure.
Use the existing full-row audit for the independent row/event problem; do
not infer that two separately sampled audits are cross-store atomic.

### C. V3 offline identity bundle (Draft PR #5)

`identity_bundle_verify.py` now pins exact first-pass
`LocalIdentityArtifactWitness` field carriers for the second local JSON
read and report construction, including denial-only getter callbacks.
Equal-valued replacement of an earlier witness SHA or nested key tuple
can no longer pass by value equality alone. This is only an offline check
of already-existing, independently SHA-pinned JSON artifacts. It does not
establish an upstream Hugging Face revision, actual model file identity,
dataset provenance, training authorization, Candidate, GPU runtime, or
protected V2 evaluation.

## Evidence, unchanged safety gates, next integration

- Initial work bases: PR #8 `4f8f463cbb286524f62320da0d6a81cb56952a4e`;
  PR #5 `994c27bb0455f8320e4e96681b50c1246f369e0d`.
- Latest saved source/test commits before this document:
  PR #8 `f791153c2be73ef29e608799ff39f717a3ace0a2`;
  PR #5 `013697f18831e2625f0121d42c0c521520a39b43`.
- At document authoring, CI was launched but not yet established as
  exact-head 6/6 GREEN; final run IDs/outcomes belong in the single
  canonical end-of-invocation checkpoint, not guessed here.
- Preserved frozen blobs: Memory contracts
  `b6e93821ecd69270a7634aceb20775dc36e9953c`;
  Agency contracts `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`;
  V3 Contract `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`.
- No paid compute/API, physical-PC action, protected final evaluation,
  unauthorized credentials, training, Candidate generation/promotion,
  irreversible operation, frozen-contract modification or main merge.
  Keep PR #5 Draft/unmerged and ARK/JARVIS/V3 **NOT_PASSED**.

**Priority:** verify exact-head CI, close any substantiated regression
without weakening guards, then add read-only Memory prefix + full-row
transactional bridges, durable manual-only UNKNOWN WRITE incident evidence,
registry-bound PermissionGate/trusted-clock audit, restart-safe scheduler
witnesses and privacy-safe Personal Context review. Integration of any real
executor requires separately proven authorization, audit and replay gates.

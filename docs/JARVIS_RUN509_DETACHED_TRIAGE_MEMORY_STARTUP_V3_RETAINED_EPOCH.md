# ARK AI Run509 — Detached WRITE triage, retained Memory, startup custody and V3 bundle

**Source/evidence date:** 2026-11-01 Asia/Tokyo/JST. **Overall JARVIS/V3 status: NOT_PASSED.**
This is an isolated, free-only change record, not signed attestation, user
approval, protected V2 evaluation opening, real Tool execution, or a Candidate.

## Work bases and branch integrity

- PR #8 (Draft, unmerged) `research/jarvis-foundations`, initial work-basis
  HEAD `7e88e5ae2fdcd2eef9fc342760e03cad1f437e5b`.
- PR #8 corrected **final source/test HEAD** before this evidence-only commit:
  `c37a72ef8a3867dca1a3d922749facd1fe16a9a8`.
- PR #5 (Draft, unmerged) `research/v3-learning-evaluation`, initial HEAD
  `9b5eb790aa8584bef898498383c9d98f4c24e477`, final source/test
  HEAD `994c27bb0455f8320e4e96681b50c1246f369e0d`.
- main `7a843f17eb96ed13d66f23b58b06406b3002e405`, untouched.
- Frozen Memory contract blob `b6e93821ecd69270a7634aceb20775dc36e9953c`,
  Agency contract blob `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`,
  V3 contract blob `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`
  unchanged at reviewed branches.

## NEW source/test packages (46 authored pytest cases)

1. **Local, manual-only WRITE investigation recheck.**
   `src/ark/agency/offline_write_triage_recheck.py` blob
   `b3583a63435a9e76c33e5d4a623cd12ab916afa8`;
   `tests/test_offline_write_triage_live_recheck_run509.py` blob
   `9546b8ed013d3568437791e029b7893945468cbd`;
   **17** cases. Binds an unchanged detached checksum packet to exact caller
   recovery claims, previously retained witness, and a read-only, re-opened
   SQLite reservation ledger. UNKNOWN/RUNNING remain quarantined, and even
   SUCCEEDED is an **unverified claim**. No external effect observation,
   replays, consent, trusted clock or backend dispatch. A retained witness
   controlled by the same actor is not independently authenticated.
2. **Retained local Memory event+row alignment comparison.**
   `src/ark/memory/sqlite_alignment_retained_review.py` blob
   `e461f368ddb2b5ea0fb9fced0ea22417b50137a1`;
   `tests/test_memory_retained_alignment_compare_run509.py` blob
   `adbae22bc8912b1fd8d430c4ac84568130c222f0`;
   **16** cases. Checks a prior independently retained local digest against
   the current read-only single-transaction row/event reconciliation; rejects
   rollback and silently changed rows without new events. On appended events
   reports `ADVANCED_PREFIX_UNAUTHENTICATED`: historical prefix authenticity
   is unproven; local digests cannot authenticate an adversarial SQLite writer.
3. **Synthetic startup lease post-authority custody.**
   `src/ark/startup_readiness_lease_review.py` blob
   `9f0474277ae3d22071cac32c1023f336c1eff9e3`;
   `tests/test_startup_lease_denial_result_epoch_run509.py` corrected blob
   `1eb6fc217ab8fc6eb0377b2f0748b18dd609cd0a`;
   **8** cases. Final lease checks explicitly deny startup, dispatch and
   notification authority and close result, probe and requirement epochs
   after potentially reentrant False-valued getters. Synthetic READY is not
   a verified local machine or capability. CI at preceding HEAD
   `2fe33a8c3ff3b8f879e0983f9602bb0555e1c4c1` exposed a test-only
   error-message regex mismatch for a correctly rejected snapshot mutation:
   `readiness inputs changed during review` instead of `epoch`. The
   diagnostic assertion was corrected without weakening the source guard at
   `c37a72ef8a3867dca1a3d922749facd1fe16a9a8`.
4. **V3 offline local identity bundle original-carrier custody.**
   `src/ark/learning/identity_bundle_verify.py` blob
   `f8d2ed28e88cafef8b4f6ac4af21bc89511f278c`;
   `tests/v3/test_identity_bundle_original_report_carriers_run509.py`
   blob `1f6d1eb008e2e0b7e2a2f76a2720058ebf4953e2`;
   **5** cases. Preserve original report tuple/string carrier identities
   before local file verifier callbacks. Local JSON file hashes do not prove
   immutable upstream HF provenance or authorize GPU, training, Candidate
   generation, protected evaluation or merge.

## CI record (do not transfer predecessor GREEN to later HEAD)

- PR #8 previous Run508 source [41221892145](https://github.com/Iam-2squared/ark-ai/actions/runs/41221892145):
  6/6 GREEN for predecessor `651d71307ef472c170ced7cbb175b191a4ea7799`.
- PR #8 intermediate [41226379381](https://github.com/Iam-2squared/ark-ai/actions/runs/41226379381)
  at `5a49b5fa1769c361cd67cde5fc507251c42caa14`: all six jobs
  individually GREEN, but this precedes later changes.
- PR #8 first full Run509 source [41226583888](https://github.com/Iam-2squared/ark-ai/actions/runs/41226583888):
  Ubuntu 3.13/3.11 failed solely on an overly narrow pytest diagnostic
  regex, with Ruff GREEN and 5712 pytest passed/1 skipped/1 failed on the
  Ubuntu 3.13 job. Its source fail-closed protection was not relaxed.
- PR #8 corrected source [41226955276](https://github.com/Iam-2squared/ark-ai/actions/runs/41226955276)
  at `c37a72ef8a3867dca1a3d922749facd1fe16a9a8`:
  **IN PROGRESS at evidence preparation**, not yet six-job GREEN.
- PR #5 final source/test [41226789958](https://github.com/Iam-2squared/ark-ai/actions/runs/41226789958)
  at `994c27bb0455f8320e4e96681b50c1246f369e0d`:
  **IN PROGRESS at evidence preparation**, not yet six-job GREEN.
- Independent local checkout/pytest/Ruff and real-model or hardware
  measurements: **NOT VERIFIED**. Local GitHub DNS resolution is unavailable.
  Files saved through normal GitHub Contents API only; no raw-object bypass.

## HARD boundaries and next plan

Do not execute paid/external GPU compute, paid API/service, full Candidate/
adapter weight generation, protected V2 final evaluation, automatic promotion,
irreversible deletion, unknown external WRITE replay, real ToolBackend action,
human approval fabrication, frozen contract edit or main merge. PR #5 and
PR #8 remain Draft, unmerged. V3 still lacks immutable upstream and local
model/tokenizer byte identities, actual approved 120/30 dataset review,
pinned runtime/device identities and explicit cost-cap/spend authorization.

Next: verify latest exact-head six-job CI, fix substantiated failures
semantics-preservingly, add independently retained Memory witnesses and
restart-safe manual UNKNOWN WRITE outcome-review ledgers, then advance
registry-bound PermissionGate, audit-before-action trusted-clock and safe
scheduler occurrence claims without any real dispatch or replay.

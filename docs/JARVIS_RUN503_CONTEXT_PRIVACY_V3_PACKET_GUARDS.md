# ARK AI Run503 — Detached context/privacy and V3 review-packet guards

**Scope:** local-first and read-only/free-only source, tests, no real ToolBackend,
network data acquisition, external GPU, paid API, model generation or protected
V2 evaluation. These are source-and-test claims, not execution permissions.

## Concurrent work and exact basis

- Read work-basis JARVIS PR #8 HEAD: `856d0f5a8b882e1ea5ec4a0bdc3fe05b78218f39`.
  That branch already carried the uncheckpointed Run502 failure-aware fixture,
  independent terminal recomputation and Memory expiry-preview work. The
  exact-head JARVIS CI #1881 / 41199388605 was GREEN before our source edits.
- Read work-basis V3 PR #5 HEAD: `bc6263e87415c40961d66e6de9ca89e89b495d21`.
  The existing PR #5 #1873 / 41198490837 was GREEN before our V3 edits.
- Branches remain separate, Draft and unmerged. No files in frozen
  V1/V2/Local UI/Launcher evidence or frozen Memory/Agency/V3 contracts edited.

## Four new coherent source/test packages

### 1. V3 authorization review output-path custody

- `src/ark/learning/authorization.py`: `86bc7bdb0dd58077a2b64feff1d139361fa6de89`
- `tests/v3/test_authorization_packet_output_path_run503.py`:
  `f00a4e9e88304a72b28c7bd9f9d69af9238db19c`
- 11 defined test cases: new exclusive canonical output, existing file,
  directory, absent parent, explicit `..`, oversized path, file/dangling/
  ancestor symlinks, CLI rejection and exact path type.
- Guards are best-effort pathname checks plus exclusive create, **not**
  an atomic directory-descriptor attestation or user compute authorization.
- CI #1883 / 41199933620: 6/6 GREEN on test-source HEAD.

### 2. Unicode-correct offline Personal Context excerpts

- `src/ark/offline_context_search.py`:
  `865b2072ffe4fea0953975a35c5a2de503b79960`
- `tests/test_offline_context_unicode_offsets_run503.py`:
  `19473833d3cb9a330d8940ee5c50ed63e96f9eaf`
- 7 defined cases. A multi-codepoint Unicode casefold (`ß`, `İ`, `ﬃ`)
  previously produced offsets for normalized text but sliced original
  fixture text using those offsets; late hits could be omitted. New source
  index mapping retains the original codepoint offsets while preserving
  deterministic score/ranking, scope and all denial-only flags.
- Fixtures remain synthetic, local, untrusted and never export-authorized.

### 3. Detached V3 review-packet rebind to exact unapproved snapshot

- `src/ark/learning/authorization_packet_verify.py`:
  `24ee0cf40f475b89a06d6354f9276fabbecf5348`
- `tests/v3/test_authorization_packet_verify_run503.py`:
  `8f61a1697090e7ac7cf9e965c15b3d6be0556349`
- 19 defined parameterized cases. Offline-only packet reconstruction, exact
  snapshot and packet carrier epochs, canonical-byte comparison, separately
  retained **whole-packet** SHA-256 and verification of packet's embedded
  digest that excludes its own digest field. A witness explicitly denies
  compute/Candidate/protected-evaluation/main-merge authority.
- Original CI #1887 / 41200271013: FAIL 6/6 at Ruff E501 in a **test-only**
  long assignment. The assignment was wrapped without changing behavior at
  `5f20a00aa86c20dab76323a82279419a17c19f03`.
  Corrected CI #1890 / 41200458143 was IN PROGRESS at this report read.
- This verifier is detached: its existence is not a new automatic gate or
  substitute for actual human decisions, data rights, or billing approval.

### 4. Privacy-safe redaction output recheck after authority callbacks

- `src/ark/offline_context_redaction.py`:
  `036b2c3632c5e774ab8c04b19bd3581c3e1ed336`
- `tests/test_offline_redaction_final_result_epoch_run503.py`:
  `bab827b2a078e3b2bfa98048fdb12e3eeae231e5`
- 8 defined cases: a denial-only last descriptor returning False could
  reflectively replace a frozen receipt's masked text, digest, identity,
  coverage, or count **after** initial validation. Final exact result-field
  recheck now rejects all these cases. Masking remains neither deletion
  evidence nor consent or disclosure authority.

**Total authored new parameterized test cases: 45 = 11 + 7 + 19 + 8.**
These numbers count source-level test parametrization only. They do not claim
local pytest execution or final exact-source CI GREEN for every new change.

## Validation state and boundaries

- Source/test updates used the normal GitHub Contents API and fresh PR HEAD
  reads before every write; no force push, raw-Git safeguard bypass, merge or
  frozen contract mutation.
- Local public-repo clone was attempted but GitHub DNS was unavailable;
  independent local pytest and Ruff were not run.
- PR #5 path custody CI #1882/#1883: GREEN; packet verifier source CI
  #1886: GREEN; verifier test CI #1887: Ruff E501 FAIL then corrected,
  latest #1890 IN PROGRESS at report read.
- PR #8 #1881: GREEN only for preceding Run502 HEAD. Current Unicode
  and redaction changes are under #1885/#1889 matrices, not yet all-GREEN
  at report read. No earlier success is attributed to the latest HEAD.
- Frozen blob checks at report read: Memory contracts
  `b6e93821ecd69270a7634aceb20775dc36e9953c`; Agency contracts
  `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`; V3 contract
  `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`; V3 checksum artifact
  `176154514bd6be22685ca0555bc682c3bd8d45dc`.
- Overall JARVIS and V3: **NOT_PASSED**, with Candidate and final evaluation
  explicitly blocked. No credentials, personal source data, live device
  capture, training adapter, real action or potentially billable execution.

## Next plan / 今後の方針

1. Confirm #1889 and #1890 job-level exact-head 6/6 CI; inspect/fix failures
   without weakening tests. No redundant manual CI re-runs.
2. Continue modular exact grant/ToolRegistry, durable UNKNOWN WRITE quarantine,
   trusted-clock audit-before-action and Scheduler occurrence/replay gates.
3. Strengthen Memory CAS and retention; privacy-safe Context consent/revocation;
   offline Observation fixture custody; keep integration gated by exact-head
   GREEN invariants.
4. Keep V3 detached input/file/approval-reproducibility checks strictly free,
   preserving frozen review and protected evaluation boundaries.

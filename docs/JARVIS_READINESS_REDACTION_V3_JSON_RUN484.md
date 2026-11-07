# Run484 — Disconnected READ startup / local privacy masking / V3 evidence parsing

All changes are **free-only, reversible and disconnected**. No external ToolBackend,
user-context disclosure, real sensor input, protected V2 final evaluation, GPU,
LoRA training, Candidate artifact, automatic promotion or main merge was attempted.

## Work-basis and exact source identities

- Invocation initial canonical PR #8 head:
  `9814c25d03ea408f02955e37404cf0b783ca3c66`.
- Invocation initial separate V3 PR #5 head:
  `d8669d3bb45d8cd766123bdd6536fbec8664eba5`.
- Final authored PR #8 source/test head before this document:
  `fb67c8feaa1e25bb4979f40fb5de6189bddbb967`.
- Final authored PR #5 source/test head:
  `f5f4a87c6985a6c5c6992d7b14a35cc314a6741f`.

### Package A: Independent verification of disconnected startup READ preflight

- `src/ark/disconnected_local_readiness.py`, blob
  `e4ed7a32f2a6a7327d3acfd689f5ece6db24dafc`.
- `tests/test_disconnected_startup_preflight_custody_run484.py`, blob
  `93fe6afc2ca036697c8d54e6f188d39ccf65a814`.
- **9 authored pytest cases**. The startup review now re-derives READY membership from
  the PlanGraph statuses, binds each READY step through the registry without
  executing a backend, and independently reconstructs the canonical preflight
  grant and review digests. A forged same-type preflight with altered steps,
  bound identities, grants, or fingerprint is rejected.
- The early source commit used a double-escaped domain separator; this was
  corrected immediately by the normal GitHub Contents API before adding tests.
  No changed frozen contract or real authorization resulted.

### Package B: Privacy-safe offline masking receipt authority check

- `src/ark/offline_context_redaction.py`, blob
  `41793fcf34014d643f4b2ee2b7a17651a194c8e9`.
- `tests/test_offline_redaction_receipt_authority_run484.py`, blob
  `6ad09aa848993f515d509c2a036906c419c4d3dc`.
- **8 authored pytest cases**. The locally constructed redaction preview
  explicitly rejects spoofed consent, erasure, export, or dispatch authority.
  It also requires an exact integer masked-character count. Full masking is
  never treated as irreversible deletion, complete PII removal or release consent.
  Masked content remains local and is never persisted or transmitted here.

### Package C: Robust offline V3 canonical JSON evidence reader

- PR #5 `src/ark/learning/run_manifest.py`, blob
  `236299b8d1b8ae7cc4bda5081229b504fa687055`.
- PR #5 `tests/v3/test_manifest_parser_failclosed_run484.py`, blob
  `9624f73ca1528cba01011dabad8b73312d53a0ef`.
- **15 authored pytest cases**. An exponent lexically valid in JSON but
  decoded as infinity, excessive JSON nesting, or an error during canonical
  serialization now results in `CandidateRunManifestError` rather than
  leaking a raw parser/recursion/overflow exception. Existing 1 MiB read cap
  and byte-for-byte canonical matching remain unchanged. This checks already
  existing evidence only; it neither trains nor creates Candidate weights.

## CI and evidence limits

- Prior canonical checkpoint PR #8 head `9814c25d03ea408f02955e37404cf0b783ca3c66`:
  GitHub Actions #1660, run `41095217819`, reported **SUCCESS**.
  This is **NOT** validation of new Run484 source.
- PR #8 Run484 final source/test head `fb67c8feaa1e25bb4979f40fb5de6189bddbb967`:
  CI #1665, run `41101556659`, **QUEUED** at last exact-head read.
- PR #5 Run484 final source/test head `f5f4a87c6985a6c5c6992d7b14a35cc314a6741f`:
  CI #1667, run `41101765576`, **QUEUED** at last exact-head read.
- The authored **32** new parameterized cases are not declared passing before
  exact-head CI completes. Local full pytest/Ruff **NOT VERIFIED**; local
  `git ls-remote` could not resolve `github.com` through DNS.
  No duplicate Actions runs were started.

## Frozen evidence, security boundaries, next work

The Memory v1 SQLite store, Memory contract, Agency contract and frozen V3
Contract remained on their previously established blob identities:
`0aba6392b39563df520aa8b378d0b313f0cc0a0d`,
`b6e93821ecd69270a7634aceb20775dc36e9953c`,
`13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`,
`b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`.
Historical V1/V2/Local UI/Launcher proof and protected final V2 suite stay closed.

An offline startup receipt is never permission to start tools. Local SHA/SQLite
evidence does not establish independent writer custody, trusted time, human
consent/revocation, cross-store atomicity or exactly-once external effects.
V3 still lacks real immutable model/dataset/tool identity and approvals before
any billable action; PR #5 stays Draft/unmerged.

**Next plan / 今後の方針:** Resolve CI #1665 and #1667 at exact source HEADs;
if any FAIL, inspect logs and make the smallest semantics-preserving normal
Contents API correction. Then pursue independently held Memory event witnesses,
durable UNKNOWN WRITE triage, trusted-clock audit-before-action, personal
context revocation, and local-only Observation fixtures on separate safe lanes.

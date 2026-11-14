# Run559 — Passive scheduler prefix authority and complete local search excerpts

**Scope:** Draft PR #8 only; no main merge, live action, trusted-clock grant,
notification, personal-data export, or consent decision. This is bounded
synthetic/local-fixture evidence, not a readiness/PASS determination.

## 1. Direct due-prefix review authority is pinned before I/O

- Source [dbad7577](https://github.com/Iam-2squared/ark-ai/commit/dbad75778a665021bdcaf7a897bb2a6907dcfcd1):
  `src/ark/agency/disconnected_due_prefix_review.py` retains six original
  result denial properties plus the retained due witness's original
  `independent_custody_proven` descriptor at import time. It rejects a
  substituted always-False getter before read-only SQLite inspection, and
  checks those original descriptors at further review/callback boundaries.
- Regression [55a3beeb](https://github.com/Iam-2squared/ark-ai/commit/55a3beeb780bc05d6395a1e066dc1bf10c0cc6ac):
  `tests/test_due_prefix_original_denials_run559.py` contains **9 authored
  cases**: 6 false-only result getters, 1 witness getter, 1 mid-snapshot
  swap, 1 clean unchanged passive review. Before-read cases assert **zero
  database opens and zero substituted getter invocations**.
- Exact source+tests CI [41478380271](https://github.com/Iam-2squared/ark-ai/actions/runs/41478380271):
  at the latest inspection, 3 Ubuntu jobs GREEN and 3 Windows jobs IN
  PROGRESS. Do not infer six-job GREEN before the full matrix completes.

The retained due fingerprint is supplied by the caller; matching it cannot
prove an independently authenticated writer, clock, user intent, actual
notification, or absence of other effects. No automatic replay is enabled.

## 2. Complete earliest Unicode lexical match in bounded excerpt

- Source [c55af80e](https://github.com/Iam-2squared/ark-ai/commit/c55af80e643bbea6a822d74f24dcf9f82f507d2a):
  `src/ark/offline_context_search.py` now converts **both** casefolded
  boundaries of the earliest matched query token back to original Unicode
  source offsets. The local excerpt includes the whole token (up to the
  existing 128-byte token budget) and bounded surrounding text, rather
  than truncating long tokens at `first_source + 96`.
- Regression [fb878bfc](https://github.com/Iam-2squared/ark-ai/commit/fb878bfc4695e17e86447b8fa1affe89deb8bb38):
  `tests/test_offline_context_full_match_excerpt_run559.py` adds **7
  authored cases**, including 110/128-character terms after ASCII, ß and
  İ prefixes, deterministic ranking/digest, a 256-source-codepoint bound,
  and preservation of the historical short-term 96-character following
  window.
- Exact source+tests CI [41478772433](https://github.com/Iam-2squared/ark-ai/actions/runs/41478772433):
  at the latest inspection, 3 Ubuntu jobs GREEN and 3 Windows jobs IN
  PROGRESS. Do not infer six-job GREEN before the full matrix completes.

This only retrieves **explicit local synthetic fixtures**. It is not a
MemoryStore reader, not a live Personal Context grant, and does not permit
retention beyond the fixture expiry, external disclosure or Tool dispatch.

## Work basis, evidence limits and next dependency

- Initial work-basis HEAD: `dbf33a04430c23ef7d31c940343c8aa0c3315017`.
- These package commits were saved by normal GitHub Contents operations;
  source/test additions do not alter frozen V1/V2/Local UI/Launcher,
  `agency/contracts.py`, or `memory/contracts.py`.
- **16 authored pytest cases, not 16 locally executed PASS results**.
- Both packages remain read-only/disconnected; file and SQLite checks are not
  authenticated external custody and not a cross-store transaction.
- Next: establish exact-head six-job CI for the newest PR #8 commit before
  interpreting dependent planner/restart or Personal Context integration.
  If any CI job fails, correct the narrow failing behavior without relaxing
  denial, expiry, scope or provenance rules.

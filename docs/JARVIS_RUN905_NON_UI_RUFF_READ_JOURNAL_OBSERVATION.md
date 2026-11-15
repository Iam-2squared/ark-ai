# ARK Run905 — non-UI CI recovery, bounded READ identities, Observation fixture preallocation

**Prepared (observed JST wall clock): 2026-11-16T06:51:13.816+09:00.** Isolated, reversible, free-only Draft PR #8 work; no user device, real ToolBackend, paid services, actual user data, UI, Candidate, V2 protected evaluation or main merge.

## Verified baseline and actionable CI failure

- Prior checkpoint/source HEAD `77bac4278c8a46d41c87f046606d62533549e30a` had [Actions run 43761205316](https://github.com/Iam-2squared/ark-ai/actions/runs/43761205316) **FAIL 6/6**: all six runners stopped on Ruff `I001` (import sort) at `src/ark/memory/expiry_candidate_preview.py`. Not a passed Run904 baseline.
- Exact import-only correction: [`ecd1b6874af5b919e2866aa4830f652076321621`](https://github.com/Iam-2squared/ark-ai/commit/ecd1b6874af5b919e2866aa4830f652076321621). No schema, expiry logic, consent, or safety contract changed. This correction's CI [43765295142](https://github.com/Iam-2squared/ark-ai/actions/runs/43765295142) started; not yet confirmed GREEN when this report was prepared.

## NEW — 3 independent non-UI packages + focused CI fix

1. **Disconnected synthetic READ result admission** — [source `074325144e6d194502e4eded09660f99ece11b90`](https://github.com/Iam-2squared/ark-ai/commit/074325144e6d194502e4eded09660f99ece11b90), [8-case regression file `f127655c66806ef5b3453814e8ab56403621794d`](https://github.com/Iam-2squared/ark-ai/commit/f127655c66806ef5b3453814e8ab56403621794d). Require exact request/step/hash string lengths before regex matching; reject a massive canonical result JSON before allocating UTF-8 or invoking JSON; require exact result carrier string types before equality so a reflected subclass cannot execute attacker-supplied `__eq__` or `__ne__` during identity admission. Keep standard one-result and UTF-8 receipts non-authorizing. This does not authenticate a READ operation.
2. **Detached READ journal bound witness/receipt preflight** — [source `b418b2e4989bb194e740021e177cb1f5f9773a45`](https://github.com/Iam-2squared/ark-ai/commit/b418b2e4989bb194e740021e177cb1f5f9773a45), [11-case regression file `c21639bd79399d03b5a3bfd8d945e339a56d4b52`](https://github.com/Iam-2squared/ark-ai/commit/c21639bd79399d03b5a3bfd8d945e339a56d4b52), [regex fixture correction `f612fdd61c376a7c2a77bd041f056ccb5760dd80`](https://github.com/Iam-2squared/ark-ai/commit/f612fdd61c376a7c2a77bd041f056ccb5760dd80). Bounds for retained tip, receipt request/step/digests and stored chain digest precede regex. Existing SQLite pre-hydration and append/CAS behavior unchanged. Regression isolates oversized reflected values; malformed digest and count still deny. This is local hash-chain consistency only, not independent custody.
3. **Private Observation fixture metadata allocation** — [source `c69f96277109a415d843189111078c130e968ba8`](https://github.com/Iam-2squared/ark-ai/commit/c69f96277109a415d843189111078c130e968ba8), [13-case regression file `7faf8ea8bddb9b2f6d6b75e480ad1c99003ae142`](https://github.com/Iam-2squared/ark-ai/commit/7faf8ea8bddb9b2f6d6b75e480ad1c99003ae142). Cap exact source/privacy label length before `strip()`; existing native NUL, UTF-8 and byte-width rules continue. Both text and binary fixture adapters refuse very large metadata without handing private input to the hashing helper. An exactly 1024-byte valid Unicode label remains allowed.

**32 regression cases authored across 3 test files; not yet a claim that all 32 have passed.** The individual small source/test writes naturally launch PR CI; no manual duplicate runs. Intermediate CI outcomes do not prove the final merged source/test HEAD.

## Scope, limitations and next actions

- All new work is on `research/jarvis-foundations` / Draft PR #8, with Frozen V1/V2/Local UI/Launcher, protected V3 Draft PR #5, paused UI Draft PR #9 and main untouched.
- Exactly-once real effects, externally trusted clock, signed authorization, independent row/event witnesses, cross-store Planner UNKNOWN reconstruction and real tool execution remain unproven.
- Existing Windows/Ubuntu SQLite WAL/SHM cross-process revocation last-close race remains a blocker. Keep a durable-but-disputed attempt in **DENIED/UNKNOWN**, never a successful authorization or safe automatic WRITE retry.
- After final exact-HEAD CI, check every Windows/Ubuntu × Python 3.11–3.13 job; on failure fix the smallest semantics-preserving defect through the normal Contents API, then switch to an independent lane. Continue Memory CAS/event, Planner recovery, registry/gate and disconnected mock integration only after their prerequisites have exact-head evidence. No UI work.

**Overall ARK/JARVIS: NOT_PASSED.** No paid, external GPU, protected evaluation, actual personal-data export, Candidate promotion or irreversible action authorized.

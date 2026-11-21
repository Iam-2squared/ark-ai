# ARK AI — Run748 / non-UI CI repair, Observation, Planner & Personal Context

**Report sampled at:** 2026-11-10 05:54:47 JST (administrative wall clock; NOT an ARK trusted clock).
**Branch:** `research/jarvis-foundations`; [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), intentionally unmerged. **Initial exact work basis:** `0aa1a8930085528e41793144f74e0bbef6805067`. **Source/test terminal HEAD:** `a0af2b14a3331271991c6012c4960c7aacd9ddff`. This report's own commit and subsequent checkpoint have separate SHAs and require separate CI verdicts.

## Package A — Observation optional closed-chain protocol preaccess

- [Source b1d1af2](https://github.com/Iam-2squared/ark-ai/commit/b1d1af2ecb47b3778521d8fae1edcb3a524ca902) preserves import-original `_MAX_ENVELOPES`, envelope field/name tuples, review result fields and False-only authority-name vector, in addition to the already-pinned hashes/constructors/slots. Rejects preinstalled replacements before any potentially private observation fixture read.
- [8 authored cases 5cfa1cb](https://github.com/Iam-2squared/ark-ai/commit/5cfa1cb51f6f55760e354d73cbcbe1f491bbcb47) cover seven admission/protocol mutations (including value-equal cloned tuple) and an inert valid closed-chain review. No sensor/camera/mic usage, authenticated provenance, consent or dispatch.

## Package B — Disconnected Planner ambiguous restart

- [2 authored cases 8553679](https://github.com/Iam-2squared/ark-ai/commit/85536795c6eb71f4030137dcba0c6a08a0aba5d8) test a synthetic DAG with a post-COMMIT result callback failure on (i) a root RUNNING transition, preserving ambiguous running without automatically starting its dependent; and (ii) a root FAILED transition, preserving the derived BLOCKED child and an independently eligible mock branch. Both use temporary SQLite and inert `ToolCall` metadata; no actual executor, grant or replay authorization.
- This is a test-only extension, NOT a new proof of exactly-once external side effects.

## Package C — Personal Context replay recovery codec fence

- [Source 879096a](https://github.com/Iam-2squared/ark-ai/commit/879096a1ac9986e44cf0d06d437d3910a29a820d) pins import-original `hashlib`, `hashlib.sha256`, `json`, `json.dumps` and the versioned local digest domain before caller ledger/witness access and after reentrant callbacks. Rejects swapped or same-value replacement domain before private metadata reads.
- [8 authored cases 8bb75ff](https://github.com/Iam-2squared/ark-ai/commit/8bb75ffc7c26ab44758a630876028a55102934ca): six preinstalled codec/domain changes, one ledger callback retargeting its domain, one legitimate inert local witness. Previous callback-execution expectations in [Run482 fixture 39c6497](https://github.com/Iam-2squared/ark-ai/commit/39c6497d98389fcd50381bdd2870097bd5bc42be) and [Run487 fixture d976def](https://github.com/Iam-2squared/ark-ai/commit/d976defeac02ca51835087017ae1e6141400e72b) now assert early denial rather than execution of a substituted codec or a synthetic late append.
- None of these receipts authenticate consent, legal basis, revocation freshness, independently retained prefix or disclosure rights.

## Package D — Real CI failure diagnosis and 8 semantics-preserving clock fixture fixes

- Latest prior-checkpoint [CI #42692739846](https://github.com/Iam-2squared/ark-ai/actions/runs/42692739846) Ubuntu Python 3.11/3.12/3.13 **FAIL** (last inspected); [earlier completed #42692304054](https://github.com/Iam-2squared/ark-ai/actions/runs/42692304054) **6/6 FAIL**. Actual Ubuntu Python 3.11 job log recorded **8 failed, 12,132 passed, 1 skipped**, all eight old fixtures expecting a mutable `_hash` to execute. The Run747 source correctly rejected an injected digest helper *before* touching a caller clock iterator with `synthetic clock digest implementation changed`.
- [Six cases 1abd2f9](https://github.com/Iam-2squared/ark-ai/commit/1abd2f9cd6ee1254d4272fbdc9c6bdad9a25b748), [one case 2418cd8](https://github.com/Iam-2squared/ark-ai/commit/2418cd848fed9265ab8edff1734d779fc2d8b0b4), [one case a0af2b1](https://github.com/Iam-2squared/ark-ai/commit/a0af2b14a3331271991c6012c4960c7aacd9ddff) now assert **early refusal and zero untrusted callback executions**. No production clock rule relaxed.
- Source/test latest commit has an automatically triggered separate CI; **no local full pytest, no exact-head six-job GREEN yet**, and no manual duplicated workflow was started. An earlier GREEN (e.g. #42691268489) applies only to its *different* older HEAD.

## Custody boundaries, blockers and follow-up

- Frozen V1/V2/Local UI/Launcher contracts and evidence remain unchanged. UI-paused Draft PR #9 and training/approval-gated Draft PR #5 remain untouched/unmerged; no main merge.
- Zero paid API, external GPU, training weights, Candidate generation/promotion, hardware action, credential, actual external tool or protected V2 evaluation. No raw Git object/write-safeguard bypass.
- Prioritize (1) exact latest six-job CI and corrective logs; (2) Memory global event, CAS/ABA, WAL and manual-only COMMIT-UNKNOWN evidence; (3) Planner terminal restart and registry-bound PermissionGate/occurrence audit-before-action, mock-only until separate GREEN; (4) privacy revocation/retention and free-only V3 provenance/approval guards. Actual authenticated clock, true exactly-once external effects, retained independent provenance, physical GGUF and real Windows handle identity remain unresolved.
- **ARK/JARVIS/V3 PASS: NOT_PASSED.** New synthetic test cases are authored, NOT declared passing absent an exact-HEAD CI verdict.

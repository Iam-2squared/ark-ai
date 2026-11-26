# ARK AI Run979 — Memory event and disconnected READ journal prehydration

**Prepared at (Asia/Tokyo): 2026-11-19T08:56:04.750+09:00**. This is a reporting timestamp, not a trusted approval, scheduler, audit or expiry clock.

**Work basis:** Draft PR #8 `research/jarvis-foundations` at `a49c9df0155c7d45946e039d49ec6e54f590a8e2` (Run978). **Latest executable/test HEAD at report preparation:** `0fffd69d70c11861a3b2b75aa5e7d1ad1defa88e`. **Overall ARK/JARVIS:** **NOT_PASSED**. This is isolated, reversible, non-UI foundation work; no model, external operation or real tool is invoked.

## Two independent implementation+test packages

### 1. Memory v1 event page and direct ID admission

- [Source `3aab212b`](https://github.com/Iam-2squared/ark-ai/commit/3aab212bbbc66de655c57067e5016e470f869470): direct `_memory_id()` validates exact `str` and 68-codepoint fixed width *before* regex or SQLite. An adversarial `str` subclass or million-character ID cannot pass into a private read/delete path. No valid `mem_<64-hex>` grammar change.
- Same source: scoped event-page SQL-side prehydration now refuses nonpositive revisions, negative occurrence timestamps and operation labels not in the frozen create/update/delete/expire set. This prevents corrupted negative scalar rows from reaching `SELECT *` event hydration; it does not authenticate events or guarantee global history provenance.
- [Tests `eeb54562`](https://github.com/Iam-2squared/ark-ai/commit/eeb545624e21c91785b5c37c79cffe446ae2596c): **8 authored cases** covering subtype/width/digest input refusal without database access; oversized-ID regex avoidance; malformed persisted revision/timestamp refusal before `SELECT *`; valid multilingual create/update/delete replay.
- [Ruff-only correction `0fffd69d`](https://github.com/Iam-2squared/ark-ai/commit/0fffd69d70c11861a3b2b75aa5e7d1ad1defa88e): import order and one test line length, no denial weakening or test deletion.

### 2. Disconnected synthetic READ journal prehydration

- [Source `dba7f570`](https://github.com/Iam-2squared/ark-ai/commit/dba7f5705209ac6f21dbb2a974d0311beac6c4aa): add SQLite-side fixed-operation allowlist and positive `seq` check before receipt row allocation. Preserves read-journal schema, hash-chain format, existing dispatch/replay denials and valid local READ operation set.
- [Tests `c8a6bd98`](https://github.com/Iam-2squared/ark-ai/commit/c8a6bd98c5788300bbdad893971801ba92fe06ff): **5 authored cases** for zero/negative SQL sequence, invalid stored operation, and valid four-operation cold-restart witness. A guarded connection fails if a corrupt receipt reaches full row hydration. No executor and no plaintext tool results.

**Total new regression cases authored:** **13** (8 Memory + 5 READ). These are not claimed to have passed until an exact-HEAD CI result is confirmed. The source/test commits are all normal GitHub Contents API writes; no forced refs/raw Git objects or bypassed safeguards.

## Observed CI, exact refs, limitations

- Previous Run978 checkpoint `a49c9df0155c7d45946e039d49ec6e54f590a8e2`: [CI #44416733340](https://github.com/Iam-2squared/ark-ai/actions/runs/44416733340) **SUCCESS**; this proves only that prior commit.
- Pre-repair test HEAD `b815a6ee08cf9c337ed48d52c6dc27d9d75a9463`: [CI #44424168763](https://github.com/Iam-2squared/ark-ai/actions/runs/44424168763) **FAIL 6/6** at Ruff: I001 import order and E501 long line in the new Memory fixture.
- READ-test HEAD `c8a6bd98c5788300bbdad893971801ba92fe06ff`: [CI #44424449673](https://github.com/Iam-2squared/ark-ai/actions/runs/44424449673) **FAIL** from the same prior Memory fixture Ruff findings; source behavior was not evaluated by those red jobs.
- Repair HEAD `0fffd69d70c11861a3b2b75aa5e7d1ad1defa88e`: [CI #44424622568](https://github.com/Iam-2squared/ark-ai/actions/runs/44424622568) **IN PROGRESS** at last independent check. Full six-job GREEN **not yet verified** at report preparation. No manual duplicate run, local PC/GGUF, model evidence or independent consent/time proof.

## Frozen state and constrained next work

At report preparation: main `7a843f17eb96ed13d66f23b58b06406b3002e405`; PR #5 Draft `805b377697472268db02650a89c7a94b1c5337c8`; PR #9 Draft `3b49048dd70eebcb6268299b9ecef4e301bbc0fd` and **UI paused**; PR #8 remains Draft/unmerged. Frozen V1/V2/Local UI/Launcher evidence, Memory v1, ToolCall/PlanStep v1, Observation Envelope v1 and protected V2/V3 evaluation gates unchanged. No paid/external compute/API/GPU, no credentials, no Candidate training/promotion, no protected evaluation opening, no human review claim, no actual tool dispatch, no WRITE retry or main merge.

**Open blockers:** cross-process WAL/SHM pathname races, externally authenticated owner/consent/revocation and trusted clock, independent event prefix/witness custody, exact-once real-world effect reconciliation and device-side evidence. Local SQLite plus SHA-256 do not prove external actors or actions.

**Next plan / 今後の方針:** (1) confirm exact latest HEAD CI 6/6 and repair failures by ordinary permitted changes; (2) Memory WAL/SHM, generation CAS/ABA, expiry and COMMIT-UNKNOWN manual quarantine; (3) Planner durable crash recovery, ToolRegistry/PermissionGate, one-shot authority and preaction audit in disconnected/mock mode; (4) privacy-safe Personal Context, proactive occurrence fencing, Observation fixture adapters and free-only V3 checks. Never resume UI without user authorization.

**Overall ARK/JARVIS: NOT_PASSED.**

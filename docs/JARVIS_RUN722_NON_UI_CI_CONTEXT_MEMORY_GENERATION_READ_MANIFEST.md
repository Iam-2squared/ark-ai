# ARK AI — Run722: inherited Context CI repair, Memory retained generation preaccess, and Planner READ manifest epoch fences

**Saved / report prepared:** Asia/Tokyo/JST 2026-11-09T06:52:38.236+09:00 (administrative clock sample, not an authenticated execution clock). **Only zero-cost, disconnected, non-UI work**. No physical GGUF, external compute, Candidate, live tool, human approval, protected V2 evaluation, or main merge.

## Exact basis and scope

- Repo: `Iam-2squared/ark-ai`, `research/jarvis-foundations` / **Draft PR #8**; first basis `062df1781ef993736469cc19400eba1dc9a277bb` (Run721 checkpoint).
- No changes to `main`, protected Draft PR #5, paused UI Draft PR #9, frozen V1/V2/Local UI/Launcher evidence, protected V3 contract/evaluation boundaries.
- **Three substantive coherent work packages** (one CI repair across two files; one Memory source/test; one Planner source/test); two production modules modified, **two existing test files corrected**, two NEW test files, **11 authored new parameter-expanded cases**, plus **eight existing parameter-expanded cases changed/strengthened**. No full local Ruff/pytest was available in the tool environment; CI must establish platform PASS.

## A — repair actual Run721 Context CI failure without weakening guards

- Exact Run721 result HEAD `062df1781ef993736469cc19400eba1dc9a277bb` [CI #42522934151](https://github.com/Iam-2squared/ark-ai/actions/runs/42522934151) **FAIL 6/6**. Ubuntu Python 3.11: **7 FAIL / 11,281 PASS / 1 SKIP**, Ruff passed. All seven failures were old `personal_context_offline_preview` tests still expecting later serializer, parser, or retained-result callbacks. New early SHA/JSON original-function pin correctly rejects with `context preview authority definition changed` **before invoking hostile functions**.
- [Commit `91927dc2`](https://github.com/Iam-2squared/ark-ai/commit/91927dc2df438a852720a72e8532c110e46ec743): update six existing JSON-roundtrip tests to expect early denial; assert callback never ran where tracked and retained text is unchanged. One earlier `changed` regex coincidentally passed; tightened it to exact early diagnostic.
- [Commit `acc36298`](https://github.com/Iam-2squared/ark-ai/commit/acc362988760c5eb91d3f1ea02f2fb8219d62585): update two parameter-expanded retained-preview tests to require no synthetic-private hash callback invocation and no forged report mutation. The production context guard was **not changed**.
- Fresh per-commit automatic CI: [#42526882290](https://github.com/Iam-2squared/ark-ai/actions/runs/42526882290) and [#42526914362](https://github.com/Iam-2squared/ark-ai/actions/runs/42526914362), observed **IN PROGRESS** at report prep. **Not yet certified GREEN**.

## B — Memory: fail closed before retained CAS report descriptor/reviewer callbacks

- [Source `0c42cb5e`](https://github.com/Iam-2squared/ark-ai/commit/0c42cb5efe14682f532684dd9a00e593dfb9648f): in `src/ark/memory/retained_generation_fence.py`, extend already present denial-property pins to seven dataclass field descriptors, four constructor/lookup hooks and original `review_memory_revision_reuse` function identity. Check before retained fields or private SQLite can be passed to a substituted callback; recheck at existing phase boundaries.
- [Tests `b53de69a`](https://github.com/Iam-2squared/ark-ai/commit/b53de69a139e452e1b59343bae88e53b94d6d081): **7 authored synthetic regression cases**: five substituted field/hook/denial carriers, one rebound reviewer, one clean retained comparison. All malicious callback tests require **zero invocations**, and the clean case retains explicit non-authority flags.
- No migration, SQLite write, consent, authenticated writer or independent historical custody.

## C — Planner: detached READ input manifest same-length file race refusal

- [Source `983dbe68`](https://github.com/Iam-2squared/ark-ai/commit/983dbe680690893e8a6f4ff734630faeb30628a3): `load_read_input_manifest` now compares named-file and both handle-fstat observations on `st_dev/st_ino/st_size/st_mtime_ns/st_ctime_ns/st_nlink`, and requires the named/after file remain a regular single-link file. Detect same-size in-place updates or metadata drift during read rather than accepting one internally canonical envelope.
- [Tests `755781d7`](https://github.com/Iam-2squared/ark-ai/commit/755781d735338c2787c68651d2fcb7de506bd2b9): **4 authored synthetic same-size metadata-race cases** exercising handle post-read and named-path post-read `mtime_ns` and `ctime_ns` changes. They require `changed during read` rejection, preserved existing artifact and no replay authority.
- These epochs are **local and mutable**, not external attestation; a post-review attacker can still replace local evidence. Windows crash-safe directory name publication remains unproven, and digest evidence never proves backend READ execution.

## CI / caveats / prioritized next

At report prep, automatic CI for `0c42cb5e` [#42527065235](https://github.com/Iam-2squared/ark-ai/actions/runs/42527065235) and `b53de69a` [#42527112087](https://github.com/Iam-2squared/ark-ai/actions/runs/42527112087) were IN PROGRESS; `983dbe68` [#42527224541](https://github.com/Iam-2squared/ark-ai/actions/runs/42527224541) and last test HEAD `755781d735338c2787c68651d2fcb7de506bd2b9` [#42527290391](https://github.com/Iam-2squared/ark-ai/actions/runs/42527290391) were QUEUED. **Current exact-head Ubuntu/Windows × Python 3.11–3.13 6/6 GREEN = NOT VERIFIED.** No manually duplicated or rerun workflows.

1. Check **checkpoint-result exact HEAD** 6 jobs. Diagnose actual errors, fix semantics-preservingly and work an independent non-UI lane during CI.
2. Memory: retained row/event provenance, CAS ABA/expiry, genuine COMMIT-UNKNOWN manual triage, foreign WAL writers, multi-owner consistency. Local hashes are not authenticated custody.
3. Planner: independent persistent READ input/hash custody, crash joins and Windows publication gaps; do not infer replay/dispatched reads from a receipt.
4. Registry, PermissionGate, occurrence/replay fences, audit-before-action, trusted-clock and mock-only disconnected executor integration after lower-level exact-head GREEN.
5. Privacy-safe Personal Context lifecycle, Proactive scheduler and Observation noncapturing fixtures; free-only V3 guard review. PR #5/#8/#9 remain Draft/unmerged, UI paused. ARK/JARVIS/V3 **NOT_PASSED**.

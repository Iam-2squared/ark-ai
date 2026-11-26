# ARK AI Run963 — opt-in Memory identity controls, SQLite recovery fixtures and Registry CI repair

**Report UTC:** 2026-11-18T08:16:05.206Z (ordinary reporting time, not a trusted authority clock).
**Work basis:** `13028018015fadc1db511afa2d2d8b1d73f509ac` (Run962 technical report on Draft PR #8; its checkpoint not yet written when this run started).
**Report write basis:** `1b511ee1676bde86dd8a9a9d18ef00346520dcf8`.
**Overall ARK/JARVIS:** **NOT_PASSED**. All work offline, local/disconnected/synthetic and non-UI.

## Four coherent packages / 72 newly authored parametrized cases

1. **Memory generation-CAS Unicode/ASCII control admission.**
   [Source `62e44f6b`](https://github.com/Iam-2squared/ark-ai/commit/62e44f6b2e8b739b97928fde1008b041cfcc87a6) limits *optional* `observe_memory_generation_for_cas` and `generation_fenced_memory_update` identities before request hashing, SQLite reads or writes. Both source and scope identifiers refuse C0/DEL and the 15 problematic Unicode line/direction format marks (U+0085, U+061C, U+200E/U+200F, U+2028–U+202E, U+2066–U+2069). Frozen Memory v1 `MemoryScope`/`MemoryWrite` and schema are unchanged. [58 authored tests `dc34ec68`](https://github.com/Iam-2squared/ark-ai/commit/dc34ec68562f1c246d54854fe4bd07776e466949): 19 marks × owner/namespace/source plus one valid Japanese identity with successful fenced update. Failed attempts leave the event journal unchanged and grant no authority.
2. **Retained privacy revocation under historical WAL readers.**
   [8 authored tests `ea30d521`](https://github.com/Iam-2squared/ark-ai/commit/ea30d5210511d7e9e06e5cf0b21101497dcc91be): one/two owners × PASSIVE/FULL/RESTART/TRUNCATE checkpoints; pinned read snapshots remain historical, but separate writers must reject stale revocation witnesses. After cold reopen the latest revocations are visible and context release remains denied. Synthetic SHA labels only.
3. **Finite Proactive quarantine terminal state.**
   [6 authored tests `c5186271`](https://github.com/Iam-2squared/ark-ai/commit/c518627193ec92876c4004f1ef6f63e7823820cd) and [fixture-WAL correction `1b511ee1`](https://github.com/Iam-2squared/ark-ai/commit/1b511ee1676bde86dd8a9a9d18ef00346520dcf8): one/two/three recurrence slots × PASSIVE/TRUNCATE. Out-of-order, stale and exhausted slots remain denied after each cold restart, with no notification/execution/replay flag. WAL is explicitly activated before checkpoint assertions; the preliminary test commit by itself did not guarantee WAL mode.
4. **Root-cause CI fix for Run962 Registry format-scope tests.**
   [Source `94964c3f`](https://github.com/Iam-2squared/ark-ai/commit/94964c3fc71df7a8fc3266e9df6dfc66225df0ed) applies the existing opt-in Unicode formatting-control rule to the two missing `ToolRegistry.resolve`/`bind` scope ingress checks. [Run962 CI #44263561593](https://github.com/Iam-2squared/ark-ai/actions/runs/44263561593) Ubuntu 3.11 yielded **17,720 PASS / 33 FAIL / 1 SKIP** (three Ubuntu jobs FAIL at inspection), chiefly 30 unguarded scope cases and 3 indirect one-shot error-message mismatches. No tests were deleted or weakened; the one-shot remains process-local and does **not** authorize real actions. This is a semantics-preserving correction, not PASS evidence.

## Evidence and current limits

- Prior Run961 `44ddda2276e81cee648720117e6990324cf5ca9b`: [CI #44254482936](https://github.com/Iam-2squared/ark-ai/actions/runs/44254482936) **COMPLETED GREEN 6/6** (Windows and Ubuntu × Python 3.11–3.13), strictly before Run962/963 changes.
- First Run962 report HEAD `13028018`: [CI #44263561593](https://github.com/Iam-2squared/ark-ai/actions/runs/44263561593) **FAIL**, see above. The correction `94964c3f` has [new CI #44265212141](https://github.com/Iam-2squared/ark-ai/actions/runs/44265212141), queued at last sample.
- Memory source [#44264571069](https://github.com/Iam-2squared/ark-ai/actions/runs/44264571069) IN PROGRESS; Memory 58 tests [#44264691007](https://github.com/Iam-2squared/ark-ai/actions/runs/44264691007) IN PROGRESS; Privacy [#44264854573](https://github.com/Iam-2squared/ark-ai/actions/runs/44264854573) QUEUED; Proactive initial [#44265072253](https://github.com/Iam-2squared/ark-ai/actions/runs/44265072253) QUEUED; corrected Proactive [#44265261934](https://github.com/Iam-2squared/ark-ai/actions/runs/44265261934) QUEUED at last sample.
- **72 test cases AUTHORED; no exact final HEAD six-job GREEN claim.** GitHub Actions is auto-triggered on normal Contents commits, without manual workflow reruns. No local full pytest, physical PC, actual GPU, network, OS tool dispatch, media capture or live external adapter was used.

## Hard boundaries and next priority

Frozen V1/V2/Local UI/Launcher evidence; Observation v1 and V3 Contract 1; contamination, provenance, reproducibility, review and protected final-evaluation gates untouched. Draft PR #5 protected/unmerged. Draft UI PR #9 paused/unmerged/untouched. No new UI or frontend, paid APIs/GPU/services, actual Candidate/model weights/training/promotion, credentials, protected V2 evaluation, destructive effects, real tool execution, force push, raw Git write, or main merge. Local SHA/SQLite snapshots do NOT authenticate external custody, consent, trusted time or exactly-once effects.

**Next plan / 今後の方針:** (1) certify CI for exact latest HEAD, repair any remaining real failures without weakening safety; (2) Memory prehydration/event integrity, WAL/SHM last-close and unknown COMMIT; (3) Planner persistent ambiguous RUNNING quarantine and registry-bound PermissionGate with durable audit-before-action, disconnected/mock-only until lower-level exact-head GREEN; (4) Privacy retained veto, Proactive recurrence, Observation fixture provenance, startup readiness and V3 free-only identity/path/reproducibility.

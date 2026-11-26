# ARK AI — Run730: non-UI WAV CI repair, PCM custody, Memory triage, READ publication, Context privacy

**Recorded (administrative JST):** 2026-11-09T15:01:11.077+09:00. This is not a trusted action clock or user authorization.  
**Branch/PR:** `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), open/unmerged.  
**Exact initial work-basis HEAD:** `f77d74a4363b70286aa478f936d11e857af75020` (Run729 canonical status).  
**Exact last confirmed source/test HEAD before report:** `fc1765b93ae35c7d980985c3aecd14b4eb6e2682`.  
**Scope:** zero-cost, non-UI, synthetic/local-only. Frozen V1/V2/Local UI/Launcher and protected V2 final evaluation unchanged. Draft PR #5/PR #9 untouched. No real tool dispatch, external model, microphone, Candidate, GPU, identity/consent assertion, paid compute or main merge.

## A — Diagnose exact Run729 failure and repair inherited WAV tests

[Run729 canonical CI #42564011022](https://github.com/Iam-2squared/ark-ai/actions/runs/42564011022) **6/6 FAIL**; Ubuntu Python 3.11 log: **11,510 PASS / 2 FAIL / 1 SKIP**; Windows Python 3.11 log: **11,449 PASS / 2 FAIL / 62 SKIP**. Both cases in `tests/test_offline_wav_request_slot_custody_run635.py` still expected late `request identity|constructed WAV` rejection after forging a digest callback. The production guard correctly rejects the substituted `hashlib` module **before private WAV data reaches the callback**, with `WAV codec or digest implementation changed before private bytes`.

[Normal Contents API test fix `3fb4530`](https://github.com/Iam-2squared/ark-ai/commit/3fb453021d0874b21f74b1709b8f58fec2c55f35) changes the expected denial and **additionally asserts neither the forged digest nor reflected getter executes**. No production refusal relaxed.

## B — Offline PCM amplitude carrier/codec/privacy preaccess

[Source `01cf813e`](https://github.com/Iam-2squared/ark-ai/commit/01cf813e129fd949241c4cd07075b7022281b0af) pins original `hashlib`/`json` modules and SHA/JSON implementations, checksum regex, digest domain, maximum byte/window budgets, all private PCM request slots/hooks, amplitude window/result slots/constructors and deny-only authority descriptors. Recheck epochs before every window progression, after digest serialization, and before returning a denial-only result. Private bytes never enter a substituted SHA callback.

[New synthetic tests `11d48b5`](https://github.com/Iam-2squared/ark-ai/commit/11d48b5210159ee60ca2a040d640c9dcc6ecbb56): **14 parameterized malicious replacements + 1 normal control = 15 new cases**; commits `5e0dc20` and `43e7e42` correct lint without semantics changes. No live microphone, ASR or authorization.

## C — Manual-only Memory COMMIT-UNKNOWN triage helper custody

[Source `f67ef3e`](https://github.com/Iam-2squared/ark-ai/commit/f67ef3e7a15dca4275693c9dace7e3be68f3844f) pins import-original `sqlite3` module, Memory identity derivation, retained token extraction, generation-input and token validators **before reading caller-private proposed content or SQLite**. Existing independent callback-fault injection seams (`_snapshot`, `_row_hash`, `_digest`) remain available for their focused established tests. Local matching row/history never proves caller attribution, consent, trusted clock or safe automatic retry.

[New tests `4346e35`](https://github.com/Iam-2squared/ark-ai/commit/4346e3575d81c8152844bb25d70a604901a3b132): **five substituted helpers + one benign manual-only local case = six new cases**. Assert hostile callback and private SQLite reader are never entered on protocol drift. The existing SQLite Memory v1 schema and API remain untouched.

## D — Planner READ manifest write-once publication byte recheck on both OS families

[Source `9437a01`](https://github.com/Iam-2squared/ark-ai/commit/9437a017d441107d987ff1a91ee5f9974e37d7ac) extends complete **reopen and byte equality after initial fsync/directory publication to POSIX as well as Windows**. Checks named file identity and stable same-descriptor epochs, preserving the Windows caveat about differing descriptor/path creation timestamps. POSIX also binds the created/named file epochs. Detecting a changed artifact refuses a success receipt; the unknown artifact is **not** deleted, replaced or automatically retried. This is not independent authenticated custody or a cross-file transaction.

[Three tests `da8f8ff`](https://github.com/Iam-2squared/ark-ai/commit/da8f8ffeb127c5480357e568e6190448cdb540ef): one confirms the post-publication named reread on every platform; one injects a readback failure and verifies preservation/creation refusal; one introduces same-size local corruption during publication and requires refusal. No backend READ run or automatic replay follows.

## E — Private Personal Context protocol format/limit custody

[Source `f728f29`](https://github.com/Iam-2squared/ark-ai/commit/f728f29fa79e09be80e161e5a0bcbfb985d3f056) pins original digest/JSON modules, digest/record regex objects, separation domain, time ceiling and record/content/serialized bounds before processing the caller's local private fixtures. Existing private field/constructor/privacy denial guards and final rechecks remain unchanged. This does not authenticate owner identity, consent, retention, revocation or external disclosure.

[New tests `fc1765b`](https://github.com/Iam-2squared/ark-ai/commit/fc1765b93ae35c7d980985c3aecd14b4eb6e2682): **10 tampering surfaces × build and verify + one successful non-authorizing control = 21 new cases**. No actual account connection or real profile acquisition.

## CI provenance and gating, as observed while authoring

- **Initial prior source/checkpoint CI #42564011022:** completed **6/6 FAIL**, exact two inherited WAV tests, as above.
- **Intermediate CI #42569623297:** completed **6/6 FAIL** at Ruff E501, one 104-character line in newly added PCM test. Repaired in [commit `43e7e42`](https://github.com/Iam-2squared/ark-ai/commit/43e7e425a2b37f405eb81ca0de964c1ed7f6d38c); the incomplete intermediate HEAD is NOT used as regression evidence.
- **Corrected four-package HEAD `43e7e42`, CI #42570056717:** at last read, Ubuntu Python 3.11, 3.12 and 3.13 **GREEN**, Windows three matrix jobs **IN PROGRESS**. This is **not** a GREEN assertion for later work.
- **Latest source/test HEAD `fc1765b`, CI #42570478761:** **QUEUED** at last read, not a PASS. New 45 parameter-expanded cases, 4 non-UI production modules changed and 4 new test files require final exact-head Windows/Ubuntu validation.
- The report and canonical checkpoint will produce distinct later commits and corresponding CI runs. No duplicate equivalent workflow was manually dispatched. No local full pytest run or actual hardware/model benchmark; final CI conclusions must be rechecked.

**Safety/provenance limits:** local module/descriptor comparison cannot enforce a Python sandbox or independently authenticated provenance. SQLite/file witness digests do not prove user consent, original writer, trusted time, true exactly-once side effects, or external outcomes. All execution remains disconnected/mock and advisory. **Overall ARK/JARVIS/V3: NOT_PASSED.**

## Next plan / 今後の方針

1. Confirm exact latest source and checkpoint-result CI in all six OS/Python jobs; inspect *actual* failed job logs if needed, repairing narrowly while retaining early refusal.
2. Continue Memory CAS/ABA/expiry/coherent snapshots and manual-only COMMIT-UNKNOWN; preserve event history and independent retained witnesses.
3. Advance Planner retained READ source custody and crash-safe publication/UNKNOWN quarantine and terminal propagation.
4. Integrate ToolRegistry, exact-type PermissionGate, durable occurrence and audit-before-action only with a **disconnected mock executor** after exact lower-layer GREEN.
5. Keep privacy-safe Context/proactive/observation back-end work moving; V3 only free/offline approval/path/identity/reproducibility review. Draft PR #5/#9 and frozen contracts remain untouched.

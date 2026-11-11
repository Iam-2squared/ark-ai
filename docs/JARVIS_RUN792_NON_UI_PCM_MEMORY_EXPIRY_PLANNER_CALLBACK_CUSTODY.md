# Run792 — Non-UI, free-only source/receipt preaccess and Planner recovery custody

## Work basis and change isolation

- Initial GitHub PR #8 HEAD: `4dfb39c47990cdb7f44f7c8a6eb8f82842fd99eb`.
- Prior exact-HEAD CI: [#43016042021](https://github.com/Iam-2squared/ark-ai/actions/runs/43016042021) individually checked **6/6 GREEN**, on Windows and Ubuntu with Python 3.11, 3.12, 3.13.
- All changed paths are non-UI and remain on `research/jarvis-foundations` / PR #8 (Draft, unmerged). PR #5 and PR #9 are untouched.
- No real device, microphone, camera, paid API/GPU, external backend, protected V2 evaluation, Candidate artifact, user authority, or main merge was used.

## Package A — disconnected PCM fixture request preaccess

`src/ark/offline_pcm_mono16.py` now statically pins the original
`OfflinePcmConvertRequest` class and its seven stored input fields plus four
construction/lookup hooks **before reading any PCM or provenance field**. The
same check repeats at each existing request epoch; it does not change DSP
arithmetic or turn the fixture into authenticated audio.

`tests/test_offline_pcm_request_preaccess_run792.py`: **10 negative
fault-injection variants + 1 successful local-only conversion**. A forged
getter/method is counted but must never be called, including an originally
absent `__getattr__`. `__new__` is pinned by production but is not mutated
inside a shared pytest process: GitHub CI exposed CPython constructor-slot
poisoning after monkeypatch restoration, causing unrelated audio tests to
fail. The regression fixture was repaired without weakening production guard.

## Package B — retained Memory expiry receipt budget and shape

`src/ark/memory/expiry_candidate_preview.py` now rejects clearly
mismatched or malformed retained preview evidence **before private SQLite
access**: exact integer time/limit/count, valid bounds, exact bool
`has_more`, valid lowercase 64-hex receipt digests, matching retained
preview digest and source read time. No purge or erasure is authorized.

`tests/test_memory_expiry_retained_preaccess_run792.py`: **10 malformed
receipt cases + 5 malformed clock/budget cases + 1 successful read-only
recheck**. Invalid cases supply a trap object in place of a private store to
ensure that its fields are never accessed.

## Package C — detached Planner journal callback custody

`src/ark/agency/disconnected_planner_epoch_recheck.py` pins its own
import-original recovery-denial precheck and `SyntheticPlanTail.assert_shape`
before executing either as a callback; missing or replaced callbacks fail
closed before journal access. The existing two-sweep recovery logic and
terminal/UNKNOWN interpretation remain unchanged.

`tests/test_planner_recheck_callback_preaccess_run792.py`: **2 negative
callback traps + 1 successful local-only diagnostic**. No Planner step is
dispatched or automatically replayed.

## Verification discipline

**30 submitted cases total** across the three packages. Source and test files
were saved using the ordinary GitHub Contents API with fresh file blob SHAs and
fresh PR HEAD checks before each write. No local `pytest`/`ruff` result is
claimed because repository code execution is not mounted in this automation
runtime. GitHub Actions results are independent; queued/in-progress runs
must not be reported as GREEN.

Known workflow IDs at report preparation:

- PCM tests head: [#43023023816](https://github.com/Iam-2squared/ark-ai/actions/runs/43023023816), **Ubuntu pytest FAIL** with `TypeError: object.__new__() takes exactly one argument` after an injected `__new__` test contaminated the process. Root cause verified from individual job logs; all historical tests remain unchanged.
- Memory tests head: [#43023249346](https://github.com/Iam-2squared/ark-ai/actions/runs/43023249346), **QUEUED**.
- Planner tests head: [#43023456283](https://github.com/Iam-2squared/ark-ai/actions/runs/43023456283), **QUEUED**.
- First PCM test correction head: [#43023538738](https://github.com/Iam-2squared/ark-ai/actions/runs/43023538738), **QUEUED** at previous read; second attempted restoration was also proven insufficient in an isolated CPython reproduction. The final test revision simply does not mutate `__new__` in-process; **latest exact-HEAD CI remains unconfirmed**.

Further work: inspect six individual jobs on latest code; repair any actual
failure by minimal ordinary Contents-API changes; keep source packages
isolated while CI is running. Memory COMMIT-UNKNOWN and CAS/ABA,
Planner durability and mock-only registry/permission/audit coordination
remain higher-level unfinished foundations.

Frozen V1/V2/Local UI/Launcher evidence and V3 Contract 1 were not changed.
JARVIS/ARK/V3 PASS remains **NOT_PASSED**. No claimed external authority,
source attestation, consent, trusted clock, exactly-once real-world effect,
cross-store atomicity or integration readiness.

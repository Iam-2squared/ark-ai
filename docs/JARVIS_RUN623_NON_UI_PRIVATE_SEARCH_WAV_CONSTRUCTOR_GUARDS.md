# Run623 — Constructor-origin guards for offline search and WAV metadata (non-UI)

**Scope:** `research/jarvis-foundations` / [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), based on Run622 checkpoint `1e06312f9bd95bdd0d5b656d7d15124928c07383`. Everything uses offline fixture input and local Python. **No real private Memory, microphone, ToolBackend, external dispatch, UI/frontend work, model inference, paid service, protected evaluation, or main merge.** These synthetic checks are not proof of operator authorization or consent.

## Package A — detached lexical index constructor custody

- `src/ark/offline_text_index.py` at source commit `64f0d56069c159a6fd79e92fac0220de6c538226`: pin import-time original `OfflineIndexHit.__init__` and `OfflineIndexResult.__init__`, alongside existing original false-only authority descriptors; reject replacements at ingress, after token/hash callbacks, and before object construction. No index API, payload format, retained data, or persistence changes.
- `tests/test_offline_text_index_constructor_custody_run623.py`, commit `7a1c0a9ef94b37780e1005acc2c4976405430976`: six authored parameter-expanded cases: forged result/hit initializer before admission, during tokenization, during result digest, and normal denial-only baseline. No forged initializer may execute.
- Exact intermediate test HEAD CI [#41963611098](https://github.com/Iam-2squared/ark-ai/actions/runs/41963611098) **6/6 GREEN observed**. Note this validates only that intermediate HEAD, not later changes.

## Package B — private synthetic Context search constructor custody

- `src/ark/offline_context_search.py` at `4e15a7f4ba1924dc119ebcc2dddd0aafb468ee35`: pin original result/hit classes and `__init__` before private fixture read, after callback epochs and before constructing search hit and preview; keep original denial descriptors. Does not authorize content export or memory disclosure.
- `tests/test_offline_context_search_constructor_custody_run623.py`, `4eff21cf75a45d5c943433474cde77b026c4e8c0`: six authored parameter-expanded cases: forged preview/hit constructors before admission and during query UTF-8 processing, forged preview after digest, normal local-only false-authority baseline.
- At an intermediate observation, [#41963702675](https://github.com/Iam-2squared/ark-ai/actions/runs/41963702675) had five GREEN / one Windows in progress, and [#41963780985](https://github.com/Iam-2squared/ark-ai/actions/runs/41963780985) had Ubuntu three GREEN / Windows three in progress. These are **not** final exact-head results.

## Package C — disconnected PCM/WAV metadata constructor and denial origin

- `src/ark/offline_pcm_wav.py` at `33d4fd6f37fffa58dad50c765994fa3fe3091595`: pin import-original `OfflineWaveReview.__init__` and four denial descriptors and statically reject rebindings before caller-supplied bytes are reviewed or receipt instantiated. This intentionally moves rejection ahead of hostile property getter execution; normal WAV fields/formats remain unchanged.
- `tests/test_offline_pcm_wav_import_epoch_run623.py` at `6ae5809956cd775c8dfa8db312d9c1d9cea8a0e3`: seven authored parameter-expanded cases for forged initializer before/during source digest, all four forged false-only denial getters, and a valid 80-frame synthetic WAV.
- Three older WAV tests repaired for earlier fail-closed semantics: `tests/test_offline_wav_denial_descriptor_custody_run539.py` (`a03d7cf3d3ba531c9e1832434708029144a5e280`), `tests/test_offline_wav_post_authority_run496.py` (`1f8d1717d9685dbfd16395b5257b760ae690d603`), `tests/test_offline_pcm_wav_result_custody_run481.py` (`bd0c9e0e9b623d0b25b26be2de6319cf5f62da3c`). They now require the forged callback not to run, while preserving refusal of authority/spoofed result.
- Intermediate CI [#41964286419](https://github.com/Iam-2squared/ark-ai/actions/runs/41964286419), [#41964326861](https://github.com/Iam-2squared/ark-ai/actions/runs/41964326861), [#41964348468](https://github.com/Iam-2squared/ark-ai/actions/runs/41964348468), and [#41964457950](https://github.com/Iam-2squared/ark-ai/actions/runs/41964457950) **six FAIL at Ruff F841**: two unused local aliases left after moving descriptor checks to import-pinned helper. Normal guarded source correction at `7616ffbab756c80c5a71bc7bce144cc8d3bd6b20` removed exactly those two aliases; source semantics and constructor checks remain unchanged. New exact-head CI needed; no claim of GREEN until observed.

## Counts and limitations

- **Three meaningful source+test work packages**, **19 new parameter-expanded pytest cases authored (6+6+7), not a local PASS count**, three preexisting WAV test files updated. All production changes are non-UI, opt-in/local fixture analysis.
- Local full pytest and Ruff were **not executed**; repository inspection, source edits, and CI evidence used normal GitHub connector and ordinary Contents API. GitHub Actions executes its standard matrix automatically. Do not equate a successful earlier CI run with this final checkpoint HEAD.
- Earlier Run622 exact checkpoint [#41958903563](https://github.com/Iam-2squared/ark-ai/actions/runs/41958903563) was independently observed **GREEN in all Ubuntu/Windows × Python 3.11/3.12/3.13 jobs** at this invocation's start.
- False-only result flags are not authenticated consent, source custody, real-time device capability, protected training approval, or legal/license resolution. This is Python-level synthetic fault-injection defense; it is not isolation from arbitrary code already running in-process.

## Gates / next

Keep main and frozen V1/V2/Local UI/Launcher and V3 protected contracts unchanged. PR #5/#8/#9 Draft/unmerged, PR #9 and all new UI work PAUSED. V3 weight/HF immutable identity and human dataset/reviewer/approval/budget evidence unresolved; no paid compute, Candidate, protected final evaluation, real physical-PC tool, actual sensor access, credentials, destructive action or automatic UNKNOWN WRITE retry. **ARK/JARVIS/V3 NOT_PASSED.**

**Next:** (1) verify latest exact-source/head CI and repair only logs-proven defects; (2) Memory COMMIT-UNKNOWN row/event/CAS/snapshot manual reconciliation; (3) independent Planner crash-recovery and PermissionGate/immutable ToolRegistry/trusted audit before *mock* action; (4) privacy-safe context, proactive, observation evidence; (5) preserve all frozen gates and UI pause.

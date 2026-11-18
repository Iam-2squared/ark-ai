# ARK AI Run976 — opt-in identity admission before fixture hashing, proactive state, and private context

**Work basis:** `43ec54c31d59c67bb081b9847170cb13e2602649` (Run975 checkpoint).  
**Executable source/test result:** `7eff4eb4663c30d727085860dbc4f5e9bb9154e4` (before this report).  
**Branch:** `research/jarvis-foundations`, Draft PR #8, unmerged.  
**Safety:** local fixture only, no frontend work, no live tools, no real notifications, no paid services, no protected evaluations, no Candidate training, no main merge. **ARK/JARVIS NOT_PASSED.**

## Scope and root cause

Three *optional*, non-UI boundaries allowed visually ambiguous identifier text while hashing private fixture inputs, preparing durable synthetic scheduling markers, or deriving ephemeral Personal Context policy identities. Examples include C0/DEL, C1 terminal escapes, bidirectional overrides/isolate marks, zero-width format characters, and Unicode line separators. These labels can look equal in a log while binding different hashes. No claim is made about a demonstrated exploit or a malicious real actor. Direct frozen `ObservationEnvelope v1`, `Memory v1`, `ToolCall v1` and other preserved schemas are not modified.

## Saved independent source + test packages

1. **Observation in-memory fixture prehash metadata:** [source `e8dc0dba5`](https://github.com/Iam-2squared/ark-ai/commit/e8dc0dba5286a1f25ec0aa3e1bbe9671d65dbda6), [tests `066447c8f`](https://github.com/Iam-2squared/ark-ai/commit/066447c8fe364cce1f6932c72e832dd0a850b0d5). Text and binary adapters reject spoofable source/privacy controls after the bounded string admission but **before raw content hashing**. **34 newly authored parameterized cases**, including two valid multilingual/digest-only cases; rejected inputs assert no private hash helper call.
2. **Proactive offline policy identity:** [source `2aab70673`](https://github.com/Iam-2squared/ark-ai/commit/2aab706739913bbd6abf212caa9161c9b7c224ac), [tests `743985a8c`](https://github.com/Iam-2squared/ark-ai/commit/743985a8c3977b7285e5236e16a4b9383b440823). Local-only policy identifiers reject the same controls before hash and SQLite marker preparation. **41 newly authored cases**, including reflected post-construction tampering with a zero-row assertion and clean multilingual inert marker. There is no real timer authority or notification.
3. **Ephemeral Personal Context selection policy:** [source `2917c54ab`](https://github.com/Iam-2squared/ark-ai/commit/2917c54ababd33538538890581055fff045c7580), [tests `7eff4eb46`](https://github.com/Iam-2squared/ark-ai/commit/7eff4eb4663c30d727085860dbc4f5e9bb9154e4). Refuse control-bearing policy revisions before private snapshot review or content-derived hash processing. **19 newly authored cases**, including reflected mutation and valid UTF-8 Japanese policy revision. No private context was uploaded or exported.

**Total newly authored regression cases: 94.** Cases are source additions, not a test PASS certificate until exact-head CI is complete. No new credentials, accounts, external compute, hardware capture, or dispatch paths were introduced.

## CI/evidence boundaries

- Run975 exact checkpoint `43ec54c31d59c67bb081b9847170cb13e2602649`: [Actions #44385071884](https://github.com/Iam-2squared/ark-ai/actions/runs/44385071884), **GREEN 6/6** Ubuntu/Windows × Python 3.11/3.12/3.13 (observed this run).
- Observation source `e8dc0dba5`: [#44394775595](https://github.com/Iam-2squared/ark-ai/actions/runs/44394775595) — IN PROGRESS at report preparation.
- Proactive source `2aab70673`: [#44395056771](https://github.com/Iam-2squared/ark-ai/actions/runs/44395056771) — IN PROGRESS at report preparation.
- Observation test head `066447c8f`: [#44395616909](https://github.com/Iam-2squared/ark-ai/actions/runs/44395616909) — IN PROGRESS at report preparation.
- Proactive test head `743985a8c`: [#44395873684](https://github.com/Iam-2squared/ark-ai/actions/runs/44395873684) — IN PROGRESS at report preparation.
- Personal Context test head `7eff4eb46`: [#44396483982](https://github.com/Iam-2squared/ark-ai/actions/runs/44396483982) — QUEUED/IN PROGRESS at report preparation. The intermediate Personal Context source commit has its own auto CI.
- Automatic GitHub CI is not duplicated manually. A later report/checkpoint HEAD launches its own CI; its six-job result is not inferred from previous HEADs.

## Open blocking gates / next plan

1. Confirm exact latest source/test/report/checkpoint SHA in Actions (6/6). Inspect any failure and fix only via permitted normal GitHub Contents writes.
2. Prioritize Memory WAL/SHM and CAS/ABA/COMMIT-UNKNOWN handling, then Planner durable terminal propagation/restart and ToolRegistry/PermissionGate/one-shot approval/pre-action audit with disconnected mock only.
3. Continue Personal Context revocation/retention controls, Proactive occurrence/replay and trusted clock constraints, Observation fixture provenance contracts, free-only V3 path/identity/reproducibility guards. Avoid frontend and protected evaluation.
4. Preserve all frozen V1/V2/Local UI/Launcher evidence, protected V2/V3 evaluation, Draft PR #5 and paused Draft PR #9. Main merge, Candidate promotion, live execution and physical-PC validation remain blocked.

Synthetic fixture integrity and a local hash are *not* independent provenance, authenticated consent, a trusted clock, or proof of externally exactly-once action delivery.

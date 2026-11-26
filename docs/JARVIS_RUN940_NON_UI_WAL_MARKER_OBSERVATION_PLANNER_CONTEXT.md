# ARK AI Run940 — non-UI WAL barrier repair, Observation/Planner UTF-8 limits, Context cold privacy veto

**Recorded at JST:** 2026-11-17T18:53:32+09:00 (reporting clock, not a trusted audit or action clock). **Overall: NOT_PASSED.** Only free, public-repo CI, disconnected/synthetic non-UI development.

## Exact repository basis and gates

- Work started from Run939 checkpoint `7111229e3a45a46242270f487a0b9a967f36cc81` on `research/jarvis-foundations`, Draft PR #8. Main `7a843f17eb96ed13d66f23b58b06406b3002e405` unchanged on the prewrite check.
- Protected V3 Draft PR #5 and paused frontend Draft PR #9 remain outside this work. No frozen V1/V2/Local UI/Launcher contracts or evaluation evidence was changed. No main merge, user-data mutation or external action.

## New work (4 independent packages)

1. **WAL test signal repair:** `db669c40c660565638ebb042d600b771f2eeab32` changes only `tests/test_memory_wal_pinned_expiry_scope_run939.py`. Its child used `Path.write_text` to publish its observation, but parent regarded **file existence** as proof that the write was complete. A reader can see the newly created **empty file** before the child writes text. Use a unique `.pending` file followed by atomic same-directory `Path.replace`, preserving the child transaction and all substantive WAL, CAS, scope and event assertions. This directly addresses observed CI failures on Ubuntu 3.13 and Windows 3.11, not a Memory production-code failure.
2. **Observation exact limits:** `fb1659147a2b61daf0364420e6daf5c0d0040468` adds `tests/test_disconnected_observation_utf8_and_payload_edges_run940.py`: 12 parametrized fixture cases for labels of 1,024 vs 1,028/4,100 UTF-8 bytes, ASCII 4,096-byte lengths, and all four modalities' exact 65,536-byte payload limit. Assert content digest only, no retained raw payload and no sensor access. No frozen Observation v1 change.
3. **Planner exact graph limits:** `bc73d206d47aed9d36d3c800c925150d1a0ba2b4` adds `tests/test_planner_utf8_label_byte_edges_run940.py`: 10 parametrized tests at exactly 4,096 UTF-8 bytes vs 4,100, on step/dependency labels plus reflected post-constructor overwrites. Only inert standalone PlanGraph; no tool backend.
4. **Context retained veto after restart:** `a2a1009f2693fde6228ac22937852b6a0de269fb` adds `tests/test_personal_context_cold_retention_revocation_run940.py`: 2 parametrized cases where a synthetic scope is revoked and the independent Memory/veto SQLite files are reopened. Review must continue reporting `revoked=True` and deny all context-use/deletion/erasure authority without confusing owner and namespace scope boundaries. This is negative-only privacy evidence, not proof of consent or cross-store atomicity.

**24 parametrized regression cases authored; one pre-existing flaky test's handshake corrected.** No production source, frozen evaluations, protected V3 scoring, candidate weights, UI/frontend or network/tool adapters changed. Only synthetic, local files/bytes, and inert planning were used.

## Observed CI and limitations

- Prior Run939 exact checkpoint HEAD `7111229e3a45a46242270f487a0b9a967f36cc81`: [CI #44050391449](https://github.com/Iam-2squared/ark-ai/actions/runs/44050391449) **COMPLETED, 5/6 GREEN, 1 Windows Python 3.11 FAIL**. Windows failure: a zero-length `observed` marker read in `test_memory_wal_pinned_expiry_scope_run939.py` despite child subsequently writing its marker; no underlying Memory corruption was established. An earlier Personal Context-head CI [#44049914211](https://github.com/Iam-2squared/ark-ai/actions/runs/44049914211) independently saw the same empty-marker flake under Ubuntu 3.13. The tests' parent/child handshake was corrected without changing retention or safety checks.
- Repair [CI #44058974652](https://github.com/Iam-2squared/ark-ai/actions/runs/44058974652): **IN PROGRESS** at last read.
- Observation [CI #44059290045](https://github.com/Iam-2squared/ark-ai/actions/runs/44059290045): **IN PROGRESS** at last read.
- Planner [CI #44059400189](https://github.com/Iam-2squared/ark-ai/actions/runs/44059400189): **IN PROGRESS** at last read.
- Context [CI #44059579641](https://github.com/Iam-2squared/ark-ai/actions/runs/44059579641): **QUEUED** at last read.
- **All-six exact-new-HEAD GREEN is not yet established.** Do not present new tests as confirmed PASS. No local full pytest was possible; public repo GitHub CI is the verification path. A later docs/checkpoint commit will initiate distinct CI. No duplicate workflow dispatch was requested.

## Authorization and trust boundary

No paid API, paid/external GPU, purchased service, new credential/account, physical-PC action, protected final V2 evaluation, generated Candidate weights, model promotion, live backend, irreversible operation, UI feature or main merge. Frozen evidence and controlling PR gates unchanged. Synthetic WAL histories, local hash receipts and locally persisted revocations are not trusted clocks, authenticated human approval, external exactly-once evidence or independent archival custody.

## Next plan / 今後の方針

1. Evaluate the corrected marker's exact-head CI, then all newly authored cases across Windows/Ubuntu/Python 3.11–3.13. If any FAIL, inspect actual logs and repair the smallest test/source issue by ordinary Contents API while keeping fail-closed behavior.
2. Audit other independent-process tests that publish a marker with a non-atomic `write_text` but release on file existence; replace race-prone handshakes only after their current code path's CI is GREEN.
3. Resume bounded Memory WAL/SHM, CAS/ABA, coherent event snapshots and Planner COMMIT-UNKNOWN/manual-only recovery while independently advancing exact ToolRegistry/PermissionGate, persistent audit-before-action and disconnected Mock Executor.
4. Continue privacy-safe Personal Context, Proactive, Observation and free-only V3 guard work. Preserve all human-approval, evaluation, candidate and UI-stop boundaries. ARK/JARVIS **NOT_PASSED**.

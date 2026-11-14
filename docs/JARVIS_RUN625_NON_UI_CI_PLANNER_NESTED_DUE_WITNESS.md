# Run625 — Non-UI CI repair, Planner exact nested epochs and due-witness constructor custody

**2026-11-05 JST.** This is a **local-first, disconnected foundation** change on Draft PR #8, not a JARVIS PASS, not user/device authorization, and not evidence of real backend dispatch or external exactly-once effects.

## Work packages saved (ordinary GitHub Contents API only)

1. **Prior Run624 CI failure repaired, no semantic change.** The Run624 checkpoint's workflow [#41970333907](https://github.com/Iam-2squared/ark-ai/actions/runs/41970333907) failed all six Ubuntu/Windows Python 3.11–3.13 jobs at Ruff `I001`, before pytest. The exact unformatted two-name import in `tests/test_write_restart_original_constructor_custody_run624.py` was split onto separate lines; source logic and security policy were untouched. First Run625 commit `d3d3e42e10823934f23fdfcb37cc21c95a783ed5`, test blob `3a3e30f42a06d1c09cb19611bb1a6e5b09088a9e`. **Do not claim the previous red run is green.**

2. **Planner journal preserves original nested identity across reentrant digest callbacks.** `SyntheticPlanJournal._pin_topology` now retains the original PlanStep ID and nested ToolCall tool/capability/scope references as well as the existing call, dependencies, arguments and canonical request digest. `_assert_topology_epoch` rejects distinct but value-equal replacements: identical SHA/request-ID values do **not** establish original carrier custody. No persistence schema or replay rule changed. Source commit `880b329c829da1bb415694c0e15d747ea54c5f95`, blob `bdfd1845db1584de2921e50f12921fa7e03c31ff`. New `tests/test_planner_journal_nested_field_epoch_run625.py` has **12 authored, parameter-expanded cases**, checking four fields during recover/append digest callbacks and four during an append snapshot callback; each verifies a refused append did not publish a local event and that recovered RUNNING remains non-dispatchable. Test commit `75ad3795d90369e8d761710d6a481fbc927ec4d0`, blob `112070b48ffb1edb8715f84911e63dd15271fc81`.

3. **Durable due-slot witness constructor pinned before executing synthetic code.** `_require_original_witness_denial` now rejects `DueReservationWitness.__init__` substitution alongside the preexisting import-original class/false-only authority descriptor check. This covers genesis, reservation preflight, digest reentrancy, and read-only SQLite scans without changing the synthetic due-slot schema or enabling notifications. Source commit `4fbd21283056192c8ca9a03933c2d236ec949cef`, blob `11547411a80685165abac250de66af2cdcb2fc9b`. New `tests/test_due_witness_original_constructor_run625.py` has **4 authored cases** for preinstalled and callback-time substitutions, assert no hostile initializer was invoked and no reservation was committed in the preflight case. Test commit `f53b3779750d4abc0d9b3bb8908ece3355a69f6f`, blob `9178886d4cccb9d8ea1df8741c77e43fa2ebcb0e`.

**Total:** 3 coherent work packages, **16 new parameter-expanded pytest cases authored** (12 Planner + 4 due witness), and 1 prior test import-format repair. The authored count is **NOT** a local pytest PASS count. Local read-only `git ls-remote` failed `Could not resolve host: github.com`; no local pytest, Ruff or physical-PC GGUF verification was run.

## Exact CI observation / what is NOT proven

- Run624 checkpoint `3eb9e7a2eab22ce64f9d527a51465b890402fb73` [#41970333907](https://github.com/Iam-2squared/ark-ai/actions/runs/41970333907): **FAIL 6/6**, precisely Ruff I001 on the malformed WRITE restart test import.
- Run625 import fix `d3d3e42e10823934f23fdfcb37cc21c95a783ed5` [#41976151679](https://github.com/Iam-2squared/ark-ai/actions/runs/41976151679): **IN PROGRESS** at prior observation.
- Run625 Planner source+test `75ad3795d90369e8d761710d6a481fbc927ec4d0` [#41976653663](https://github.com/Iam-2squared/ark-ai/actions/runs/41976653663): **IN PROGRESS** at prior observation.
- Run625 due-witness source+test `f53b3779750d4abc0d9b3bb8908ece3355a69f6f` [#41976920696](https://github.com/Iam-2squared/ark-ai/actions/runs/41976920696): **QUEUED** at prior observation.
- All subsequent commit/result CI statuses must be fetched from GitHub at their **exact HEAD**, including the report and canonical checkpoint commits; do not extrapolate intermediate GREEN to a newer HEAD.

## Boundaries and remaining risk

- The synthetic Planner journal and due reservation store operate locally and without ToolBackend execution. Their checks detect specified in-process reflective drift only. They cannot authenticate the clock, writer, consent, owner, provenance, whole-file/WAL custody, external outcome or cross-store atomicity. UNKNOWN WRITE/COMMIT-UNKNOWN always remain manually quarantined, without automatic retry.
- Existing `DueReservationReceipt` constructor hardening and broader durability/permission integration remain separate, test-sensitive work. No claims about those paths being closed in this run.
- Frozen V1/V2/Local UI/Launcher contracts, evaluation and evidence must remain unchanged. PR #5's V3 human approval and real Candidate/compute boundaries remain blocked. PR #9's Next Generation UI remains **PAUSED**, Draft/unmerged; no UI source, tests or features were modified. No paid API/GPU/service, secret, account connection, destructive operation, protected evaluation opening, Candidate promotion, physical-device execution or main merge.
- Current overall ARK/JARVIS and V3 status: **NOT_PASSED**.

## Next plan / 今後の方針

1. Confirm all **six** Ubuntu/Windows Python 3.11–3.13 CI jobs for the latest source/tests and final checkpoint **exact HEAD**. On failure, inspect logs and repair the smallest semantics-preserving cause; while CI runs work independent non-UI modules, do not duplicate equivalent CI.
2. Advance Memory COMMIT-UNKNOWN manual-only row/event/CAS/snapshot consistency and privacy/expiry evidence without inferring authorization.
3. Advance Planner durable restart/quarantine, immutable registry, exact PermissionGate, audit-before-*mock*-action, occurrence fences and startup readiness only after predecessor exact-HEAD CI GREEN.
4. Keep V3 static approval/path/identity/reproducibility work free-only and separate; keep paused UI, frozen evidence and PR #5/#8/#9 Draft/unmerged.

## CI failure investigation and corrective commits (observed later this run)

At exact import-fix HEAD `d3d3e42e10823934f23fdfcb37cc21c95a783ed5`, [CI #41976151679](https://github.com/Iam-2squared/ark-ai/actions/runs/41976151679) Ubuntu 3.11 ran Ruff successfully, then reported **3 FAIL, 8,719 PASS, 1 SKIP**. At Planner test HEAD `75ad3795d90369e8d761710d6a481fbc927ec4d0`, [CI #41976653663](https://github.com/Iam-2squared/ark-ai/actions/runs/41976653663) likewise reported **3 FAIL, 8,731 PASS, 1 SKIP** on Ubuntu 3.11. At due-witness test HEAD `f53b3779750d4abc0d9b3bb8908ece3355a69f6f`, [CI #41976920696](https://github.com/Iam-2squared/ark-ai/actions/runs/41976920696) reported **3 FAIL, 8,735 PASS, 1 SKIP** on Ubuntu 3.11. These three consistent failures were not caused by the new Planner/due tests:

- `tests/test_disconnected_read_plan_result_constructor_custody_run624.py` two parameterized cases: a synthetic `_digest` callback replaced `DisconnectedReadPreflight.__init__`; the last stability check did not reverify the constructor directly before invoking it, and the hostile initializer **actually executed**. This was a genuine source guard gap, not just a stale expectation. Revalidated original result constructor immediately before instantiation in `src/ark/agency/disconnected_read_preflight.py` (normal guarded source commit **`0eef7937c507f18e89c59895379250656a68ade6`**, blob `8f7a4bf788428c10dc2bbd403ccffbc6b4187029`). The same existing tests require the hostile initializer never execute. No real backend execution or new READ dispatch introduced.
- `tests/test_disconnected_write_restart_binding_run486.py` one legacy expectation still looked for `changed after review`, although Run624 correctly rejects class rebinding **before** report construction with `constructor changed`. Updated only the regression fixture to assert the forged constructor was **never called**, the exact preconstruction rejection, and unchanged reservation witness (normal guarded test commit **`5f5e4c56192a701114bb99201937fab4a90c51f2`**, blob `e2160741a347c0b2338056349a6289dffd97ade9`). The WRITE quarantine and inability to replay remain intact.

**These two fixes have NOT yet been proven six-environment GREEN.** Their exact-head workflow [#41977333716](https://github.com/Iam-2squared/ark-ai/actions/runs/41977333716) was QUEUED at initial observation. Any later result, including this documentation/checkpoint commit, must be read separately. The earlier FAILs remain historical evidence rather than being relabeled success.

# Run789 — disconnected atomic and retained Memory control-plane custody

**Work basis:** `2ee7a9695d2f8c55fbdc1a14c0f87027f9f3342b`, `research/jarvis-foundations`,
[Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8). The basis
[CI #42991433471](https://github.com/Iam-2squared/ark-ai/actions/runs/42991433471)
was checked directly and all **six** Ubuntu/Windows × Python 3.11–3.13 jobs
completed **GREEN**. That basis PASS does not cover this run's new code.

## New saved, isolated non-UI packages

1. **Atomic intent input parser and shape capture.** Source
   `src/ark/agency/disconnected_atomic_input_review.py`, commit
   `db5a60d727359f68ccf4f7738ca0c73c4da6293a`, retains the
   module's exact regex objects, claim/witness class field names,
   original descriptor captures, immutable hook-name tuple, 128-entry
   admission ceiling, and original validator functions. It rejects
   altered module-global protocol before any carrier attribute read
   and rechecks around the read/revalidation stages. No reservation,
   external call, consent verification or action permission is gained.
   `tests/test_atomic_input_protocol_preaccess_run789.py`, commit
   `cda748d3f2ebf70ca1fe37e4d41a46081a2ecb18`, submits **12**
   hostile control-plane variants and **one** original valid-path
   check. This is interpreter-local tamper detection, not authenticated
   provenance or a sandbox.

2. **Retained Memory generation fail-closed review protocol.** Source
   `src/ark/memory/retained_generation_fence.py`, commit
   `2ea7b0852f663d320f107b748dc4e59a1d0696fb`, independently
   pins the original list of False-only denial properties,
   Memory generation field list, class hook list, captured
   descriptors, retained review class and imported review callback.
   A changed baseline is rejected **before private SQLite access**.
   `tests/test_memory_retained_generation_control_plane_run789.py`,
   commit `ddf1ccdd1e33ac600a56645bdeb3bf3b5770753c`,
   submits **eight** changed-baseline cases plus **one** normal
   read-only continuity check. It does not make the retained hash an
   independently authenticated generation witness, perform a CAS
   write, resolve a commit-unknown result, or permit erase.

3. **Disconnected registered recovery quarantine.** Source
   `src/ark/agency/disconnected_atomic_recovery_quarantine.py`,
   commit `884ae3e3c9da601b5b3167b1879afb5f23070e1f`, now
   rejects replaced `ledger.inspect` and registry-bound intent
   derivation callbacks, altered snapshot fields/hooks and the
   exported deny-only result's original fields, permissions and
   constructor hooks. Both initial preflight and post-inspect
   checks remain before return. `tests/test_atomic_recovery_callback_custody_run789.py`,
   commit `38b47f3e20426f943df9842264277e0a67d7e744`,
   submits **eight** hostile callback/descriptor cases plus
   **one** valid deny-only result check. Even local occurrence
   membership cannot prove a bound request or real-world WRITE.

**Total:** 3 non-UI work packages, **31 submitted parametrized/positive
test cases** across 3 newly added regression files; 3 source modules changed.
New tests are not claimed GREEN until the matching exact-head
Actions jobs complete.

## Exact-head CI / evidence at report authoring

- Basis `2ee7a9695d2f8c55fbdc1a14c0f87027f9f3342b`:
  [#42991433471](https://github.com/Iam-2squared/ark-ai/actions/runs/42991433471),
  **COMPLETED GREEN 6/6**.
- Atomic input source `db5a60d...`: 
  [#42998053496](https://github.com/Iam-2squared/ark-ai/actions/runs/42998053496),
  **IN PROGRESS** at initial CI read.
- Atomic input test `cda748d...`:
  [#42998099085](https://github.com/Iam-2squared/ark-ai/actions/runs/42998099085),
  **IN PROGRESS** at initial read.
- Memory source `2ea7b085...`:
  [#42998152058](https://github.com/Iam-2squared/ark-ai/actions/runs/42998152058),
  **IN PROGRESS** at initial read.
- Memory test `ddf1ccdd...`:
  [#42998180994](https://github.com/Iam-2squared/ark-ai/actions/runs/42998180994),
  **QUEUED** at initial read.
- Recovery source `884ae3e...`:
  [#42998307560](https://github.com/Iam-2squared/ark-ai/actions/runs/42998307560),
  **QUEUED** at initial read.
- Recovery test `38b47f3...`:
  [#42998352687](https://github.com/Iam-2squared/ark-ai/actions/runs/42998352687),
  **QUEUED** at initial read.
- The later report/checkpoint HEAD has its own CI; do **not**
  borrow successes from an earlier SHA. No manual duplicate
  workflow runs requested; no local pytest execution was available
  in this connector-backed environment.

## Limitations and integration order

These modules continue to be opt-in, read-only or disconnected.
Python in-process function/class identity checks can detect inadvertent
or hostile local rebinding but cannot protect against an attacker with
arbitrary control of the running interpreter. No independent identity
attestation, trusted-clock approval issuer, authenticated consent,
cross-SQLite atomic transaction, durable one-time authorization,
effect receipt or physical-PC action is established.

Safe next steps: verify each actual six-job CI matrix; repair only
observed failures through normal Contents API; then strengthen Memory
CAS/ABA and commit-unknown manual recovery, Planner terminal
persistence, and registry-bound PermissionGate plus pre-action
audit review. Real ToolBackend/WRITE must stay disconnected without
independently reviewed authorization and durable audit. Continue
read-only privacy/occurrence/observation fixture work in parallel.

**Frozen and approval gates:** V1/V2/Local UI/Launcher evidence and
protected V2 evaluation unchanged. PR #5 remains Draft/unmerged;
PR #9 remains Draft/unmerged and the UI lane paused. No paid API,
GPU compute, candidate training/adapters, promotions, account
connections, credentials, real PC actions, destructive writes, or
main merge are authorized. ARK/JARVIS/V3 remains **NOT_PASSED**.

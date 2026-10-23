# ARK AI Project Status

**LATEST**

Saved at: **2026-10-23 14:59:25.379 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / **Draft, unmerged PR #8**.
Exact work-basis HEAD (before Run357): `ed13c53c815eeacaec22b9e7d8e97e410c63d932`.
Exact new source/test HEAD (before this checkpoint): `112c6f4951210a1b1159fb0c7df560e65e5739f5`.
Checkpoint-result HEAD: cannot be embedded into its own committed file; **the GitHub Contents update result commit SHA is authoritative**. CI #278 applies to `112c6f4951210a1b1159fb0c7df560e65e5739f5` only, and not automatically to the documentation-only checkpoint commit.

## Overall current ARK state

ARK JARVIS foundations remain reversible Draft research, **not** production dispatch, authenticated consent, real exactly-once actions, or JARVIS completion. Frozen V1/V2/Local UI/Launcher evidence/contracts unchanged. `main` remains `7a843f17eb96ed13d66f23b58b06406b3002e405`.
V3 PR #5 stays Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`, **NOT_PASSED**, no protected evaluation opening.

## NEW work this invocation — Run 357

- **Registry mapping epoch:** normal GitHub Contents source update `adb173e14a36a71285ddbaec594960af44c65265` pins the exact read-only ToolRegistry mapping object and rejects reflected equal-valued replacement; separate repository regression file at `fa6a6bc270ef6dd9e05cad2da853d97aa275e009` (11 parametrized tests). No backend is invoked.
- **Memory expiry CAS:** source update `b24cecf2bde72ffd6b8a62dc62564a82d7ec1a56` acquires SQLite writer lock **before** sampling time or selecting expired rows, and conditionally deletes by exact memory ID, scope, revision and expiry. Only successful deletions emit expiry audit events. Repository tests committed at `5446d3a69a6eaed8aaab59f77120a23a8377247d` (3 tests: writer-lock clock probe, scoped expiry, rollback on failed audit).
- **CI recovery:** commit `5446d3a69a6eaed8aaab59f77120a23a8377247d` produced CI **#277 FAIL** across 6 jobs due solely to Ruff I001 import ordering in the new Memory test. A minimal import-order correction at `112c6f4951210a1b1159fb0c7df560e65e5739f5` restored **CI #278 SUCCESS 6/6**.
- **Independent Planner durability (offline only):** disconnected synthetic SQLite Planner journal now transactionally updates and verifies a second local tail-anchor table. Missing/replaced anchor, inconsistent count/hash or truncated journal are refused. 9 new synthetic tests; Linux/Python 3.13.5 local warnings-as-errors: Memory **390**, Agency/Observation **659**, Personal Context **193** = **1,242/1,242 PASS**. Clean Run356 patch replay matches **162/162 file SHA-256**; syntax parsed as Python 3.11/3.12/3.13 grammars (not actual alternate runtime tests).
  Detached source ZIP SHA-256 `039a1fb9e34147f9220045ac098e25454531878d2380ffd37bf426b376c97652`; detached evidence ZIP SHA-256 `c8f30521db7d6fbd4ed0ddccd84bb51774fa26499ff983b1b0d873f54726a2f0`. **Not committed or covered by GitHub CI.**
- Produced read-only exact-source follow-up audit prioritizing Memory put/delete lock-before-clock, persisted-row integrity and same-version schema checks. No frozen-contract changes or operational data reads.

## Tests / CI / evidence

- PR #8 CI #274 / run `39907742262`: **SUCCESS**, registry source HEAD `adb173e14a36a71285ddbaec594960af44c65265`.
- CI #275 / run `39907979841`: **SUCCESS**, registry regression HEAD `fa6a6bc270ef6dd9e05cad2da853d97aa275e009`.
- CI #276 / run `39908163598`: **SUCCESS**, Memory source HEAD `b24cecf2bde72ffd6b8a62dc62564a82d7ec1a56`.
- CI #277 / run `39908372539`: **FAIL 6/6**, Ruff I001 new test import only, test body not reached.
- CI #278 / run `39908587091`: **SUCCESS 6/6 GREEN**, exact source-and-test HEAD `112c6f4951210a1b1159fb0c7df560e65e5739f5`; Ubuntu/Windows × CPython 3.11/3.12/3.13; job IDs `120266096541`, `120266096437`, `120266096428`, `120266096146`, `120266096559`, `120266096293` respectively.
- The detached Planner fixture is not part of PR #8. Its synthetic local hashes are **not** independent security attestation.
- No run of new CI on this documentation checkpoint commit is asserted here.

## Frozen boundaries, blockers and authorizations

No paid/external compute, paid services, training, real Candidate adapter/weight generation, protected V2 final evaluation, promotion, frozen-contract edits, credentials, physical-PC action, real backend execution, personal-data ingestion, notification delivery, destructive migration, or main merge. No bypass or raw Git Object writes. PR #5 remains separately gated. SQLite local tail anchor is mutable with its database; it is not a trusted external history root. Memory v1 still needs schema/content-row integrity and more lock-before-clock work; trusted clock, issuer authenticity and real restart-safe exactly-once remain open.

## Next plan / 今後の方針

1. Verify the documentation-only checkpoint result HEAD/CI separately; maintain exact-head GREEN evidence without duplicate reruns.
2. Continue **Memory v1**: move put/delete clock behind writer locks, validate persisted IDs, content digests, types/canonical metadata and same-version schema integrity. Add conflict, corruption, cross-process SQLite tests.
3. After official lower-level GREEN, integrate registry-authoritative PermissionGate, durable one-shot, trusted-clock pre-action audit and mock no-replay recovery. **No live tool dispatch**.
4. Advance Planner state persistence and UNKNOWN WRITE reconciliation; keep offline anchor fixture isolated pending API/schema compatibility and independent history-witness design.
5. Progress privacy-safe Personal Context, Scheduler/Observation and V3 free-only provenance/path/reproducibility guards without training, live inputs, Candidate, protected evaluation or main merge.

---

**HISTORICAL — earlier status preserved below; superseded by Run357**


Saved at: **2026-10-16 17:59:25 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / **Draft, unmerged PR #8**.

Work-basis HEAD: `2baeb7824df9460235e876336fac942ae64dbbee` (source).
Checkpoint-result HEAD: this file cannot embed the SHA of its own future commit; use the GitHub Contents update result SHA. CI #271 applies to work-basis HEAD **only**, not automatically to the subsequent documentation checkpoint commit.

## Overall current ARK state

V1/V2/Local UI/Launcher contracts and evidence remain frozen and unchanged.
`main` remains `7a843f17eb96ed13d66f23b58b06406b3002e405`.
V3 PR #5 remains Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`, NOT PASSED.
JARVIS PR #8 remains reversible Draft/unmerged, not a production dispatch gate or JARVIS completion.

## NEW work this invocation — Run 204

- Saved a narrowly scoped **source** hardening in `src/ark/agency/registry.py`: reject equal-valued reflected `str` subclasses for registry revision and registered name/capability/backend identity. Normal GitHub Contents write succeeded at source HEAD `2baeb7824df9460235e876336fac942ae64dbbee`, based on `3804b77de13570bf8cc6b59aa67a3f0f6c4bec84`.
- Exact source HEAD CI **#271**, run `38876767855`: **SUCCESS 6/6 GREEN** on Ubuntu/Windows × Python 3.11/3.12/3.13; jobs `116893574699`, `116893574968`, `116893575063`, `116893575068`, `116893575095`, `116893575174`. These jobs validate committed source and existing tests, **not** the blocked new test file.
- Attempted the normal Contents `create_file` path for `tests/test_registry_epoch_exact_types_run204.py`, but the safety path **BLOCKED** it. No focused GitHub test commit/CI is claimed and no bypass was attempted.
- Continued independent, reversible **offline-only** code: an exact-carrier ToolRegistry regression suite; duplicate synthetic pre-action audit receipt detection across distinct WRITE occurrences; and purpose-bound synthetic observation/privacy review. **29 new tests**, detached Linux/Python 3.13.5 **1,601/1,601 PASS with warnings-as-errors**. Clean Run203 patch replay has 166/166 Python SHA-256 matches and **29/29 focused PASS**; a full clean replay was interrupted, so it is not claimed GREEN. Offline ZIP SHA-256: `634064ace63338365a2f7804b18de8a94bdb370f70aa756ef2de3f83f02eb7c5`.
- Detached source and PR #8 source are **not byte-identical**; never replace PR source wholesale with the offline ZIP.

## Frozen boundaries and blockers

No paid/external compute, new credentials, training, Candidate generation, protected V2 evaluation opening, promotion, real tool/backend execution, destructive migrations, frozen contract changes, or main merge. PR #5 stays under its separate authorization gate. No live observation/consent proof is asserted.
The new ToolRegistry regression file remains GitHub-write blocked; only the source change has exact-head CI. Synthetic hash/digest results are not external attestation. Multi-database atomicity, trusted time, issuer provenance, restart-safe authorizing one-shot and unknown WRITE recovery remain unproven.

## Next plan / 今後の方針

1. Save the focused Registry exact-epoch test file via the **normal** GitHub path when permitted; establish fresh exact-head CI GREEN before downstream PermissionGate authority wiring.
2. In separate safe lanes, advance Registry-bound exact-type PermissionGate, durable one-shot/occurrence integrity, trusted-clock pre-action audit and disconnected no-replay recovery; preserve no real dispatch.
3. Independently advance Memory CAS/event/expiry and coherent snapshots; address existing GitHub Memory v1 schema/row integrity and lock-before-clock gaps before integration.
4. Continue Planner ambiguous WRITE recovery, privacy-scoped synthetic Observation/Personal Context and Scheduler fixtures; require actual provenance/consent design before live capture.
5. Keep V3 free-only JSON/identity/provenance guards reversible, with no paid/training/validation/final opening or promotion.

---

**HISTORICAL — superseded by Run 204**

Saved at: **2026-10-13, 00:37:52 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / Draft, unmerged PR #8

Work-basis HEAD: `1ebeafe6d7ba8ffd58a32cd0d83d0567a66d256c`.

Checkpoint-result HEAD: this self-updating file cannot contain the SHA of the commit that
writes it. The GitHub Contents update result for this checkpoint commit is authoritative;
CI #267 below applies to the **work-basis source HEAD**, not automatically to this
subsequent documentation-only checkpoint commit.

## Overall current ARK state

V1/V2/Local UI/Launcher contracts and evidence remain frozen and unchanged.
`main` is `7a843f17eb96ed13d66f23b58b06406b3002e405`.
PR #5 V3 remains Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`;
no protected evaluation was opened or later PASS declared. PR #8 remains Draft,
reversible, and unmerged, not a JARVIS completion or official roadmap PASS.

## NEW work this invocation

- Restored PR #8 source CI after public registry exports commit
  `3ea77091a9725341f3e3e79d77ff0257f577b26b` caused Ruff I001.
  The **only source change** was a reorder of the `.policy` and `.registry`
  imports in `src/ark/agency/__init__.py`. Normally permitted GitHub Contents
  update succeeded at `1ebeafe6d7ba8ffd58a32cd0d83d0567a66d256c`.
- The exact source HEAD above passed CI #267 / run `38270375604`:
  **SUCCESS 6/6 GREEN**, Windows and Ubuntu, Python 3.11/3.12/3.13.
  Previous #266 / run `38244247324` was FAIL 6/6 for I001 on an older HEAD.
- Prepared reference-vector/non-dispatch ToolRegistry repository tests for the
  already-committed fixture files. A normal GitHub Contents `create_file` write
  for `tests/test_tool_registry_committed_vectors.py` was blocked by safety
  checks, so no such test was saved and **its CI evidence does not exist**.
- Advanced two **detached, reversible, offline-only** modules in Run 121:
  paged Memory event-chain continuity (21 new tests) and per-source Observation
  liveness (23 new tests). Neither source/test module is in PR #8.
  Run121 detached Linux/Python 3.13.5 Agency **2555/2555 PASS**,
  independent V3 guards **186/186 PASS**, total **2741/2741 PASS**;
  source ZIP SHA-256 `f49aff22ec9fc0c5204719b305b658a81b3316f9108f6c941c2be432275f601d`.
  All 311 prior Run120 source bytes are unchanged; 4 new files; 315 source
  hashes match the ZIP manifest. Clean patch replay new tests **44/44 PASS**.
  No Windows/actual Python 3.11/3.12/Ruff run was performed for the detached candidate.

## Tests / CI / evidence

CI #267 / `38270375604`, source HEAD `1ebeafe6d7ba8ffd58a32cd0d83d0567a66d256c`:

- Ubuntu 3.11 job `114882867967`: SUCCESS
- Ubuntu 3.12 job `114882868485`: SUCCESS
- Ubuntu 3.13 job `114882868378`: SUCCESS
- Windows 3.11 job `114882868301`: SUCCESS
- Windows 3.12 job `114882868373`: SUCCESS
- Windows 3.13 job `114882868279`: SUCCESS

Run121 offline test evidence is **not** exact-head GitHub CI evidence.
The Run121 ZIP is not safe to overwrite onto PR #8: its lower-level module
dependencies and implementation differ from the GitHub branch.

## Frozen boundaries unchanged

No paid/external GPU compute, paid APIs/services, model training, real Candidate
adapter/weight generation, protected V2 final-evaluation opening, promotion,
frozen-contract change, credentials/account connection, physical-PC device
capture, actual tool dispatch, destructive action, or main merge.

## Blockers / authorization boundaries

Normal GitHub source/test write safety layer rejected the focused ToolRegistry
repository-test addition. No bypass, raw Git object, alternate ref-write, force
push, or duplicate CI workflow was used. Keep all detached Memory/Observation/
Planner/Scheduler/Personal Context work isolated until prerequisites are
reviewed and integrated with exact-head GREEN evidence.

PR #5 remains subject to frozen Contract and explicit approval for any real
training, provider/billing, Candidate generation, protected evaluation or promotion.
Preserve populated historical audit/Memory migration boundaries until reviewed.

## Next plan / 今後の方針

1. Add focused ToolRegistry committed-fixture identity/immutability/non-dispatch
   tests through the normal path when permitted; require exact-head CI GREEN.
2. Then integrate Registry-bound PermissionGate, durable one-shot authorization,
   execution occurrence/replay protection and trusted-clock audit-before-action
   only after their prerequisite invariants are GREEN.
3. Advance independently tested Memory CAS/event/expiry and coherent snapshots;
   integrate detached chain review only once its underlying interfaces match.
4. Continue Planner ambiguous-RUNNING recovery without automatic WRITE replay.
5. Stage fixture-only Observation session/liveness adapters and privacy-safe
   Personal Context/Scheduler without live capture, action authority or user
   consent assumptions. Keep free-only V3 guards isolated.

---

## Historical checkpoint — 2026-10-07 (preserved)

**HISTORICAL — superseded by LATEST above**

Saved at: **2026-10-07 18:50:20 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / Draft PR #8

Work-basis HEAD: `eb49558c0e6a80df53e246aa1fb0a71b93ec3932`

Checkpoint-result HEAD: this file cannot contain the SHA of the commit that writes itself; use the
resulting commit SHA from this checkpoint update as the authoritative checkpoint-result HEAD.

## Current state

V1/V2/Local UI/Launcher evidence is frozen and unchanged. PR #5 remains Draft/unmerged at
`d6d4c1954a85fc716b1c593ac55c85417912418f` under its controlling V3 Contract. JARVIS
foundation work remains isolated/reversible and is not a roadmap PASS.

PR #8 is open, Draft, mergeable, **114 commits ahead / 0 behind** `main` at this work basis.

## New work this session

- Landed immutable ToolRegistry source at
  `eb49558c0e6a80df53e246aa1fb0a71b93ec3932` through the normal GitHub Contents path.
- The registry snapshots exact `ToolRegistration` values, rejects duplicate names, sorts by
  tool name, exposes a read-only mapping, computes a registration-order-independent revision,
  resolves exact capabilities, and derives registry-bound action IDs from request + registry
  revision + capability/effect/backend identity.
- CI #260 / run `37603020130` for that exact source HEAD completed **SUCCESS, 6/6 GREEN**,
  including Ruff and pytest on Windows/Linux Python 3.11-3.13.
- Offline focused validation reproduced the frozen registry revision and all three bound-action
  reference vectors, exercised 256 randomized registration orders, and verified lookup/bind
  caused zero backend executions: **260 focused checks PASS**. This focused result is local
  evidence only until matching repository tests are saved.
- Read-only Memory review reconfirmed the highest-risk v1 gaps remain exact request/scope ingress,
  persisted row/event storage-class and digest validation, lock-before-clock mutation ordering,
  revision-bound expiry purge, and coherent read snapshots.
- PR #5 free-only audit reconfirmed **8 production modules / 9 `json.loads` parse sites**.
  A shared strict decoder package was prepared for duplicate decoded keys, NaN/Infinity,
  float-overflow-to-infinity, invalid UTF-8, and exact str/bytes ingress, but the normal source
  write was safety-blocked and therefore did not land.
- Production Observation fixture adapters and focused ToolRegistry repository tests/public exports
  were also prepared, but their normal source/test writes were safety-blocked and did not land.

## Tests / CI / evidence

CI #260 GREEN jobs:
- Ubuntu 3.11 `112731721391`
- Ubuntu 3.12 `112731721723`
- Windows 3.11 `112731721736`
- Windows 3.12 `112731721767`
- Ubuntu 3.13 `112731721779`
- Windows 3.13 `112731721793`

The prior PR #8 checkpoint HEAD
`ae967e5cb8a5df40162c3a9223cc25582bae7fb2` remains CI #259 /
run `37578146322` **SUCCESS, 6/6 GREEN**.

PR #5 remains at `d6d4c1954a85fc716b1c593ac55c85417912418f` with
CI #151 / run `36223644908` **SUCCESS**.

Focused local/source-ready evidence is not repository test evidence until matching tests are
saved and their exact-head CI is GREEN.

## Frozen boundaries unchanged

No paid/external compute, real training, Candidate adapter/weight generation, protected V2
opening, Candidate promotion, frozen-contract change, new credentials/account connection,
live capture, destructive action, unavailable physical-PC action, or main merge occurred.

## Blockers / authorization boundaries

After the ToolRegistry source write succeeded, later normal GitHub Contents writes for production
Observation adapters, focused ToolRegistry tests, agency public exports, the PR #5 strict JSON
guard, and a Gap Matrix reconciliation were rejected by the safety layer. No raw Git objects,
ref manipulation, force push, hidden route, or other safeguard bypass was used.

The ToolRegistry source is landed and exact-head CI GREEN, but its frozen-vector/randomized-order
focused repository regressions and public package exports remain pending; do not integrate durable
authorization on top of it until those tests/exports are saved and exact-head GREEN.

PR #5 still requires explicit authorization before any external compute, real Candidate
generation, protected V2 opening, or promotion.

Populated Action Audit v1 -> occurrence-bound v2 migration and populated Memory v1 ->
independently anchored event-log v2 migration remain blocked until reviewed historical mapping
policies exist.

## Next plan / 今後の方針

1. Retry only the normal permitted path later for focused ToolRegistry fixture/reference-vector
   tests and public exports; require exact-head GREEN before dependent integration.
2. Then harden exact PermissionGate ingress + non-consuming grant validation and, only after GREEN,
   land durable registry-bound one-shot authorization -> execution occurrence/replay protection ->
   trusted-clock audit-before-action disconnected executor.
3. Continue independent Memory v1 hardening: exact ingress, schema/row/event integrity,
   lock-before-clock CAS/expiry, then coherent multi-namespace snapshot -> Personal Context.
4. Continue Planner Recovery against the already-landed exact planner state machine; preserve
   rollback safety and RUNNING ambiguity without automatic write replay.
5. Land fixture-only Observation adapters when the normal source path permits; keep live capture
   disconnected.
6. Continue PR #5 free-only guard closure only; do not start preflight/training, external GPU,
   Candidate generation, protected evaluation, or promotion.

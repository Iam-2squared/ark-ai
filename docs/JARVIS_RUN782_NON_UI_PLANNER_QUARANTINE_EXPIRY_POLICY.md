# Run782 — FREE-ONLY / NON-UI Planner CI repair, quarantine/expiry/policy admission

Source-grounded evidence recorded on **2026-11-11 JST**. All SHA values are
regular GitHub commit IDs, not model hashes, external attestations, timestamps
from ARK trusted clocks or human approval. ARK/JARVIS/V3 remains **NOT_PASSED**.

## Scope and exact writes

- Repository: `Iam-2squared/ark-ai`; branch `research/jarvis-foundations`;
  [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), OPEN/DRAFT/UNMERGED.
- Initial HEAD: `68d3154c7f01a7d7a9bdc5735dc393be77f07710`
  (Run781 checkpoint). GitHub Actions [#42942589306](https://github.com/Iam-2squared/ark-ai/actions/runs/42942589306)
  failed 6/6 on that exact HEAD: the only observed test failure is
  `tests/test_epoch_bound_planner_input_epoch_run781.py` parameter
  `recovered_tail_value`. Both Ubuntu 3.12 job `130267698214` and
  Windows 3.12 job `130267698582` log a fail-closed
  `Planner changed across atomic review` exception rather than the test's
  narrower expected `Planner recovery input epoch changed`.
  No registered WRITE dispatch occurred; no production relaxation was needed.
- **A — Planner CI repair:** `020e654e8c71729c81388467096ed8f54aa0415b`
  changes only that test's expected diagnostic by mutation variant. The
  recovered-tail count mutation is rejected earlier by the Planner cross-store
  comparison; retained-tail and status-carrier mutations retain their exact
  epoch rejection expectations.
- **B — Proactive quarantine equality custody:**
  `c084b09162c15015d9855fc7e9bbc86f862580eb` changes
  `src/ark/disconnected_schedule_quarantine_ledger.py` to compare exact
  persisted witness `count` and `chain_sha256` instead of calling mutable
  dataclass `__eq__` in read, writer admission and post-insert integrity
  checking. `0005c13637351e96dd23a8cb2ed9a4d3acaa8c90` adds three
  tests: forged equal witness rejection in read/write; legitimate cold
  read/write when `__eq__` throws if called. No notification or dispatch.
- **C — Memory expiry private digest protocol:**
  `cb5180a205c063f9f403fc52da4ed1f11da7124c` pins original
  `hashlib`, `json`, SHA-256, JSON dumps and domain before private
  read-only expiry review; `5e2953a1e90ea11e59a8e68b87970626ae841a91`
  adds 11 tests (five substitutions × preview/reverify plus restored-path
  regression). No purge/physical erasure and no trusted time.
- **D — PermissionGate grant budget:**
  `af08eeb46600f4f5a6d9d4aaf37b8420fe466eb4` pins exact
  `_MAX_GRANTS=1024` before grant iteration, registry-backed inspection or
  token admission and rechecks it during materialization. Commit
  `8cacad0524473e25afb204f4582bd8258b0fb2b5` adds 10 tests:
  four invalid budget substitutions × registered/unregistered WRITE, plus
  mid-iteration drift in both paths. No actual backend or durable token.
- **Total added:** 24 parametrized regression cases across three new test
  files; one prior Planner test corrected. Production changes in three
  independent non-UI modules. All GitHub writes used the ordinary Contents
  path after re-reading live HEAD; no raw Git object or force-push bypass.

## CI evidence and outstanding exact-head gate

The initial Run781 checkpoint [CI #42942589306](https://github.com/Iam-2squared/ark-ai/actions/runs/42942589306)
is **6/6 FAIL**. At the last workflow inventory during this run, new
automatically triggered workflows were **not** six-job GREEN: Planner fix
[#42947626107](https://github.com/Iam-2squared/ark-ai/actions/runs/42947626107)
IN PROGRESS; quarantine source
[#42947835724](https://github.com/Iam-2squared/ark-ai/actions/runs/42947835724)
IN PROGRESS and quarantine test
[#42947900233](https://github.com/Iam-2squared/ark-ai/actions/runs/42947900233)
IN PROGRESS; Memory source
[#42948045778](https://github.com/Iam-2squared/ark-ai/actions/runs/42948045778)
QUEUED and Memory tests
[#42948119843](https://github.com/Iam-2squared/ark-ai/actions/runs/42948119843)
QUEUED; PermissionGate source
[#42948308520](https://github.com/Iam-2squared/ark-ai/actions/runs/42948308520)
QUEUED and tests
[#42948390321](https://github.com/Iam-2squared/ark-ai/actions/runs/42948390321)
QUEUED. These workflow states may evolve after recording; no unobserved
GREEN is claimed. Any report/status commits produce later distinct HEADs.

No local full-suite, external hardware GGUF test, authenticated source
identity, model weight hash, independent retention audit or paid service
execution is asserted.

## Invariants, boundaries and next plan

- A `QuarantineWitness` matching a local chain is still not consent, clock
  authority or proof of timely execution. Exact scalar comparisons avoid
  executing a substituted equality hook; they do not authenticate SQLite
  database origin or make two databases atomic.
- Expiry preview computes content-free synthetic hashes only. Pinning codec
  identity at entry does not prove cryptographic provenance or authorized
  erasure, and does not eliminate every reentrant callback/TOCTOU concern.
- PermissionGate's `_consumed_tokens` is process-local: a granted one-shot
  in tests is NOT restart-safe authorization or independent human consent.
  No real backend path is connected.
- Keep PR #5 (protected V3 evaluation) and PR #9 (paused UI) DRAFT and
  UNMERGED. Frozen V1/V2/Local UI/Launcher contracts/evidence, `main`,
  protected evaluation and Candidate promotion remain untouched.
- **Priority 1:** inspect actual CI jobs for each code/test SHA; if failures,
  make the minimal semantics-preserving correction, maintaining the UI pause.
- **Priority 2:** Memory COMMIT-UNKNOWN/CAS/ABA/expiry retained-custody;
  Planner terminal recovery, durable UNKNOWN/manual triage.
- **Priority 3:** immutable registry + exact-type PermissionGate + audit-before-
  action and disconnected mock Executor integration only after exact-head
  lower-level GREEN; no live effect.
- **Priority 4:** Personal Context privacy/veto, proactive occurrence replay,
  offline observation contracts and free-only V3 guards.

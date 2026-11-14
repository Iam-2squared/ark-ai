# Run783 — FREE-ONLY / NON-UI CI triage, registry identity, schedule resume

Documented 2026-11-11 JST. This is synthetic, local-first, disconnected
backend engineering evidence, **not** an ARK/JARVIS/V3 PASS decision.
No physical PC, model weights, real tools, paid compute, camera/microphone,
notifications, protected evaluation, or user-authenticated authorization.

## Basis and exact source/test writes

- Repository: `Iam-2squared/ark-ai`; development branch
  `research/jarvis-foundations`; [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8)
  remains OPEN/DRAFT/UNMERGED. Work-basis HEAD from Run782:
  `7696fe8ca710486a7c62e51f1fa12ba90e0845d8`.
- **A — verified CI repair:** [previous exact HEAD CI #42948862888](https://github.com/Iam-2squared/ark-ai/actions/runs/42948862888)
  completed 6/6 FAIL. Both Ubuntu 3.13 job `130288148738` and Windows
  3.12 job `130288149035` show one old test
  `test_digest_time_constructor_replacement_is_refused`: expected an
  `authority` denial, received earlier fail-closed
  `expiry digest protocol changed`. The original callback remained unused.
  Ordinary Contents test-only correction
  `9ed4dc673a686adfb86129fb9c7dabe681f3122d`
  accepts either **specific** denial and still asserts the substituted
  constructor was not invoked. Production Memory expiry code unchanged.
  [Repair CI #42954207747](https://github.com/Iam-2squared/ark-ai/actions/runs/42954207747)
  later found Ubuntu 3.13 failure in a **different**, previously existing
  multiprocess WAL startup test; the Memory expiry test itself passed.
- **B — inert registered atomic identity:** source
  `src/ark/agency/disconnected_atomic_registry_bridge.py` updated at
  `084efe465ebc807a94405598b3fc06fd396dc1f4`.
  Import-time SHA-256 identity and compiled exact occurrence/bound/request
  grammars are checked before registry binding and across callback/digest
  boundaries. The `act_` request regex now uses the retained compiled
  pattern, not mutable `re.fullmatch`. New
  `tests/test_atomic_bridge_dependency_epoch_run783.py` at
  `a24bb6547d1f5123e3d0c46dea5d55e8167683a0`
  adds six parametrized/standalone cases: four preinstalled substitutions,
  one in-bind SHA change, and a deterministic no-dispatch baseline.
  [New-test CI #42954554778](https://github.com/Iam-2squared/ark-ai/actions/runs/42954554778)
  showed one test expectation failure on Ubuntu 3.11 and 3.13: the
  original bridge `except (TypeError, ValueError)` can normalize its
  own `AtomicPreactionRejected` to `registered intent binding refused`.
  Test-only fix `8832e68df8d3c862eab9a619f136c9f4163b1a8e`
  accepts both explicit fail-closed diagnostics and **still requires that
  the substituted digest was never executed and no backend dispatched**.
  No untrusted callback, real WRITE or approval was enabled.
- **C — disconnected proactive resume codec custody:** source
  `src/ark/offline_schedule_resume_review.py` updated at
  `8d457196ef46cf12050921d28115094465ed0acc`.
  The independent local scheduler review pins its SHA/JSON serializer,
  digest/grammar pattern and domain before reading the synthetic quarantine
  ledger, and rechecks across preview and report hashing boundaries.
  `tests/test_schedule_resume_codec_epoch_run783.py` at
  `b2337af2253b5ca234da7221e6e6f260219690bf`
  adds six cases (four preinstalled mutations, one late preview mutation,
  one read-only denied baseline). No timer, notification, trusted clock,
  autonomous trigger or backend execution is added.
- **D — independent-process Memory CAS test race fix:** Ubuntu 3.13 in
  [CI #42954207747](https://github.com/Iam-2squared/ark-ai/actions/runs/42954207747)
  job `130305333420` failed
  `tests/test_memory_generation_multiprocess_recovery_run757.py`
  `identical_content=True`, after a child refused concurrent
  first-open/checkpoint sidecar churn with
  `MemorySchemaError('memory SQLite sidecar path is not a single regular file')`.
  Test-only fix `1bc8645c516de5a703a2f8692d30faa082f35f8a`
  starts the two children **one at a time to receive initialization
  readiness**, then releases **both CAS operations together** using
  the preexisting shared event. This isolates first-open WAL cleanup from
  the actual competing CAS test without weakening production SQLite path
  checks or counting refused initialization as successful CAS.
  [Fix CI #42955128650](https://github.com/Iam-2squared/ark-ai/actions/runs/42955128650)
  was QUEUED at last check.
- **Total new test cases: 12** (Atomic 6 + scheduler 6), plus two
  evidence-driven legacy test corrections. These are added cases,
  **not yet confirmed all-platform PASS**. The original development
  state and future report/status commits also trigger GitHub Actions;
  do not infer exact latest-HEAD GREEN from any older run.

## Read-only independent audit and limitations

- `src/ark/agency/disconnected_registered_planner_atomic_triage.py`
  remains read-only and local-only. It correlates a Planner projection
  with independent SQLite atomic intent observations. No shared transaction
  spans both SQLite files; even two locally matching snapshots cannot
  authenticate an actor, authorize replay, or establish external effect.
- The SHA/JSON identity guards above defend specific **in-process test-time
  dependency substitution**. They are neither tamper-proof Python sandboxing,
  authenticated provenance nor immutable external custody.
- Frozen V1/V2/Local UI/Launcher evidence and controlling contracts unchanged.
  PR #5 V3 remains Draft/unmerged under its protected gate. PR #9 Next
  Generation UI is Draft/unmerged and untouched. `main` unchanged.
  **ALL NEW UI/FRONTEND WORK PAUSED.**
- No payment, potentially billable service, GPU compute, new secret/account
  connection, real Candidate generation/promotion, protected V2 final
  evaluation, real tool dispatch, physical hardware action, destruction,
  force push or approval-gated merge.

## Next plan / 今後の方針

1. Verify the **exact code/test HEAD** Linux+Windows / Python 3.11–3.13 CI
   for the test corrections and new code paths; repair observed failures only.
2. Extend Memory COMMIT-UNKNOWN/cold restart witness review without
   authorizing retry or erasure, and Planner durable terminal/epoch recovery.
3. After lower-level exact-head GREEN, build a **disconnected** adapter joining
   immutable ToolRegistry, exact PermissionGate, independent audit-before-action,
   and mock Executor with explicit no-dispatch default and replay denial.
4. Keep Personal Context revocation and proactive observation/restart
   contracts privacy-first, plus FREE-ONLY V3 path/approval/reproducibility
   gate review. Do not promote, merge or claim a PASS without its gate.

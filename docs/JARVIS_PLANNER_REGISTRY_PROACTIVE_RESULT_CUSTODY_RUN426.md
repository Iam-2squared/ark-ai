# ARK AI — Run426 inert Planner / registry / proactive custody

**Scope:** isolated, reversible `research/jarvis-foundations` Draft PR #8.
This is disconnected synthetic/local evidence, **not** real-world action
authority, authenticated human consent, externally attested time, verified
backend outcome, atomic cross-SQLite commit, or durable exactly-once dispatch.

**Exact invocation work-basis HEAD:** `cf22a2823b9de380d273274ff42cd7682737e14b`
(Run425 ActionAudit constructor regression; #1162 / 40198320060 subsequently
completed with all six GitHub Actions jobs SUCCESS). The Run425 technical
matrix is `docs/JARVIS_PROCESS_CAS_PRIVACY_READ_BRIDGE_AUDIT_RUN425.md`;
Run425 was not yet made the canonical `PROJECT_STATUS` checkpoint when this
invocation started. The prior canonical checkpoint was Run424 at
`63ee79c04461b3c8412043bf3eb1eb764f74675e`.

## Three independent implementation/test packages (+37 pytest cases)

1. **Planner Journal post-constructor and post-COMMIT result custody**
   (`src/ark/agency/planner_journal_review.py`, source
   `2924289de4b7c20853f79d141101e5d3db4b196f`, narrow compatibility
   fix `845d3bfa08b88a16dbc7b968addac29a3768ded7`;
   `tests/test_planner_journal_result_commit_custody_run426.py` at
   `57ff6a90ba6fdc44e4011c151a69de6ee5808e3a`, 20 cases). Before
   calling the synthetic snapshot constructor, capture replayed status and
   ambiguous RUNNING identities plus the original in-memory tail carriers.
   Reject a forged success, missing RUNNING status, wrong constructor type,
   mutated tail, duplicate status or equal-valued new tail. Verify the result
   both before and *after* local SQLite COMMIT. A post-COMMIT error does not
   erase a committed RUNNING journal record or grant automatic replay.
   A pre-COMMIT constructor failure rolls back the event/header atomically.

2. **ToolRegistry exact original ToolCall carriers**
   (`src/ark/agency/registry.py` at
   `bdeaa6dac258d4460bb44424b1fa8d554d2652e5`;
   `tests/test_registry_original_toolcall_carriers_run426.py` at
   `9f482faef4b276b0edd76874dc66bc475c833085`, 13 cases). Capture the
   original tool/capability/scope/argument *objects* before a reentrant
   ToolCall clone, registry lookup, resolve callback, or binding hash.
   Reject value-equal string carrier substitutions despite unchanged computed
   request ID. Unmodified bindings retain deterministic revision/ID. A
   registry diagnosis is not durable authorization or backend attestation.

3. **Bounded Proactive Witness row hashing**
   (`src/ark/proactive_synthetic_continuity_review.py` at
   `4236914b26f94fb9099ac0c2518ec0f2060d0373`;
   `tests/test_proactive_witness_row_budget_run426.py` at
   `6d35493c00e7749935c164721e9c9cb573d8041b`, 4 cases).
   Independently bound the read-only history row hashing loop to at most
   10,000 rows, even after a prior SQLite schema/row check. Negative tests
   lower the fixture-only limit and prove the overflow row is never hashed
   or accepted as a truncated witness; persisted triggers remain unchanged.
   No actual notifications or sensors are enabled.

**New test cases = 20 + 13 + 4 = 37.** All fixture objects, databases, scopes,
backends and process states are synthetic. No frozen Memory v1, ActionAudit v1,
V1/V2/Local UI/Launcher, or V3 Contract 1 schema/policy is edited.

## Exact-head CI and failure history

- Opening #1162 / 40198320060: all six GREEN on `cf22a282...`.
- **Historical failures #1163 / 40199112834 and #1164 / 40199219504,
  #1165–#1168:** a preexisting nested-topology mutation test expected
  `SyntheticPlanJournalRejected("...topology changed...")`; the new
  snapshot digest callback instead surfaced its underlying
  `PlanConflictError`. CI failures remain historically FAILED.
- The narrow semantics-preserving correction at `845d3bfa...` catches that
  graph-epoch exception and restores the canonical fail-closed journal
  diagnostic. **#1169 / 40199645724 was IN PROGRESS at documentation
  preparation**. Its Ubuntu and Windows six-job result must be read from
  GitHub Actions independently; do not extrapolate a GREEN final HEAD.
- Documentation and the later `PROJECT_STATUS` checkpoint trigger separate
  automatic CI workflows; neither an earlier source GREEN nor a completed
  document upload proves a later checkpoint HEAD GREEN.

## Still blocked / Next plan

Keep **UNKNOWN/RUNNING and already-reserved PENDING WRITE non-replayable** without
independently verified external outcome. No human credential/consent issuer,
signed trusted clock, live sensing/notification, external ToolBackend
attestation, cross-database atomic snapshot, real Candidate, paid/GPU compute,
V2 final evaluation, Candidate promotion, main merge or frozen-contract
change. PR #5 stays Draft/unmerged/NOT_PASSED.

Next: verify final exact-head matrix; inspect any FAIL without bypassing normal
GitHub Contents write safeguards. Extend four-store orphan/prefix recovery,
Memory cross-process CAS/expiry, privacy-safe revocation and reversible trusted
clock/issuer interfaces. Do not spend money or dispatch tools.

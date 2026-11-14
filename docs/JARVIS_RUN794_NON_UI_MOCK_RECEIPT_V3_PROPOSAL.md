# Run794 — Disconnected READ receipt integrity, V3 free preflight, proposal identity

**Scope:** Three independent, non-UI, reversible, local/mock-only work packages.
All source and test changes remain confined to Draft PR #8
(`research/jarvis-foundations`). No live tool, training, protected V2
evaluation, GPU/provider, paid service, Candidate promotion, credentials,
UI/frontend, or main merge is authorized or used. ARK/JARVIS/V3 **NOT_PASSED**.

## Basis and frozen scope

- Initial live branch/PR #8 HEAD: `bfcd7762171ac1416b69ea9f1df7ab0e129c4aab`.
- Its exact-head [CI #43035092767](https://github.com/Iam-2squared/ark-ai/actions/runs/43035092767)
  was individually inspected: **6/6 success**, Ubuntu/Windows Python 3.11–3.13.
  This is a prior baseline, **not** evidence for the packages below.
- PR #5 remains Draft/unmerged under training/evaluation gates. PR #9 stays
  Draft/unmerged and untouched; new UI/frontend development remains paused.
  Frozen V1/V2/Local UI/Launcher/V3 controlling contracts are unchanged.

## Package A: mock READ receipt cross-binding (9 submitted tests)

- `src/ark/agency/disconnected_read_tool_bridge.py` source
  `c50f39d55699e5f6b4404c2cfed62013c062a03e`,
  canonical NUL digest fix `8b6a4d63f372ca9a19fb4a8d111e4b621e5188ce`.
- `tests/test_disconnected_mock_receipt_binding_run794.py`,
  `a3016cf5eb658fae008a32458bef272e4552e2e3`: 1 valid and 8
  deliberately faulty *mock executor implementation* cases.
- New check recomputes the mock input SHA-256 and result SHA-256 from the
  actual deterministic fixture bytes, rejects altered request/operation/result
  fields, pins the result field epoch, and checks it again after serialization,
  digesting, output construction and deny-only getters.
- Test instrumentation explicitly replaces the *expected synthetic executor*
  and its guard baseline to emulate a faulty implementation. It is not an
  external action, a GitHub write safeguard bypass, or a proof of adversarial
  Python execution isolation. A matching local hash is never approval,
  provenance or verified physical-world outcome.

## Package B: free-only detached V3 numeric/identity cross-binding
(26 submitted tests)

- `src/ark/v3_detached_preflight_crossbind.py` created
  `503b09d6ff344ca4876a027b594852ae2be42907`,
  canonical digest grammar/domain fix
  `fbd324447200d17886f26e2a268d8ed94f39a08d`.
- `tests/test_v3_detached_preflight_crossbind_run794.py` created
  `2868f66aefd48d9cadfe055edf7fa414a9abd17e`;
  subclass-fixture semantics correction
  `59a3f9aef0c2c1552e98f942c2d02afcf2117114`.
- Review accepts only exact local synthetic carriers. It binds device,
  tokenizer probe, capacity and wall budget; rejects booleans, invalid/NaN/
  infinite/nonpositive measurements, allocated VRAM exceeding reserved VRAM,
  reserved VRAM exceeding the reported capacity, and elapsed wall time over
  the frozen budget.
- Capacity equality is deliberately **exact**, conservative and
  non-normative; it does **not** infer the frozen experiment's eventual
  measurement tolerance or alter Draft PR #5's code or gate.
- All return authority flags are False. No runtime/hardware measurements,
  identities or approval evidence are fabricated.

## Package C: deterministic synthetic improvement proposal identity
(26 submitted tests)

- `src/ark/agency/disconnected_improvement_proposal.py` created
  `4bc73354dabb532f4cd7d3e2696278c67ff91a7a`;
  grammar/domain fix `1f20e170bcec70cca782fed070bdc4e2775cd3c8`.
- `tests/test_disconnected_proposal_identity_run794.py`:
  `e2958e8310c880b7eda044772da51a4ab99b2355`.
- Proposal IDs bind the policy revision, issue/category, component, change
  class, owner/namespace digest and normalized source digest set. The routine
  deduplicates equal proposals and counts repeated synthetic observations
  without disclosing plaintext private evidence.
- The API is memory-only and deliberately **does not** yet implement the
  durable, approved proposal lifecycle described in the nonfrozen
  `CONTROLLED_SELF_IMPROVEMENT_PROPOSAL_CONTRACT.md`. Return flags deny code
  changes, training, Candidate promotion and protected-evaluation opening.
  Content-free hashes remain linkable metadata and are not true consent.

## CI and claim discipline

- New/source/test package HEADs above were saved through the normal
  GitHub Contents API, without force pushes or raw Git ref bypasses.
- **61 test cases have been submitted** (9 + 26 + 26). This report does
  **not** claim they are all passing until the six matrix jobs on a matching
  exact HEAD complete successfully.
- At intermediate inspection, [CI #43041371867](https://github.com/Iam-2squared/ark-ai/actions/runs/43041371867)
  for the mock receipt source+tests was Ubuntu 3/3 GREEN and Windows
  3/3 IN PROGRESS; [#43041940154](https://github.com/Iam-2squared/ark-ai/actions/runs/43041940154)
  for the corrected V3 tests and [#43042380723](https://github.com/Iam-2squared/ark-ai/actions/runs/43042380723)
  for proposal source+tests were QUEUED.
- Separate CI jobs are not proof of real GGUF, actor consent, external
  effect, cost approval or path/identity provenance. No local/physical
  machine pytest, Ruff, GPU, model validation or protected-eval test is
  claimed.

## Next plan / 今後の方針

1. Resolve exact-head 6-job GitHub CI for the combined three packages; on
   failure inspect specific job logs and make only a semantics-preserving
   correction while preserving independent lanes.
2. Continue Memory CAS/ABA, global event high-water, expiry and manual-only
   COMMIT-UNKNOWN custody, with exact SQLite snapshot/independent evidence.
3. Continue Planner durable crash recovery, terminal propagation and
   unknown-WRITE quarantine; no automatic replay of ambiguous external effects.
4. Keep ToolRegistry, PermissionGate, one-shot occurrence and audit-before-
   action bound to **disconnected mock only** until lower-layer proof is
   exact-head GREEN and separate real approval authority exists.
5. Review eventual durable proposal lifecycle and V3 preflight tolerances
   without changing frozen contracts, spending, opening evaluation,
   generating Candidates, or resuming UI development.

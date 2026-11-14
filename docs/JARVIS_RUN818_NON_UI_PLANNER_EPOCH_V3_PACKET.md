# ARK AI Run818 — Planner restart input epochs and detached V3 packet boundaries

## Scope and exact authorization

This run is strictly FREE-ONLY and NON-UI on Draft PR #8,
`research/jarvis-foundations`. It performs **no** candidate generation,
paid/external GPU work, protected V2 evaluation, tool dispatch, automatic WRITE
replay, account connection, Memory deletion, notification, main merge, or
physical-PC action. Paused UI PR #9 and gated V3 PR #5 remain Draft/unmerged
and untouched. Frozen V1/V2/Local UI/Launcher contracts/evidence remain frozen.

Work basis: Run817 HEAD `586294de7aca4ce08cd8167047c361ffacf4f773`.
Run817 added registry-bound UNKNOWN and coherent Memory restart *read-only*
bridges, and its existing [CI #43214269557](https://github.com/Iam-2squared/ark-ai/actions/runs/43214269557)
was observed **GREEN in all six** Windows/Ubuntu × Python 3.11–3.13 jobs.

## Package A — Planner late source drift between two independent reviews

- Source: `src/ark/agency/disconnected_planner_slot_restart_bridge.py`,
  change commit `d4a17905182cd40f4271fdd6992a93c1d14c31f0`.
- Test: `tests/test_planner_slot_source_epoch_run818.py`,
  commit `00fcfb24f270f762bcf7d7cbf65589c9afd647da`
  (**7** cases, including the unchanged authorized-denial baseline).
- The existing Planner bundle review executes before a separate SQLite WRITE
  slot reviewer. The earlier `stable()` verified `offline_steps` but not
  the remaining source carriers after the second review. A reentrant
  ledger callback could reflectively change a previously inspected Planner
  claim, observation, recovered step status, tail, or dependency digest,
  leaving the output detached from the original evidence.
- A local source epoch now captures the actual reference identities and
  top-level fields of the Planner/ledger/witness inputs before both reviewers.
  The same snapshot is checked after both reviews and at final return.
  Six fault-injection tests alter distinct carriers *inside the real ledger
  open callback after the Planner child review* and must fail closed.
- This is **not** atomic cross-store execution, authenticated plan provenance,
  user consent, trusted clock, real tool dispatch or safe WRITE retry.
  Immutable tuples protect their own elements; this is process-local
  reflective drift detection, not defense against arbitrary compromised Python.

## Package B — strictly free detached V3 packet test matrix

- Test file `tests/test_detached_v3_packet_boundaries_run818.py`,
  commit `58fa49b66ae1c9ccf676e958e076fa82ed8b12d3`
  (**30** cases). Production V3 code and PR #5 are **unchanged**.
- Covers exact canonical UTF-8 JSON and its byte limits; duplicate root and
  nested keys; BOM, invalid UTF-8, oversize, exponent overflow and NaN;
  unauthorized/unknown fields; device/capacity/tokenizer mismatches;
  bool and precision-losing numerics, VRAM ordering, timeout, negative
  measurement, and result denial invariants. Mutable or non-byte packets
  are refused; replaced denial property code must never execute.
- A valid synthetic receipt is a local crosscheck, **not** an immutable
  provider identity, GPU entitlement, billing approval, Candidate identity,
  training authorization, independent provenance or evaluation PASS.

## Evidence and next integration gates

- Run816 exact checkpoint HEAD `513893e2c3608cdbfbad4d8c59914a9a40564b27`
  [CI #43203510842](https://github.com/Iam-2squared/ark-ai/actions/runs/43203510842):
  previously confirmed GREEN 6/6.
- Run817 HEAD `586294de7aca4ce08cd8167047c361ffacf4f773`
  [CI #43214269557](https://github.com/Iam-2squared/ark-ai/actions/runs/43214269557):
  GREEN 6/6 as observed.
- Run818 Planner source/test HEAD `00fcfb24f270f762bcf7d7cbf65589c9afd647da`
  [CI #43215695670](https://github.com/Iam-2squared/ark-ai/actions/runs/43215695670):
  Ubuntu 3/3 GREEN, Windows three IN PROGRESS at the report snapshot.
- The V3 test-only HEAD and eventual checkpoint-result HEAD require their
  *own* six-job evidence. Merely writing tests does not prove they PASS.
- Integration order: (1) confirm all six exact-head CI jobs and investigate
  actual logs on failure; (2) preserve Planner UNKNOWN/WRITE quarantine and
  registry/permission/audit-before-action identity across a deliberately
  disconnected Mock Executor; (3) complete coherent Memory CAS/ABA and
  COMMIT-UNKNOWN recovery against independent retained evidence; (4) keep
  V3 preflight, identity, cost and human-approval gates closed; (5) defer
  new frontend work until the user explicitly resumes it.

**ARK/JARVIS is NOT_PASSED.**

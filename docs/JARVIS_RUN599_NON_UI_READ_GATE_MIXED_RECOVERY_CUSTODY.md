# Run599 — Detached READ gate and mixed-plan recovery denial (non-UI)

**Scope:** Draft PR #8, `research/jarvis-foundations`. Work basis: `51d54e1d66797f6597103b61d6703917c182a4a2`, the Run598 checkpoint HEAD. This is an implementation note, not a new normative contract or a PASS certificate.

## Package A — Independent registered READ-wave PermissionGate

- Source: `src/ark/agency/disconnected_read_cycle.py`, commit `18826f233ad801ac36112a8d4abf261576094977`.
- Regression: `tests/test_read_cycle_original_gate_before_call_run599.py`, commit `3b82f9e72a4df23ff1de59918213bcdb2d605bb5`; **5 authored parameter-expanded cases**.
- An upstream plan preflight validates its own PermissionGate method, but a later callback could substitute the class or instance method before the downstream independent READ-wave authorization. The downstream code now statically compares the exact method against its own import-time identity **immediately before** its direct grant call and rechecks after the call. A substituted method is refused without invoking that substitute.
- Four synthetic tests inject a counterfeit class/instance method after a successful preflight or during the independent registry rebind. The counterfeit-call counter must stay at zero; a separate positive test retains two deterministic shadow waves. All tests use a backend that throws if invoked. No external READ, WRITE or OneShot token consumption is authorized.
- Limit: this is in-process implementation substitution detection; it cannot authenticate installed code, a trusted execution environment, clock, real-world consent or cross-process exactly-once behavior.

## Package B — Mixed-plan crash recovery result authority

- Source: `src/ark/agency/disconnected_write_recovery_fence.py`, commit `1302102d01471d03afa70d8a894b9935b5c1861a`.
- Regression: `tests/test_mixed_recovery_false_descriptor_run599.py`, commit `2008fdd889e2c45f300a17ca84d66fa4ce633f84`; **6 authored parameter-expanded cases**.
- The offline recovery report already checks all four denied authority flags and revalidates input/disposition/result integrity after getters. The extra final check now rejects a substituted class denial descriptor even if the getter returns exactly False. It runs after existing mutation diagnostics to preserve earlier refusal types.
- Tests cover all four false-looking replacements, a late digest callback replacement, and a valid plan containing an UNKNOWN WRITE, held dependent READ and independent mockable READ. **READY_MOCK_ONLY never permits dispatch.** RUNNING/UNKNOWN WRITE remains quarantined and must not be blindly retried.
- Limit: the final descriptor check is not a pre-invocation verification for this isolated diagnostic; no independent custody, real execution permission, or externally attested outcome is claimed.

## Package C — Offline observation freshness denial integrity

- Source: `src/ark/observation_reuse_review.py`, commit `cd68014a89ea557499d374106c92bf362c57d0ac`.
- Regression: `tests/test_observation_reuse_false_denials_run599.py`, commit `a2f29cfe8ab9a86df2a23d03cef8096f275a6d91`; **6 authored parameter-expanded cases**.
- After the existing two freshness reviews, double denial getter checks, and exact source/result epoch rechecks, the offline reuse receipt additionally compares the four deny-only property descriptors to their import-time identities. A replacement that still returns False must not masquerade as the original privacy/authorization contract.
- Tests exercise four false-looking substitutions, a late substitution from the current-lineage callback, and a valid private transcript fixture. This is a **synthetic transcript descriptor**, not a microphone or media capture. No raw content or external disclosure is sent.
- Limit: the final identity check runs after getters to preserve prior mutation diagnostics; it is not independently attested executable identity or pre-call prevention of in-process callbacks. The result never authorizes capture, disclosure, notification or dispatch.

## CI evidence / provenance at documentation time

- Previous **exact Run598 checkpoint-head six-job GREEN:** [CI #41776237202](https://github.com/Iam-2squared/ark-ai/actions/runs/41776237202), Ubuntu and Windows, Python 3.11/3.12/3.13. This evidence **predates Run599 changes**.
- For Package A test HEAD `3b82f9e72a4df23ff1de59918213bcdb2d605bb5`, [CI #41780985851](https://github.com/Iam-2squared/ark-ai/actions/runs/41780985851): Ubuntu 3/3 completed-success, Windows 3 in progress when sampled. **Not final-head GREEN.**
- For Package B test HEAD `2008fdd889e2c45f300a17ca84d66fa4ce633f84`, [CI #41781253119](https://github.com/Iam-2squared/ark-ai/actions/runs/41781253119): in progress when sampled; exact six-job outcome pending.
- New cases are **17 authored definitions**, not independently executed local pytest passes. Intermediate content writes each trigger normal CI; no manual duplicate workflow run was started.

## Boundaries and next work

PR #5 (V3) remains Draft, gated and unmerged; PR #8 remains Draft; PR #9 (Command Center UI) remains Draft and fully paused. No main merge, frozen-contract or evaluation change, live backend/observation capture, physical-PC access, GPU, paid service, Candidate generation/promotion, protected V2 final evaluation, account connection or destructive action.

1. Confirm final exact-head CI. On failure, inspect real job logs; use only normal permitted Contents API for minimal semantics-preserving fixes.
2. Keep synthetic audit-before-mock-action, occurrence and permission receipt integrations **disabled-by-default** pending source-level and exact-head GREEN evidence. Audit rows and internal hashes are not permission or external effect proof.
3. Test Memory COMMIT-UNKNOWN reconciliation with retained independent witnesses and Planner restart terminal/unknown propagation, with no automatic retry.
4. Continue Personal Context revocation isolation, proactive replay fences, observation fixture privacy and V3 pre-paid guard audit in independent non-UI lanes. UI remains paused; overall ARK/JARVIS/V3 **NOT_PASSED**.

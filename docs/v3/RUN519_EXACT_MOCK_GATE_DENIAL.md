# Run519 — Exact-type mock gate denial (free-only)

**Scope:** synthetic V3 simulation only. No experiment execution, historical V2 opening, Candidate artifact, model download, human review, protected scorer access, GPU or paid service.

## Exact code evidence

- Work basis: c250b2a44b7fc6cab8b18f5d6693e32019a7453f (prior Run518 documentation HEAD).
- Code: src/ark/learning/gate.py, commit 91afc82809ce036dac9cc3c6b076f1bff9a2a275, source blob 78f5f95bd0a1b334fd4aad35691fed982b24d467.
- Cases: tests/v3/test_mock_gate_exact_inputs_run519.py; combined source+test HEAD 80c9bcef886fb619b8f58bee77a8e20755c4d627.
- Exact source+test CI: [41270771228](https://github.com/Iam-2squared/ark-ai/actions/runs/41270771228) **6/6 GREEN / SUCCESS** (three Ubuntu, three Windows Python 3.11–3.13). This result does not establish anything about later HEADs.
- **25 newly authored pytest cases**, including parametrized exact-type and input-budget rejections. Do not conflate authored cases with separately executed local test counts. No local full-checkout pytest/Ruff performed.

## NEW behavior and invariant

simulate_gate now enforces exact SimulationEvidence and exact "mock" measurement kind before synthetic policy analysis. The two synthetic run matrices must each contain exactly two bounded nonempty tuples (at most 4096 exact booleans per tuple); controlled, provenance_reviewed, contamination_suspected and memory_error must be exact booleans, while runtime_failures must be an exact integer. Values such as 1 == True, False == 0, an equal-valued float, a list masquerading as a tuple, or an unbounded answer sequence do not become simulation-eligible.

Malformed fixtures return simulation_decision: REJECT, reason noncanonical_mock_evidence, automatic_promotion: false, model_promotion_status: NOT_EVALUATED, and v3_gate: NOT_PASSED. Non-mock/derived evidence stops with StopRequired. For valid exact mock inputs, the previous simulation-only criteria and outcomes remain unchanged.

This does **not** change the frozen Experiment 001 contract, historical V2 scorer, evaluation opening rules, training hyperparameters, dataset/contamination requirements or Candidate promotion gates. **ARK/JARVIS/V3 overall NOT_PASSED.**

## Remain blocked

Real Candidate/adapter/weights, materialized and verified model/tokenizer identities, actual 120/30 human-approved examples, contamination decisions, physical Linux/device identity, explicit monetary/provider hard caps, external compute, protected evaluation, promotion and main merge remain blocked by their separate controlling gates. PR #5 remains Draft and unmerged.

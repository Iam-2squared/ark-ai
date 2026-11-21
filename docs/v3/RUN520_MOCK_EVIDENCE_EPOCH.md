# Run520 — V3 synthetic mock-gate evidence epoch

**Branch:** `research/v3-learning-evaluation` / [Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5). **Source+test HEAD:** `2b3ceb3455616f8e3864e910ea30dda8786c3efe`. Work began at prior Run519 documentation HEAD `a5ef1aaa4dd840afd5916fa9fea32ccb83cfdc9a`.

## Implemented (simulation only)

- `src/ark/learning/gate.py`: the mock-only `SimulationEvidence` is captured as an exact carrier epoch before policy calculation. All checks operate on that immutable typed snapshot, with complete rechecks before the rejection/eligible result is returned.
- A reflected mutation of frozen evidence, a late getter changing a control flag, a swapped but equal-valued tuple, or a late change to `measurement_kind` produces `REJECT / noncanonical_mock_evidence` rather than an apparently eligible simulation.
- Existing valid synthetic decisions still use the prior frozen regression, improvement, provenance, contamination, runtime, and memory-error policy. `ELIGIBLE_IN_SIMULATION_ONLY` is explicitly **not** V3 PASS, Candidate promotion, protected V2 opening, training, real evaluation, spending permission, or external execution.
- `tests/v3/test_mock_gate_epoch_run520.py` adds **17 newly authored pytest cases**: exact unchanged mock, seven existing policy outcomes, six late reflected input mutations, one last-getter mutation, one same-value tuple substitution, and explicit real-measurement rejection.

## Evidence and limitations

- Exact source+test [CI run 41274334811](https://github.com/Iam-2squared/ark-ai/actions/runs/41274334811): **SUCCESS (6/6 environments GREEN)**, observed after the source and test file were committed.
- No independent local full-checkout pytest/Ruff was executed. The case count is authored test parametrizations, not a claim of local PASS.
- This is a detached synthetic assessment. It does **not** construct real Candidate weights, download model bytes, inspect protected V2 final evaluation, validate actual model identity, use GPU compute, authenticate provenance, or authorize costs.
- Frozen Contract 1, V1/V2/Local UI/Launcher evidence, main branch, PR #5 Draft state, and user approval boundaries remain unchanged.

## Next

Keep V3 identity/path/byte custody and reproducibility audits free-only. Actual Candidate generation, protected V2 final evaluation, model promotion, hardware/provider usage and human review decisions remain blocked by their original explicit gates. No main merge.

# V3 first real experiment — execution supplement

Status: **DESIGN CLOSURE COMPLETE / EXTERNAL IDENTITIES PENDING / REAL TRAINING BLOCKED**.

This document operationalizes Contract 1 without changing it. Contract 1 remains byte-for-byte frozen and its recorded SHA remains authoritative. No real training, adapter generation, external compute use, candidate frozen evaluation, promotion decision, or main merge is authorized by this supplement.

## Experiment 001 frozen semantic design

- ID: `v3-format-compliance-001`.
- Objective: independent instruction/output-format compliance, never `math-02` memorization.
- Dataset: exactly 120 approved train + 30 approved validation examples.
- Source/template groups may not cross splits.
- Proposed method: LoRA, rank 8, alpha 16, dropout 0, q_proj/v_proj.
- One epoch, LR 1e-4, seed 42, sequence length 256, microbatch 1, gradient accumulation 8.
- One configuration; no hyperparameter sweep or validation-driven retuning in experiment 001.
- Historical V2 cases, expected-answer-derived templates and scorer-derived material are forbidden from train/validation.

These settings are a controlled first-run precommit, not claimed optimums.

## Claude independent-review disposition

Accepted: off-device GPU as the preferred first 4B route; Development/Validation/final-frozen separation; semantic/paraphrase and family contamination review; category regression review; paired Q4_K_M comparison; pipeline completion separated from promotion.

Modified: local CPU training is not declared impossible, only unapproved/unmeasured for experiment 001; LoRA remains the precommitted first method unless pre-run feasibility proves it cannot execute under the approved environment; provider/model/pricing are execution facts rather than Contract constants.

Rejected for experiment 001: changing 120/30 to 50/20/40, hyperparameter sweeps, expanding target modules without a pre-result Contract amendment, replacing the V2 2+2 opening budget, post-result threshold relaxation, or calling cross-backend/pre-quantization deltas pure training effect.

## Closure matrix

`DESIGN_CLOSED` means the policy/acceptance schema is fixed but execution-specific evidence is still required. `EXTERNAL_PENDING` means the exact identity cannot truthfully be frozen until the artifact/environment exists. No pending row may be guessed.

| Identity | Fixed decision / required evidence | State |
|---|---|---|
| Base model | `Qwen/Qwen3-4B-Instruct-2507`; immutable HF revision plus per-file SHA-256 manifest captured before training; never train deployed GGUF | DESIGN_CLOSED / EXTERNAL_PENDING |
| Tokenizer/template | Must come from the exact same frozen HF revision; hash tokenizer/config/template-bearing files and record rendered chat-template probe digest | DESIGN_CLOSED / EXTERNAL_PENDING |
| Dataset | Canonical UTF-8 artifact from existing deterministic builder; exactly 120 train/30 validation; per-example provenance/rights/reviewer/independence; artifact SHA-256 | DESIGN_CLOSED / DATA_PENDING |
| Contamination | Existing exact/conflict/group checks + pinned lexical/fuzzy audit + separately pinned semantic detector; flagged pairs 100% human-reviewed plus deterministic non-flagged audit sample | DESIGN_CLOSED / DATA_PENDING |
| Training stack | Reproducible Linux GPU environment preferred; exact OS/image digest, Python, torch, transformers, PEFT, accelerate, CUDA/runtime and optional bitsandbytes recorded; no unpinned notebook state | DESIGN_CLOSED / EXTERNAL_PENDING |
| Hardware | Single approved accelerator identity, VRAM, driver/runtime; preflight must demonstrate model load + one forward/backward training step without OOM before full run | DESIGN_CLOSED / EXTERNAL_PENDING |
| Method | LoRA under frozen experiment-001 config. QLoRA substitution is allowed only before any real result if LoRA preflight fails feasibility and requires explicit reviewed amendment | DESIGN_CLOSED |
| Budget | Exactly one full experiment-001 Candidate training run. Failed preflight is not a Candidate. Full-run retry/new Candidate requires new precommit. Monetary ceiling and wall-clock timeout require user approval before external compute | DESIGN_CLOSED / USER_PENDING |
| Training recipe | Repository-owned executable/config only; code SHA + config SHA + dataset/base/env identities emitted before first optimizer step; fail closed on mismatch | DESIGN_CLOSED / IMPLEMENTATION_PENDING |
| Adapter/export | Save adapter separately, reload verify, merge into a separate base copy, convert with pinned llama.cpp revision, quantize Q4_K_M with pinned binary/settings, hash every artifact; never overwrite Current | DESIGN_CLOSED / EXTERNAL_PENDING |
| Paired baseline | Regenerate comparison-only base Q4_K_M from exact frozen HF base using same converter/quantizer as Candidate; historical V2 GGUF remains immutable | DESIGN_CLOSED / EXTERNAL_PENDING |
| Evaluation | Validation before V2; same scorer/runtime contract for Current/Candidate where comparable; category report + hard runtime/V2 regression blockers; final V2 budget remains 2 Current + 2 Candidate fresh processes after explicit authorization | DESIGN_CLOSED / IMPLEMENTATION_PENDING |
| Storage/privacy | First experiment contains no private sessions, personal memory, secrets or unattributed text. Persistent run directory is create-only; raw data, manifests, logs, adapter, merged/export hashes and decisions retained; no automatic deletion | DESIGN_CLOSED |

## Dataset schema and construction

Each accepted example must carry stable ID, split, source type/reference, source digest, source/template family (`split_group`), prompt/input, approved target, rights-to-use statement, reviewer, approval state and independence attestation. Generated examples require independent human review and traceable generator/provenance; generator output is never auto-approved.

The deterministic builder must reject malformed/unapproved entries, exact normalized duplicates, conflicting targets, split conflicts, forbidden source references and cross-split groups. The final bytes contain no clock/random metadata and are sorted by stable ID. The manifest records input/accepted/rejected/duplicate/contamination counts, split counts, byte length and SHA-256.

The dataset objective is varied strict instruction/output-format compliance. Coverage must include multiple independently authored source/template families across restricted numeric/symbolic answers, YES/NO or choice constraints, strict JSON/structured output, restricted code/text forms and multi-constraint instructions. Category counts are descriptive evidence, not post-hoc weighting targets.

## Contamination audit protocol

1. Keep the historical V2 denylist/scorer outside trainer-visible payloads.
2. Run exact normalized input, source-reference, distinctive-target, conflict and group checks.
3. Run a pinned lexical/fuzzy similarity detector against frozen evaluation prompts without exporting expected answers to the training environment.
4. Run a separately pinned semantic/paraphrase detector. Its model/revision, preprocessing, similarity metric and threshold are frozen before the final dataset audit. The threshold is a triage heuristic, never proof of independence.
5. Human-review 100% of flagged pairs. Also review a deterministic SHA-ordered sample of at least 10% of non-flagged accepted examples, with a minimum of 15; if any sampled item shows suspicious semantic leakage, expand manual review to 100% of accepted examples before approval.
6. Record reviewer decisions and limitations. Any unresolved contamination suspicion blocks training.

No private chat, personal memory, benchmark-derived answer template, scorer code, V2 expected-answer-derived template, secrets, or licensing-unclear material is allowed.

## Training environment and preflight

The first 4B path uses off-device GPU compute only after explicit cost/external-compute authorization. Local Windows remains inference/governance. The exact provider is intentionally not frozen here.

Before the one full Candidate run, execute a non-Candidate feasibility preflight using the exact frozen base, tokenizer, environment and LoRA configuration. It may use a tiny approved training subset solely to verify mechanics. Required evidence: accelerator identity/VRAM, successful base load, tokenizer/template probe, one forward/backward optimizer step, peak allocated/reserved VRAM, wall time, dependency manifest and no OOM/runtime error. The preflight may not open Validation or V2 and may not produce a promotable Candidate.

If LoRA preflight succeeds, method is LoRA. If it fails solely because the approved accelerator cannot satisfy memory feasibility, STOP; do not silently switch to QLoRA. A reviewed pre-result amendment is required.

## Exact full-run recipe contract

The executable implementation must validate all identities before the first optimizer step and write a create-only run manifest. Experiment-001 parameters are fixed: rank 8, alpha 16, dropout 0, q_proj/v_proj, LR 1e-4, one epoch, seed 42, max sequence length 256, microbatch 1, gradient accumulation 8. Optimizer, scheduler, precision mode, gradient-checkpointing state and package versions must be frozen in the execution snapshot before authorization; they cannot be inferred after the run.

The full run count is one Candidate. Any full-run crash is evidence and does not authorize an unrecorded retry. A retry requires a new precommit identifying whether it is the same recipe or a changed experiment.

## Export and paired-Q4 protocol

Candidate lineage is:

`frozen HF base -> frozen LoRA adapter -> verified reload -> merged separate HF copy -> pinned HF-to-GGUF conversion -> pinned Q4_K_M quantization -> Candidate GGUF`.

Every stage records SHA-256, bytes, tool revision and command/config identity. Current deployed GGUF is read-only and never an output path.

A V3 comparison-only baseline is generated as:

`same frozen HF base -> same pinned HF-to-GGUF conversion -> same pinned Q4_K_M quantization -> Paired Current GGUF`.

This paired artifact does not replace historical V1/V2 evidence. Deployment comparison claims are based on paired Q4_K_M artifacts under matched ARK runtime/config/scorer. Candidate pre-export versus Candidate Q4 may be reported on non-V2 validation only; any backend/precision/prompt-rendering difference is explicitly confounded and not called pure quantization loss.

## Evaluation architecture and blockers

### Development / mechanics
Training loss and non-frozen diagnostic probes may verify mechanics. They cannot change experiment-001 hyperparameters and cannot authorize V2 opening.

### Validation — 30 independent examples
Validation is evaluated only after Candidate artifact freeze and before V2. Paired Current and Candidate use the same frozen validation scorer/runtime contract where technically comparable. Report per-example result, strict-format pass rate, category counts/results, runtime failures and memory failures.

Validation is evidence, not an optimization loop for experiment 001. No threshold is relaxed after results. Because 30 examples give wide uncertainty for small deltas, no arbitrary +5% claim is required for V3 pipeline completion. Promotion still follows Contract 1 and ultimately requires the historical V2 conditions.

Hard blockers before V2 opening: any unresolved provenance/contamination issue; incomplete artifact lineage; scorer/runtime mismatch not explicitly characterized; Candidate runtime or memory failure on validation; or export/quantization integrity failure.

### Historical V2 final opening
After all Candidate artifacts/provenance and validation evidence are frozen, STOP for explicit authorization. Then exactly two fresh-process Current runs and two fresh-process Candidate runs use the immutable V2 suite/scorer/policy with matched runtime/settings/export quantization. A Current-PASS -> Candidate-FAIL task is a promotion blocker; any runtime/memory failure is a blocker; repeated outcomes must agree; at least one previously failing task must improve for promotion eligibility. Results cannot retune experiment 001.

## Storage, privacy and evidence retention

All experiment evidence is stored under a new immutable run ID outside Current model paths. Preserve dataset manifest/hash, contamination report, environment/hardware manifests, preflight report, training config/logs, adapter and export manifests/hashes, validation results, later V2 results and human decisions. No automatic cleanup. If external storage is used, only approved non-personal experiment data/model artifacts are transferred; credentials/secrets are never committed to the repository or evidence bundle.

## Remaining work before training authorization

Design policy is now closed as far as it can be without fabricating external identities. The remaining work is concrete evidence/implementation:

1. resolve exact immutable HF base/tokenizer revision and file hashes;
2. create/review/freeze the real 120/30 dataset and contamination report;
3. implement the repository-owned preflight/full-run manifest validator and lineage-aware evaluation adapter;
4. select an actual GPU environment, pin the environment/dependencies and run only the non-Candidate preflight after external-compute authorization;
5. pin exact llama.cpp converter/quantizer revision and prove paired-base export compatibility;
6. obtain independent review of the fully populated execution snapshot;
7. STOP for explicit authorization before the first real Candidate training command.

No item above authorizes external compute, spending, adapter/weight generation, V2 opening, promotion, or main merge.
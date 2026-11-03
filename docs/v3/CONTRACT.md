# V3 Learning & Evaluation — contract 1 (pre-implementation freeze)

Base main: 6195beec55a2f97f68c53a1fef890f1f1422d6f1.
V1/V2 freezes, runtime, fixed 12-case suite, scorer and policy are immutable.
V2 math-02 remains FAIL; its problem, target and scoring behavior are not training data.

## Completion versus candidate promotion

V3 completion requires a provenance-complete **real learning pipeline demonstration**,
not guaranteed improvement: approved independent dataset, real controlled training,
candidate artifact, export/compatibility verification, same-contract baseline/candidate
evaluation, regression review, reproducibility evidence, human review, tests and CI.
A rejected candidate can satisfy pipeline demonstration. Mock training never satisfies
real learning, real artifact or V3 PASS. V3 remains NOT_PASSED until these gates close.

Candidate eligibility is stricter: genuine reviewed provenance; no contamination
suspicion; complete real evidence; same frozen suite/scorer/policy/config/runtime;
zero runtime/memory failures; no previously passing task regresses; at least one
previously failing task improves; repeat results consistent. Current and candidate
weight identities must differ intentionally, with candidate lineage linked to current
base weights and export settings. Model identity difference alone is not uncontrolled
when that is the sole intended intervention. All other differences block eligibility.
No automatic current-model replacement, no AUTO_PROMOTED state, no promotion CLI.
PROMOTION_ELIGIBLE is a recommendation requiring separate human authorization.

## Learning candidate and dataset boundary

Schema 1: candidate_id, source_type, source_reference, input, model_response,
evaluation, approved_target, rejection_reason, provenance, created_at, reviewer,
approval status, independence attestation and split group. Interaction logs are never
automatically adopted. Generated examples need independent quality/human approval.
Private sessions and unlicensed/unattributed text are rejected. Provenance must state
rights to use, source digest and a traceable reference; claims still require review.

Dataset builder rejects malformed/unapproved/contaminated examples; deduplicates by
normalized input; rejects conflicting targets or split assignments for one input.
Same source group may not cross train/validation. Only explicit train/validation splits;
frozen evaluation cannot be exported. Sort by stable IDs, UTF-8 canonical serialization,
no clock/random metadata in dataset bytes. Record input/accepted/rejected/duplicates/
contamination counts, split counts, bytes and SHA. Human attestation of independence
is mandatory: lexical detectors cannot prove absence of semantic contamination.

Contamination screening uses a separate read-only denylist derived from frozen
evaluation inputs/targets and source-reference patterns. Neither denylist nor scorer
code is passed to a trainer. Reject normalized input matches, distinctive near matches,
evaluation source references and distinctive expected-answer leakage. Common one-word
targets such as YES cannot prove leakage alone; reviewer must establish independent
example origin. Do not claim these heuristic checks are exhaustive.

## Training, registry and writes

TrainingConfig: version, base identity/hash, dataset hash, method/backend, seed,
hyperparameters, code SHA and dependency/hardware provenance. TrainingBackend protocol
returns TrainingRun and TrainingArtifact. Mock returns an explicitly non-model receipt,
never weights/adapters or measured learning scores. No real trainer executes in this PR.
Current model path is never an output. Writes are limited to a new explicit run directory;
existing outputs are not overwritten. No downloads, subprocess commands or external APIs.

Registry is append-only snapshots, hashes artifacts before acceptance, validates legal
transitions CREATED → TRAINING → TRAINED → EVALUATING → REJECTED/PROMOTION_ELIGIBLE
→ ARCHIVED (failure may reject earlier). Mock artifacts must never acquire real eligible
status. Archive preserves previous artifacts. Rollback means keep the original model
unchanged; switching models is a separate human operation, not a pipeline side effect.

## First experiment and evaluation budget (frozen before any results)

One candidate for independent output-format compliance. Planned dataset: 120 approved
train examples + 30 validation examples, grouped by source/template family with no
cross-split groups; all manually reviewed. No dataset is approved by this document.
One fixed configuration, seed 42, no validation-driven sweep in this first experiment.
Before training, freeze exact dataset/base/config/dependencies/hardware/export identities.
No real run if any identity or feasibility field remains unresolved.

After training and candidate artifact freeze: STOP for permission before first candidate
V2 evaluation. Planned budget: two fresh-process current runs and two fresh-process
candidate runs, same frozen suite/settings/runtime, no re-tuning from those outcomes.
Evaluation failure consumes the opening; no unrecorded retries. Further experiments
need a new precommit and explicit acknowledgement that V2 is already observed, not
an untouched holdout. Frozen suite cases are not training/validation examples.

## Hard stops and remaining gates

Stop before real training, weight/adapter generation, external compute use, first
candidate frozen-evaluation opening, real promotion decision or main merge. Stop and
ask before changing this contract. No automatic background work or V4–V10 scope.
This turn may implement deterministic infrastructure and simulation tests only.
Real training feasibility, artifact/export, real comparison, independent review and
human acceptance remain required for V3 completion. CI green is infrastructure only.

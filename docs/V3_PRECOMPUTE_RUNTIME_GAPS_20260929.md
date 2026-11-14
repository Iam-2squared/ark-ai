# V3 Pre-Compute Runtime Gap Review — 2026-09-29

Status: read-only review from PR #5 source. No training, preflight, protected evaluation, Candidate generation, or external compute was started.

Review basis: PR #5 head `d6d4c1954a85fc716b1c593ac55c85417912418f`.

## Confirmed existing protections

The official training CLI already verifies the frozen git checkout, code manifest, provenance/contamination bytes, measured runtime identity, authorization scope, and local-only model/tokenizer loading before full training.

The concrete HF runtime also validates the frozen experiment recipe and local base/tokenizer/dataset identities before model construction.

These protections remain intact and must not be weakened.

## Gap 1 — one-full-run budget is not a durable attempt ledger

The frozen snapshot requires `budget.full_candidate_runs == 1`, but that is a configuration invariant rather than durable evidence that the one allowed full-training attempt has already been consumed.

The current Candidate output directory is created only after the training loop reaches the save phase. A crash before output creation can therefore leave no durable Candidate-directory evidence that a full attempt already started.

Before real compute, the execution boundary should durably consume one attempt identity before model/training side effects begin. The identity should bind the exact authorized snapshot and the exact authorization artifact. Reusing the same authorization for a second full attempt must fail closed; a later attempt requires a new explicit authorization artifact.

## Gap 2 — concrete backend methods are a weaker entry boundary than the official CLI

`HfLoRAPreflightBackend.run()` and `HfLoRAFullRun.run()` call frozen-snapshot validation and local identity checks, but they do not independently repeat every CLI-level proof such as clean git checkout, code-manifest verification, measured runtime identity, and all external evidence-file binding.

The safe architecture is to make the compute backend require a validated immutable execution context produced by the official guard boundary, rather than allowing callers to pass an arbitrary snapshot dict directly.

## Gap 3 — output path can overlap trusted input/code trees

The full-run backend requires a new non-symlink output directory under existing non-symlink parents, but the current check does not prove the canonical output path lies outside the frozen base-model tree and runtime code checkout.

Before real compute, canonicalized output roots should be required to be disjoint from:

- frozen base/tokenizer bytes;
- the verified runtime code checkout;
- dataset/evidence inputs;
- protected evaluation material.

This prevents Candidate writes from mutating bytes that were previously identity-verified.

## Gap 4 — identity verification has a verify-to-use window

The runtime hashes local base/tokenizer bytes in `_verify_local_identities()`, then later loads the model/tokenizer from their paths.

A local filesystem mutation between those stages could change the bytes actually loaded without changing the already-completed identity check.

Before real compute, use a stable read-only materialization boundary or re-verify the exact materialized identity immediately around the load boundary and fail closed if the source changes.

## Gap 5 — frozen seed does not explicitly seed trainable initialization

The frozen seed is used to derive deterministic training-row order. The current model/PEFT construction path does not explicitly seed torch/CUDA before LoRA adapter initialization.

Before real compute, the runtime must apply the frozen seed to all relevant local RNGs before any trainable parameter initialization and record enough evidence to reproduce that ordering.

## Gap 6 — reported wall/VRAM metrics are training-phase metrics

The runtime resets peak CUDA memory statistics after model/adapter/optimizer setup and starts the reported elapsed timer near the training loop. Therefore current reported `peak_vram_mib` and `wall_seconds` do not represent the complete guarded attempt from identity checks/model load through evidence save.

This is not necessarily wrong if the metric is explicitly named as training-phase evidence, but it must not be interpreted as whole-attempt cost/resource evidence. Before a paid run, either rename/scope these metrics or add separately measured whole-attempt values.

## Gap 7 — generated preflight authorization packet is not runtime-consumed

PR #5 can generate a deterministic preflight authorization packet with its own SHA-256, but the
official `preflight` CLI accepts the execution snapshot and evidence paths directly. It does not
require the reviewed packet as an input or verify that the packet digest presented at execution
matches the exact packet the user approved.

Before any real preflight, the runtime boundary should consume an explicit user-provided approval
artifact that binds the packet digest and exact execution core. A snapshot boolean alone must not
stand in for the reviewed artifact.

## Gap 8 — full training lacks a distinct runtime-consumed second approval artifact

The official `train` CLI validates training authorization in the snapshot and verifies the frozen
preflight report, but it does not require a separate post-preflight approval artifact that binds the
accepted preflight report SHA-256, final execution snapshot/core, budget, and the one allowed full
Candidate attempt.

Before real full training, require a distinct second approval artifact and durably consume its
one-shot attempt identity before model/training side effects. The preflight approval must never be
reused as full-training authorization.

## Required closure before real Candidate compute

1. runtime consumption of the exact user-approved preflight packet/artifact;
2. separate post-preflight full-training approval bound to snapshot/core + accepted preflight report + budget;
3. durable exactly-once attempt consumption keyed by the full-training approval artifact;
4. one guard boundary that all concrete compute backends must receive/verify;
5. canonical output/input/code path disjointness;
6. stable verify-to-use model/tokenizer identity;
7. explicit deterministic RNG seeding before trainable initialization;
8. unambiguous whole-attempt versus training-phase resource metrics.

These are free pre-compute hardening items only. They do not authorize GPU use, spending, Candidate generation, protected V2 opening, promotion, Contract changes, or main merge.

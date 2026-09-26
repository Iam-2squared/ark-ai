# ARK AI Project Status

**LATEST**

Saved at: **2026-09-26 15:24:00 JST (+09:00)**

## Checkpoint identity

- Branch: `research/v3-learning-evaluation`
- PR #5: **Draft / unmerged**
- Work basis HEAD: `f5b8f3c68fa2693df793d5fe4cb44b135f1f951b`
- New work: `f5b8f3c68fa2693df793d5fe4cb44b135f1f951b` — frozen training-metrics validation.
- Prior verifier work: `a684755de8f761ce2df5d9abed9839ef6a123dd9`
- Previous checkpoint: `01b29ddb15dfe12058e8ba306242e8458ec7c6fa` — superseded.
- The resulting checkpoint commit cannot be embedded in this file; record it at the next update.
- Roadmap: **V3 Learning & Evaluation — Draft / NOT_PASSED / Pre-Paid-Compute closure**

## Current state / 現在の状況

V1/V2 remain OFFICIAL PASS. Local UI v1 and Launcher/Gate Runner evidence remain frozen. V3 Contract 1 remains frozen. PR #5 remains Draft. Candidate-run evidence now has create-only freeze, later byte re-verification, and strict training-metrics validation. No external compute, Candidate generation, protected V2 opening, promotion, Contract change, or main merge occurred.

## Work completed in this batch

### New work

- Closed the training-metrics evidence schema in `run_manifest.py`.
- Requires exact fields, schema v1, matching experiment/snapshot/dataset identities, exactly 15 optimizer steps and 120 microbatches, a positive integer trainable-parameter count, finite loss/VRAM/wall-time measurements, and the exact frozen method bytes.
- Rejects boolean-as-integer coercion, invalid measurements, recipe drift, and unknown post-hoc fields.
- Added regression tests for metric type/value drift, recipe drift and extra fields.
- Updated the Pre-Paid-Compute Gate documentation.

### Previously completed this run

Create-only Candidate `run-manifest.json`, frozen-run re-verification, post-freeze byte-tamper detection, canonical JSON enforcement, exact optional manifest digest verification, and the Ruff import-order fix.

## Tests / CI / evidence

- CI #146 / run `36222944733`: **GREEN 6/6**.
- CI #148 / run `36223351050` on verifier HEAD `a684755de8f761ce2df5d9abed9839ef6a123dd9`: **GREEN**.
- Latest metrics-hardening HEAD `f5b8f3c68fa2693df793d5fe4cb44b135f1f951b`: CI #150 / run `36223574582` is **IN PROGRESS** at save time. No GREEN claim is made.
- Earlier CI #144/#145 failures were Ruff-only and are superseded.
- Frozen V1/V2/Local UI/Launcher evidence unchanged; V3 Contract unchanged; protected V2 final evaluation unopened; no Candidate artifacts generated.

## Frozen contracts / evidence unchanged

V1 freeze; V2 fixed suite/scorer/policy and known `math-02` format-only failure; Local UI/Launcher evidence; V3 Contract 1/hash; protected V2 evaluation/opening budget.

## Unresolved blockers / authorization boundaries

1. Immutable HF revision, materialized base/tokenizer hashes and chat-template probe.
2. Human-approved/provenance-complete 120/30 dataset and contamination decisions.
3. Exact Linux/container plus Python/torch/transformers/PEFT/accelerate/CUDA identities.
4. Exact llama.cpp revision and converter/quantizer identities.
5. GPU/device/VRAM/driver proposal plus approved JPY/time ceilings and billing-cap evidence before external compute.
6. CI #150 must become GREEN before the latest head is treated as preflight-ready.
7. No external compute, Candidate generation, protected V2 opening, promotion, frozen-Contract change, or main merge without required explicit authorization.
8. Frozen V3 Contract excludes V4–V10 implementation scope from this V3 workstream.

## Next plan / 今後の方針

1. Follow CI #150 and fix ordinary software/plumbing failures without weakening gates.
2. Continue free Candidate reload/export and reproducibility closure.
3. Close identity/export gaps requiring no fabricated external facts.
4. Keep provider/cost preparation offline and non-authorizing.
5. Re-read PR/head/status before every write; reconcile concurrent work and never force-push.

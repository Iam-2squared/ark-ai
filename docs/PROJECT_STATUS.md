# ARK AI Project Status

**LATEST**

Saved at: **2026-09-26 15:22:00 JST (+09:00)**

## Checkpoint identity

- Branch: `research/v3-learning-evaluation`
- PR #5: **Draft / unmerged**
- Work basis HEAD: `b1a6d8e0a664488bea076ee4c0a34145eaad30e0`
- Candidate-run evidence commit: `7569c210bbcabdba1a5077ba4c9bee4d9f1ac223`
- Latest fix commit: `b1a6d8e0a664488bea076ee4c0a34145eaad30e0`
- Previous checkpoint: `4a52e2c49ccd3f85079ea1e156417caca43c7d8c` — superseded.
- This file cannot contain its own resulting checkpoint commit SHA; record that SHA in the next checkpoint.
- Roadmap: **V3 Learning & Evaluation — Draft / NOT_PASSED / Pre-Paid-Compute closure**

## Current state / 現在の状況

V1/V2 remain OFFICIAL PASS. Local UI v1 and Launcher/Gate Runner evidence remain frozen. V3 Contract 1 remains frozen. PR #5 stays Draft. No external compute, Candidate generation, protected V2 opening, promotion, Contract change, or main merge occurred.

## Work completed in this batch

### New work

- Added create-only Candidate run evidence closure in `src/ark/learning/run_manifest.py`.
- The manifest inventories existing adapter/tokenizer/metrics/snapshot files by SHA-256 and bytes, rejects symlinks, and is create-only.
- Saved execution-snapshot bytes must match the authorized canonical snapshot; metrics must bind to the same execution snapshot and dataset.
- The run manifest records Validation/V2/promotion as unopened or unauthorized.
- `HfLoRAFullRun.run()` now emits manifest path and SHA-256 after evidence writes.
- Added three focused tests and updated the Pre-Paid-Compute Gate.
- CI #144/#145 exposed one Ruff import-order issue only; `b1a6d8e0a664488bea076ee4c0a34145eaad30e0` fixes that ordering without semantic changes.

### Previously existing work

Dataset/provenance/contamination tooling, review binding, execution-snapshot validation, split preflight/training authorization, local identity hashing, runtime/git checks, preflight evidence, LoRA plumbing, validation comparison, lineage contracts and paired-Q4 planning remain intact.

## Tests / CI / evidence

- CI #143 / run `36220017532` on `767b17957ea4eb7561b5b0caa9e5ad6acc3aefd1`: **GREEN 6/6**.
- CI #144 / run `36222828905` on `7569c210bbcabdba1a5077ba4c9bee4d9f1ac223`: **FAIL at Ruff I001 only** before tests.
- CI #145 / run `36222912667` on checkpoint `4a52e2c49ccd3f85079ea1e156417caca43c7d8c`: same pre-fix Ruff failure.
- Latest fix HEAD CI: not yet confirmed GREEN at save time.
- Frozen evidence/contracts unchanged; protected V2 final evaluation unopened; no Candidate artifacts generated.

## Frozen contracts / evidence unchanged

V1 freeze; V2 fixed suite/scorer/policy and known `math-02` format-only failure; Local UI/Launcher evidence; V3 Contract 1/hash; protected V2 evaluation and opening budget.

## Unresolved blockers / authorization boundaries

1. Immutable HF revision, materialized base/tokenizer hashes, chat-template probe.
2. Human-approved/provenance-complete 120/30 dataset and contamination decisions.
3. Exact Linux/container + Python/torch/transformers/PEFT/accelerate/CUDA identities.
4. Exact llama.cpp revision and converter/quantizer identities.
5. GPU/device/VRAM/driver proposal plus approved JPY/time ceilings and billing-cap evidence before external compute.
6. GREEN CI on final preflight-authorizable head.
7. No external compute, Candidate generation, protected V2 opening, promotion, frozen-Contract change, or main merge without required explicit authorization.
8. Frozen V3 Contract excludes V4–V10 implementation scope from this V3 workstream.

## Next plan / 今後の方針

1. Confirm latest-head CI; fix ordinary failures without weakening gates.
2. Continue free Candidate evidence/reload/export and reproducibility closure.
3. Close identity/export gaps that require no fabricated external facts.
4. Keep provider/cost preparation offline and non-authorizing.
5. Re-read PR/head/status before every write; reconcile concurrent work and never force-push.

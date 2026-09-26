# ARK AI Project Status

**LATEST**

Saved at: **2026-09-26 15:09:00 JST (+09:00)**

## Checkpoint identity

- Branch: `research/v3-learning-evaluation`
- Target PR: #5 (**Draft / unmerged**)
- Exact work basis HEAD described by this checkpoint: `7569c210bbcabdba1a5077ba4c9bee4d9f1ac223`
- Primary new work commit: `7569c210bbcabdba1a5077ba4c9bee4d9f1ac223` — `feat(v3): close Candidate run evidence manifest`
- Previous checkpoint HEAD: `767b17957ea4eb7561b5b0caa9e5ad6acc3aefd1` — superseded by this checkpoint.
- Checkpoint commit HEAD: this status file is part of the checkpoint commit, so its resulting SHA cannot truthfully be embedded in itself; record that resulting SHA as the prior checkpoint HEAD in the next update.
- Roadmap position: **V3 Learning & Evaluation — Draft / NOT_PASSED / Pre-Paid-Compute closure**
- Canonical status path: `docs/PROJECT_STATUS.md`

## Current state / 現在の状況

V1 Local Core and V2 ARK Intelligence remain **OFFICIAL PASS** with frozen evidence unchanged. Local UI v1 and Launcher/Gate Runner evidence remain unchanged. V3 Contract 1 remains byte-for-byte frozen and PR #5 remains Draft/unmerged.

The previously staged V3 snapshot/git-state hardening is integrated on the actual PR branch. Its CI #143 / run ID `36220017532` completed **SUCCESS** across all six Windows/Linux Python 3.11/3.12/3.13 jobs.

This batch adds create-only Candidate-run evidence closure after an explicitly authorized full training run. It does **not** authorize or execute external compute, Candidate generation, Validation/V2 opening, promotion, Contract changes, or main merge.

## Work completed in this batch

### New work

- Added `src/ark/learning/run_manifest.py` to close a completed Candidate run with a deterministic, create-only `run-manifest.json`.
- The manifest inventories every already-created adapter/tokenizer/metrics/execution-snapshot file by SHA-256, byte length, relative path and symlink state.
- Manifest creation revalidates the full-training execution snapshot, requires saved `execution-snapshot.json` bytes to equal the authorized canonical snapshot, and requires `training-metrics.json` to bind to the same execution-snapshot and dataset identities.
- The run manifest explicitly records that this training run did not open Validation, historical V2, or promotion.
- Integrated final manifest generation into `HfLoRAFullRun.run()`; the runtime returns manifest path and SHA-256 only after create-only evidence closure.
- Added three focused tests covering deterministic inventory/hashability, saved-snapshot tamper rejection, and metrics/dataset cross-binding rejection.
- Updated `docs/v3/PRE_PAID_COMPUTE_GATE.md` to document Candidate-run evidence closure.

### Previously existing work

Dataset/provenance/contamination freeze tooling; human-review queue binding; strict execution-snapshot validation; separate preflight/full-training authorization scopes; local HF/tool/code identity hashing; authorization packets; runtime environment identity checks; clean exact-Git-checkout enforcement; non-Candidate preflight evidence; LoRA runtime plumbing; Validation-only comparison; Candidate/export lineage contracts; and paired Q4_K_M export planning were already present before this batch.

## Tests / CI / evidence

- Integrated hardening HEAD `767b17957ea4eb7561b5b0caa9e5ad6acc3aefd1`: CI #143 / run ID `36220017532`: **GREEN / 6 of 6 jobs SUCCESS**.
- New Candidate-run-manifest work HEAD `7569c210bbcabdba1a5077ba4c9bee4d9f1ac223`: CI #144 / run ID `36222828905`: **QUEUED at checkpoint time**. No GREEN claim is made yet for the new batch.
- New focused tests added: 3.
- V1/V2/Local UI/Launcher frozen evidence: unchanged.
- V3 Contract 1 semantics/hash: unchanged.
- Historical/frozen V2 final evaluation: unopened.
- No Candidate/adapters/weights were generated.

## Frozen contracts / evidence unchanged

- V1 Local Core freeze and evidence.
- V2 ARK Intelligence freeze, fixed 12-question suite/scorer/policy, and known `math-02` format-only failure.
- Local UI v1 and Launcher/Gate Runner reviewed evidence.
- V3 Contract 1 and its recorded hash.
- Frozen/protected V2 final evaluation contents and opening budget.

## Unresolved blockers / authorization boundaries

1. Immutable 40-hex Hugging Face revision for `Qwen/Qwen3-4B-Instruct-2507`, materialized base/tokenizer byte manifests, and chat-template probe hash remain unresolved.
2. The real experiment-001 120-train / 30-validation dataset still requires traceable provenance/rights, human approvals, contamination-review decisions and final frozen hashes.
3. Exact Linux/container plus Python/torch/transformers/PEFT/accelerate/CUDA identities remain unresolved.
4. Exact llama.cpp revision plus converter/quantizer byte identities remain unresolved.
5. Concrete GPU/device/VRAM/driver plus user-approved JPY ceiling, wall-clock ceiling, and provider-side billing/cost-cap evidence remain required before any external compute.
6. CI #144 must become GREEN before this new head can be treated as preflight-ready.
7. Hard stops remain: no paid/external compute; no real Candidate generation; no frozen V2 opening; no Candidate promotion; no frozen-Contract change; no main merge without explicit authorization.
8. V3 Contract 1 continues to exclude V4–V10 implementation scope from this V3 workstream unless that frozen boundary is explicitly changed.

## Next plan / 今後の方針

1. Follow CI #144 to completion; diagnose/fix ordinary code or lint failures without weakening any frozen gate.
2. Continue free V3 readiness hardening around Candidate evidence/reload/export closure, provenance/reproducibility and authorization evidence.
3. Prepare provider-neutral cost/billing evidence interfaces only where they can remain offline, reversible and non-authorizing; do not provision or purchase compute.
4. Continue closing remaining runtime/export identity gaps that require no fabricated external identities.
5. Re-read PR #5, latest HEAD and this canonical checkpoint before every later branch write; reconcile concurrent work and never force-push.

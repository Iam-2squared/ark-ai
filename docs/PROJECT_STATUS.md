# ARK AI Project Status

**LATEST**

Saved at: **2026-09-26 12:17:23 JST (+09:00)**

## Checkpoint identity

- Branch: `research/v3-learning-evaluation`
- Exact latest HEAD described before this checkpoint update: `953ca21d2b96f53a7e9f660419986517628eb052`
- Latest code work commit: `ffdaec70920cb0c1d35fe626841597474118ca62` — `harden(v3): revalidate preflight runtime evidence`
- Prior checkpoint commit: `953ca21d2b96f53a7e9f660419986517628eb052`
- Checkpoint commit HEAD: this status-only update is the commit containing this file; its resulting SHA will be recorded by the next checkpoint update.
- Draft PR: #5
- Roadmap position: **V3 Learning & Evaluation — Draft / NOT_PASSED / Pre-Paid-Compute boundary**
- Canonical checkpoint: `docs/PROJECT_STATUS.md`
- Prior canonical checkpoint: none. This is the first rolling LATEST checkpoint. Historical evidence remains append-only/frozen and is not superseded.

## Current state / 現在の状況

V1 Local Core and V2 ARK Intelligence remain **OFFICIAL PASS** with frozen evidence unchanged. Local UI v1 and Launcher/Gate Runner remain frozen on main. V3 Contract 1 remains frozen; PR #5 remains Draft/unmerged.

V3 already contains deterministic dataset/provenance/contamination tooling, human-review queue + decision binding, execution-snapshot validation, separate non-Candidate preflight/full-training authorization, local byte-identity tooling, a hash-addressed authorization packet, local-files-only HF/PEFT LoRA runtime plumbing, execution-core binding, candidate/export lineage, paired Q4_K_M export planning, and validation-only comparison.

No real Candidate/adapter weights, frozen V2 Candidate evaluation, promotion, paid/external compute, or main merge has occurred.

## Work completed in this batch

### New work

- CI state materially closed after the prior checkpoint: run #138 on `953ca21d2b96f53a7e9f660419986517628eb052` completed **GREEN**. This checkpoint records that state change; it does not claim additional code changes.

- Re-read the actual PR #5/branch state before writing; no stored SHA was reused as authority.
- Hardened `RuntimeIdentity` validation so measured runtime identity text cannot be silently coerced and measured/frozen GPU VRAM must be finite and positive.
- Hardened VRAM-tolerance validation to reject booleans, non-finite values, and negative tolerances.
- Hardened full-training replay of preflight evidence: non-standard JSON constants such as NaN/Infinity are rejected; the stored `PreflightEvidence` object is reconstructed and revalidated before it can authorize the Candidate run.
- Added regression tests covering malformed authorized preflight reports, non-finite/boolean numeric evidence, unexpected evidence fields, runtime identity coercion, and invalid VRAM values/tolerances.
- Updated the Pre-Paid-Compute Gate documentation to record the stricter replay boundary.

### Previously existing work

All dataset, authorization, identity, preflight, training, export-lineage, validation, registry, and frozen-policy simulation capabilities listed above existed before this batch and are not claimed as new.

## Tests / CI / evidence

- Previous head `8345710fbb47f2583f06995611d153207e938ca7`: CI run #136, run ID `34582010056`, **GREEN**.
- Code work head `ffdaec70920cb0c1d35fe626841597474118ca62`: CI run #137, run ID `36214072901`, superseded by the checkpoint-head CI.
- Prior checkpoint head `953ca21d2b96f53a7e9f660419986517628eb052`: CI run #138, run ID `36214130735`, **GREEN**.
- PR #5 remains Draft.
- V1/V2/Local UI/Launcher frozen evidence: unchanged.
- V3 Contract 1 semantics/hash: unchanged.
- Historical V2 suite/scorer/policy and the final V2 opening budget: unchanged and unopened by this batch.

## Unresolved blockers / authorization boundaries

The first external-compute preflight still requires real, non-fabricated inputs/evidence:

1. Immutable Hugging Face revision for `Qwen/Qwen3-4B-Instruct-2507`, materialized base/tokenizer hashes, and chat-template probe hash.
2. Actual human-approved 120 train / 30 validation dataset plus completed contamination-review decisions.
3. Exact Linux/container + Python/torch/transformers/PEFT/accelerate/CUDA runtime identities.
4. Exact llama.cpp commit plus converter/quantizer byte identities.
5. Concrete GPU/device/VRAM/driver proposal and explicit user-approved JPY ceiling + wall-clock timeout.
6. Provider-side billing/cost-cap evidence before any paid/external compute.
7. GREEN CI on the final preflight-authorizable head.

Hard stops remain: no paid/external compute, no real adapter/Candidate generation, no frozen V2 Candidate opening, no Candidate promotion, no frozen-Contract change, and no main merge without explicit authorization.

## Next plan / 今後の方針

1. Confirm CI on the latest checkpoint head; if ordinary plumbing fails, diagnose/fix without weakening gates.
2. Continue free V3 fail-closed readiness/evidence tooling, especially deterministic blocker reporting and human-review/artifact-identity preparation.
3. Close all non-human/non-payment execution-snapshot gaps that can be closed without fabricating identities.
4. When V3 is limited only by user/payment/hardware decisions, advance reversible V4–V10 foundations (interfaces, schemas, migrations/versioning, safety boundaries, tests) without declaring later milestones complete.
5. Before every future GitHub write, re-read this canonical checkpoint and latest branch HEAD; reconcile concurrent work and never force-push.

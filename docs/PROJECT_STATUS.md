# ARK AI Project Status

**LATEST**

Saved at: **2026-09-26 12:23:56 JST (+09:00)**

## Checkpoint identity

- Branch: `research/v3-learning-evaluation`
- Exact work basis HEAD: `51419e17bd4e9608fa65bca5fd6ea92a47b38f55`
- Latest code work commit: `51419e17bd4e9608fa65bca5fd6ea92a47b38f55` — `feat(v3): bind reserved VRAM preflight evidence`
- Prior checkpoint commit: `039f0ee4c8bfd3dfbd8f1fc493167ecacf5385b8` — superseded by this checkpoint.
- Checkpoint commit HEAD: this status-only update is the commit containing this file; its resulting SHA is recorded by the next checkpoint update.
- Draft PR: #5
- Roadmap position: **V3 Learning & Evaluation — Draft / NOT_PASSED / Pre-Paid-Compute boundary**
- Canonical checkpoint: `docs/PROJECT_STATUS.md`

## Current state / 現在の状況

V1 Local Core and V2 ARK Intelligence remain **OFFICIAL PASS** with frozen evidence unchanged. Local UI v1 and Launcher/Gate Runner remain frozen on main. V3 Contract 1 remains frozen; PR #5 remains Draft/unmerged.

V3 has deterministic dataset/provenance/contamination freeze tooling, human-review queue and decision binding, execution-snapshot validation, separate non-Candidate preflight/full-training authorization, local artifact identity hashing, a hash-addressed authorization packet, local-files-only HF/PEFT LoRA runtime plumbing, execution-core binding, candidate/export lineage, paired Q4_K_M export planning, and validation-only comparison.

No real Candidate/adapter weights, frozen V2 Candidate evaluation, promotion, paid/external compute, or main merge has occurred.

## Work completed in this batch

### New work

- Re-read actual PR #5 HEAD, canonical status, and CI before each branch write.
- Closed a preflight-evidence gap between the execution supplement and runtime: `PreflightEvidence` now requires **peak reserved VRAM** in addition to peak allocated VRAM.
- Non-Candidate preflight now records both `torch.cuda.max_memory_allocated()` and `torch.cuda.max_memory_reserved()`.
- Full-training metrics now retain both peak allocated and peak reserved CUDA memory.
- Added fail-closed tests for missing/non-finite/zero reserved-VRAM evidence and explicit report serialization coverage.
- Updated the Pre-Paid-Compute Gate to state the exact memory evidence recorded.
- Previous status head `039f0ee4c8bfd3dfbd8f1fc493167ecacf5385b8` completed CI run #140 successfully before this code batch.

### Previously existing work

The runtime-identity/preflight replay hardening from `ffdaec70920cb0c1d35fe626841597474118ca62` remains in place: non-standard JSON numeric constants are rejected, stored preflight evidence is reconstructed and revalidated, runtime identity strings are not silently coerced, and measured/frozen VRAM identities must be finite positive values.

## Tests / CI / evidence

- Prior latest checkpoint `039f0ee4c8bfd3dfbd8f1fc493167ecacf5385b8`: CI run #140, run ID `36214496459`, **GREEN**.
- New work head `51419e17bd4e9608fa65bca5fd6ea92a47b38f55`: CI run #141, run ID `36214677390`, **IN PROGRESS** at checkpoint time; no GREEN claim is made yet.
- PR #5 remains Draft/unmerged.
- V1/V2/Local UI/Launcher frozen evidence: unchanged.
- V3 Contract 1 semantics/hash: unchanged.
- Historical V2 suite/scorer/policy and the final V2 opening budget: unchanged and unopened.

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

1. Confirm CI on the latest checkpoint head; diagnose/fix ordinary plumbing failures without weakening gates.
2. Continue free V3 fail-closed readiness and evidence tooling around the remaining external/human inputs.
3. Close any remaining deterministic execution/preflight/export evidence gaps that require no fabricated identity, payment, hardware action, or Contract change.
4. When V3 is limited only by user/payment/hardware decisions, advance reversible V4–V10 foundations without declaring later milestones complete.
5. Before every future GitHub write, re-read latest HEAD and this canonical checkpoint; reconcile concurrent work and never force-push.

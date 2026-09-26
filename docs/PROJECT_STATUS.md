# ARK AI Project Status

**LATEST — STAGED**

Saved at: **2026-09-26 13:00:38 JST (+09:00)**

## Checkpoint identity

- Branch: `automation/v3-git-state-hardening-20260926-1300`
- Target branch: `research/v3-learning-evaluation`
- Target PR: #5 (Draft / unmerged)
- Target PR HEAD at save time: `ceae0919caf0b6a3b6cca4a5b4862e9235026663`
- Exact latest code HEAD described by this checkpoint: `5576a270349fba0494b8950ed1fa8a216bc8d2f2`
- Primary implementation commit: `cac3bd1ef011cf2e6b2edf1fb0d5bd7c345dca1c` — `feat(v3): bind runtime to clean frozen git checkout`
- Follow-up lint/test-format commit: `5576a270349fba0494b8950ed1fa8a216bc8d2f2`
- Previous staged checkpoint: `e566662c2d2ecb132143f62320d89d06cc0f47cf` — superseded by this staged checkpoint.
- Checkpoint commit HEAD: this status-only commit contains this file, so its resulting SHA cannot be embedded in itself; record that resulting SHA in the next checkpoint.
- Roadmap position: **V3 Learning & Evaluation — Draft / NOT_PASSED / Pre-Paid-Compute boundary**
- Canonical status path: `docs/PROJECT_STATUS.md`

## Current state / 現在の状況

V1 Local Core and V2 ARK Intelligence remain **OFFICIAL PASS** with frozen evidence unchanged. Local UI v1 and Launcher/Gate Runner evidence remains unchanged. V3 Contract 1 remains frozen and PR #5 remains Draft/unmerged.

The target V3 branch remains at `ceae0919caf0b6a3b6cca4a5b4862e9235026663`, whose CI #142 / run ID `36214712712` is GREEN. Existing-branch mutation is still unavailable from this automation runtime, so the new work is preserved on an isolated staging branch rather than overwriting PR #5.

No paid/external compute, real Candidate/adapter weights, frozen V2 Candidate evaluation, promotion, Contract change, or main merge occurred.

## Work completed in this batch

### New work

- Re-read PR #5, the target/staged checkpoint, and branch ancestry before each GitHub write; no force-push or target overwrite was attempted.
- Closed an execution-identity gap in the authorized runtime: `ark-v3-run` now verifies the **actual local Git checkout** instead of trusting only the operator-supplied `--code-sha`.
- Before any GPU/runtime import path, the runtime requires:
  - an existing non-symlink code root,
  - an exact lowercase 40-hex frozen `code.git_sha`,
  - `git rev-parse --verify HEAD` equal to the frozen SHA,
  - an empty `git status --porcelain=v1 --untracked-files=all`.
- Dirty tracked files and untracked files now fail closed before V3 compute.
- Retained the existing runtime source-manifest check, so Git commit identity and byte-level `code.manifest_sha256` evidence are both required.
- Added tests for clean/exact HEAD acceptance, HEAD mismatch rejection, and dirty/untracked checkout rejection.
- Updated `docs/v3/PRE_PAID_COMPUTE_GATE.md` to document the new repository-state evidence.
- Detected and corrected a top-level test-spacing/lint issue before publishing the staging branch.

### Previously existing work

The prior staged batch remains intact: experiment-001 frozen integer/boolean recipe fields reject Python/JSON type-coercion edge cases; dataset/provenance/contamination tooling, preflight evidence, runtime identity checks, authorization packets, local identity hashing, LoRA runtime plumbing, Candidate/export lineage, paired Q4_K_M planning, and Validation-only comparison were already present.

## Tests / CI / evidence

- Target PR #5 HEAD `ceae0919caf0b6a3b6cca4a5b4862e9235026663`: CI #142 / run ID `36214712712`: **GREEN**.
- New git-checkout hardening: three focused tests added. No GitHub Actions run exists for this new staging head yet, so **no GREEN claim is made for the new work**.
- V1/V2/Local UI/Launcher frozen evidence: unchanged.
- V3 Contract 1 semantics/hash: unchanged.
- Historical/frozen V2 final evaluation: unopened.
- No Candidate artifacts were generated.

## Unresolved blockers / authorization boundaries

1. The connector cannot fast-forward or directly mutate `research/v3-learning-evaluation` in this runtime, so staged work still requires a later safe integration path.
2. Immutable Hugging Face revision for `Qwen/Qwen3-4B-Instruct-2507`, materialized base/tokenizer hashes, and chat-template probe hash remain unresolved.
3. The real 120-train / 30-validation dataset still requires human-approved provenance and contamination-review decisions.
4. Exact Linux/container + Python/torch/transformers/PEFT/accelerate/CUDA identities remain unresolved.
5. Exact llama.cpp revision plus converter/quantizer byte identities remain unresolved.
6. Concrete GPU/device/VRAM/driver proposal plus user-approved JPY ceiling, wall-clock ceiling, and provider billing/cost-cap evidence remain required before external compute.
7. Final preflight-authorizable head must have GREEN CI.
8. Hard stops remain: no paid/external compute, no real Candidate generation, no frozen V2 opening, no Candidate promotion, no frozen-Contract change, and no main merge without explicit authorization.
9. Frozen Contract 1 continues to block automatic V4–V10 scope unless that contract boundary is explicitly changed.

## Next plan / 今後の方針

1. Publish this isolated staging checkpoint without changing PR #5.
2. Obtain a CI-bearing path for the staged work if the connector permits it; otherwise continue semantics-preserving V3 inspection and test/tooling preparation.
3. Diagnose and fix any ordinary CI/software failures without weakening frozen gates.
4. Continue free fail-closed V3 readiness work around execution identity, provenance, reproducibility, preflight/export evidence, and human-review preparation.
5. Re-check the latest PR #5 HEAD and canonical status before every later write; reconcile concurrent work and never force-push.

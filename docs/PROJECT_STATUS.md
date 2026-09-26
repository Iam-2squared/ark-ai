# ARK AI Project Status

**LATEST**

Saved at: **2026-09-26 15:18:59 JST (+09:00)**

## Checkpoint identity

- Branch: `research/v3-learning-evaluation`
- PR #5: **Draft / unmerged**
- Exact work basis HEAD: `a684755de8f761ce2df5d9abed9839ef6a123dd9`
- Primary new work: `a684755de8f761ce2df5d9abed9839ef6a123dd9` — `feat(v3): verify frozen Candidate run evidence`
- Earlier Candidate evidence commit: `7569c210bbcabdba1a5077ba4c9bee4d9f1ac223`
- Prior lint fix: `b1a6d8e0a664488bea076ee4c0a34145eaad30e0`
- Previous attached checkpoint: `fb1c94c8ea74251a6b82286c2cda7b74079aab07` — superseded.
- A previously prepared unattached status object is historical only and is not the branch LATEST.
- Resulting checkpoint commit cannot be embedded in itself; record it in the next checkpoint.
- Roadmap: **V3 Learning & Evaluation — Draft / NOT_PASSED / Pre-Paid-Compute closure**

## Current state / 現在の状況

V1/V2 remain OFFICIAL PASS. Local UI v1 and Launcher/Gate Runner evidence remain frozen. V3 Contract 1 remains frozen and PR #5 remains Draft/unmerged.

Candidate-run evidence now has both create-only freeze and later fail-closed re-verification. No external compute, Candidate generation, protected V2 opening, promotion, Contract change, or main merge occurred.

## Work completed in this batch

### New work

- Added `verify_candidate_run_manifest()` so a frozen Candidate run can be checked again before later export/evaluation.
- Verification requires canonical `run-manifest.json` and canonical training-metrics JSON; non-standard/non-canonical JSON is rejected.
- Optional expected manifest SHA-256 can be supplied and must be an exact lowercase 64-hex digest.
- The verifier revalidates the authorized full-training snapshot, saved execution snapshot, dataset binding, and recomputed file inventory.
- Any post-freeze adapter/tokenizer/metrics/snapshot byte change, symlink introduction, manifest mutation, or digest mismatch fails closed.
- Added focused tests for post-freeze file tampering, non-canonical manifest JSON, exact digest mismatch, and successful verification.
- Updated the Pre-Paid-Compute Gate documentation with downstream frozen-run verification semantics.

### Previously completed in this run

- Added create-only Candidate run manifest generation integrated into `HfLoRAFullRun.run()`.
- Diagnosed CI #144/#145 Ruff I001 and fixed only import ordering in `b1a6d8e0a664488bea076ee4c0a34145eaad30e0`.
- CI #146 / run `36222944733` on that fix head is **GREEN 6/6**.

## Tests / CI / evidence

- CI #143 / run `36220017532`: prior integrated hardening **GREEN 6/6**.
- CI #144 / run `36222828905`: pre-fix Ruff-only failure.
- CI #145 / run `36222912667`: same pre-fix Ruff-only failure.
- CI #146 / run `36222944733` on `b1a6d8e0a664488bea076ee4c0a34145eaad30e0`: **GREEN 6/6** across Windows/Linux Python 3.11/3.12/3.13.
- New verifier work HEAD `a684755de8f761ce2df5d9abed9839ef6a123dd9`: CI #148 / run `36223351050` is **QUEUED** at save time; no GREEN claim is made yet.
- Frozen V1/V2/Local UI/Launcher evidence unchanged; V3 Contract unchanged; protected V2 final evaluation unopened; no Candidate artifacts generated.

## Frozen contracts / evidence unchanged

V1 freeze; V2 fixed suite/scorer/policy and known `math-02` format-only failure; Local UI/Launcher evidence; V3 Contract 1/hash; protected V2 evaluation/opening budget.

## Unresolved blockers / authorization boundaries

1. Immutable HF revision, materialized base/tokenizer hashes, chat-template probe.
2. Human-approved/provenance-complete 120/30 dataset and contamination decisions.
3. Exact Linux/container + Python/torch/transformers/PEFT/accelerate/CUDA identities.
4. Exact llama.cpp revision and converter/quantizer identities.
5. GPU/device/VRAM/driver proposal plus approved JPY/time ceilings and billing/cost-cap evidence before external compute.
6. CI #148 must become GREEN before this latest verifier head can be treated as preflight-ready.
7. Hard stops remain: no external compute, Candidate generation, protected V2 opening, promotion, frozen-Contract change, or main merge without required explicit authorization.
8. Frozen V3 Contract excludes V4–V10 implementation scope from this V3 workstream.

## Next plan / 今後の方針

1. Follow CI #148; diagnose/fix ordinary failures without weakening gates.
2. Continue free Candidate reload/export and reproducibility closure.
3. Close remaining identity/export gaps requiring no fabricated external facts.
4. Keep provider/cost preparation offline and non-authorizing.
5. Re-read PR/head/status before every write; reconcile concurrent work and never force-push.

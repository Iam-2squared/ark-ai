# ARK AI Project Status

**LATEST**

Saved at: **2026-09-26 16:05:49 JST (+09:00)**

## Checkpoint identity

- Branch: `automation/v3-export-metric-hardening-20260926-1605`
- PR #5 target branch remains: `research/v3-learning-evaluation`
- Work basis HEAD: `d6d4c1954a85fc716b1c593ac55c85417912418f`
- This staging branch was created exactly from that HEAD after latest-state verification.
- Previous canonical checkpoint on the target branch: `d6d4c1954a85fc716b1c593ac55c85417912418f` — still authoritative for PR #5 until this staging work can be integrated.
- Resulting checkpoint commit SHA cannot be embedded in itself; record it in the next checkpoint update.
- Roadmap: **V3 Learning & Evaluation — Draft / NOT_PASSED / Pre-Paid-Compute closure**

## Current state / 現在の状況

V1/V2 remain OFFICIAL PASS. Local UI v1 and Launcher/Gate Runner evidence remain frozen. V3 Contract 1 remains frozen. PR #5 remains Draft/unmerged. A staging branch was created for the next V3 hardening batch because direct content writes to the target branch were rejected by the GitHub write safety layer. No frozen evidence or protected evaluation was changed.

## Work completed in this batch

### New work

- Re-read PR #5, the canonical checkpoint, latest branch HEAD and latest CI before attempting writes.
- Confirmed target checkpoint HEAD `d6d4c1954a85fc716b1c593ac55c85417912418f` has CI #151 / run `36223644908` GREEN.
- Designed a semantics-preserving Candidate evidence hardening batch: reject impossible allocated-vs-reserved VRAM geometry, reserved VRAM above frozen device capacity, and training wall time above the approved timeout.
- Designed paired-export path hardening: require disjoint non-symlink Current/Candidate source trees, keep export output outside both source trees, and reject canonical path aliases into the deployed Current model location.
- Prepared regression cases for those boundaries.
- Created staging branch `automation/v3-export-metric-hardening-20260926-1605` from the verified target HEAD.
- Direct source/test writes were attempted but rejected by the connector safety layer; no partial source mutation occurred.

## Tests / CI / evidence

- Target checkpoint HEAD `d6d4c1954a85fc716b1c593ac55c85417912418f`: CI #151 / run `36223644908` **GREEN**.
- No source-code change was successfully attached in this batch, so no new-code GREEN claim is made.
- Frozen V1/V2/Local UI/Launcher evidence unchanged.
- V3 Contract 1/hash unchanged.
- Protected V2 final evaluation remains unopened.
- No Candidate adapter/weights were generated.

## Frozen contracts / evidence unchanged

V1 freeze; V2 fixed suite/scorer/policy and known `math-02` format-only failure; Local UI/Launcher evidence; V3 Contract 1/hash; protected V2 evaluation/opening budget.

## Unresolved blockers / authorization boundaries

1. Immutable HF revision, materialized base/tokenizer hashes and chat-template probe.
2. Human-approved/provenance-complete 120/30 dataset and contamination decisions.
3. Exact Linux/container plus Python/torch/transformers/PEFT/accelerate/CUDA identities.
4. Exact llama.cpp revision and converter/quantizer identities.
5. GPU/device/VRAM/driver proposal plus approved JPY/time ceilings and billing-cap evidence before external compute.
6. GitHub content mutation is temporarily rejected by the connector safety layer for the prepared hardening batch; retry after re-reading latest state.
7. No external compute, Candidate generation, protected V2 opening, promotion, frozen-Contract change, or main merge without required explicit authorization.
8. Frozen V3 Contract excludes V4–V10 implementation scope from this V3 workstream.

## Next plan / 今後の方針

1. Re-read target and staging HEADs, then retry the prepared metric/export hardening without force-push or overwrite.
2. If target advances, reconcile from the new target before any write.
3. After a successful source batch, update this checkpoint in the same run and follow CI.
4. Continue free V3 reproducibility/export/lineage closure while hard authorization boundaries remain untouched.

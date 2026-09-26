# ARK AI Project Status

**LATEST — STAGED**

Saved at: **2026-09-26 12:42:34 JST (+09:00)**

## Checkpoint identity
- Branch: `automation/v3-snapshot-type-hardening-20260926`
- Target branch: `research/v3-learning-evaluation`
- Work basis HEAD: `ceae0919caf0b6a3b6cca4a5b4862e9235026663`
- Latest code work commit: `817fc6fa9797658fcf0090c2ea1ad630c9d495f7`
- Prior target checkpoint: `ceae0919caf0b6a3b6cca4a5b4862e9235026663`
- Checkpoint commit HEAD: the commit containing this file; record its resulting SHA at the next checkpoint.
- Roadmap position: **V3 Learning & Evaluation — Draft / NOT_PASSED / Pre-Paid-Compute boundary**
- Draft PR: #5
- Canonical status path: `docs/PROJECT_STATUS.md`

## Current state / 現在の状況
V1/V2 remain OFFICIAL PASS and frozen evidence is unchanged. Local UI/Launcher evidence is unchanged. V3 Contract 1 is unchanged and PR #5 remains Draft/unmerged. Target HEAD `ceae0919caf0b6a3b6cca4a5b4862e9235026663` has GREEN CI run #142 (ID `36214712712`).

## Work completed in this batch
### New work
- Tightened experiment-001 snapshot validation so frozen integer fields require exact integers.
- Rejected booleans in frozen numeric recipe fields and non-boolean values in frozen boolean recipe fields.
- Tightened dataset counts, full-Candidate-run count, and Validation/V2 run counts.
- Added regression tests for boolean/float values that Python equality could otherwise accept.
- Updated the Pre-Paid-Compute Gate documentation.
- Prepared code work at `817fc6fa9797658fcf0090c2ea1ad630c9d495f7`.

### Previously existing work
Dataset/provenance/contamination tooling, preflight evidence, runtime identity checks, authorization packets, local identity hashing, LoRA runtime plumbing, candidate/export lineage, paired Q4_K_M planning, and Validation-only comparison were already present.

## Tests / CI / evidence
- Target HEAD `ceae0919caf0b6a3b6cca4a5b4862e9235026663`: CI #142 / run ID `36214712712`: **GREEN**.
- Staged code work: tests added; no GREEN claim until a workflow completes for the staged branch.
- V1/V2/Local UI/Launcher evidence: unchanged.
- V3 Contract 1 semantics/hash: unchanged.
- Frozen V2 final evaluation: unopened.

## Unresolved blockers / authorization boundaries
- Existing-branch mutation is unavailable in this automation runtime, so the prepared code is staged separately and PR #5 is unchanged.
- External-compute blockers remain: immutable HF revision + materialized hashes/probe; approved 120/30 dataset + review decisions; exact runtime pins; exact llama.cpp identities; GPU/VRAM/driver proposal; user-approved JPY/time ceilings; provider billing/cost-cap evidence; final GREEN CI.
- Hard stops remain: no paid/external compute, real Candidate generation, frozen V2 opening, Candidate promotion, Contract change, or main merge.
- Frozen Contract 1 also blocks automatic V4–V10 scope.

## Next plan / 今後の方針
1. Publish and inspect CI for this staged checkpoint.
2. Fix ordinary CI/software issues without weakening gates.
3. Re-read PR #5 HEAD before any later integration.
4. Integrate only when an allowed target-branch write path is available; otherwise keep PR #5 untouched.
5. Continue free V3 readiness work that does not require protected data, payment, hardware action, or Contract changes.

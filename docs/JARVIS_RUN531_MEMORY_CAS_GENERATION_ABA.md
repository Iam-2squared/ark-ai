# Run531 — Memory v1 deterministic ID and CAS lifetime ambiguity (read-only)

**Draft PR #8 / \`research/jarvis-foundations\`**, no merge or frozen contract edits. **Package work-basis HEAD:** \`51903ef2a6c789b93a216f0ad60f1d47c4252cc1\`. Source \`a510a77ac15460448c2362153b227a5e9d6eedc4\`; source + focused regression fixtures \`77aa16d78e9dfe9b73fcf911fbbea86058ef4935\`.

## Problem — numerical CAS revision is not a lifetime ID

Frozen Memory v1 generates the same \`memory_id\` deterministically for the same owner/namespace/source. It also begins a newly created row at revision 1, including **after deletion of an earlier row with the identical ID**. That is valid frozen v1 behavior, but a stale writer which retained only \`memory_id + expected_revision=1\` can mistake the *new* generation for the old, even though ordinary single-row SQLite CAS remains atomic. Treating numeric revision as an authenticated generation token would be an ABA error.

## New isolated diagnostic

\`src/ark/memory/cas_generation_review.py\` adds \`review_memory_revision_reuse\`:

- Takes exact, bounded MemoryStore, MemoryScope, source_id and \`expected_revision\`; opens a read-only SQLite snapshot and validates the existing frozen v1 schema.
- Reconstructs **all** event operations for that deterministic memory ID, up to 40,000 events, including create/update/delete/expire and delete/recreate boundaries, matching event owner/namespace, sequential revision constraints and the current row's revision/create/update timestamps.
- Returns a content-free \`MemoryGenerationReview\` with event count, lifetime count, current revision, caller's expected revision, local history SHA-256, and \`revision_reuse_possible\` when **a re-created lifetime now has the same numerical revision**. Its three authority flags remain literal False.
- Never calls \`put\`, \`delete\`, \`purge_expired\`, ToolBackend or the live executor. The report is observational and does not solve stale-writer authorization, authenticate an owner, prevent a future race, sign an audit chain, or change frozen v1 CAS semantics.

\`tests/test_memory_cas_generation_aba_run531.py\` adds nine focused test functions, including parametrized invalid input/history cases. It exercises independent handles and recreated revision 1, revived revision 2, terminal/missing histories, forged event scope/revisions, scan caps, strict integer input, no event changes, and denied authority.

## Integration guidance

Planner/Memory integration should **not** accept a plain \`memory_id + revision\` as a durable handle across deletion/recreation. Future nonbreaking designs can carry a separately retained generation witness or treat ambiguous generations as manual recovery until a genuinely atomic cross-process generation token is proven. This read-only diagnostic is a prerequisite for investigating that design; it does not authorize a frozen schema change or an irreversible architecture decision.

## Verification and boundaries

- GitHub Actions source+test run [41313546787](https://github.com/Iam-2squared/ark-ai/actions/runs/41313546787) was **IN PROGRESS** when this evidence text was prepared. Final exact-head CI status will be recorded in canonical project checkpoint; never infer success on this new path from earlier heads.
- Nine test functions are **authored**, not independently run locally. Local DNS prevented a standalone checkout/pytest/Ruff. The committed focused tests and CI are the external verification route.
- Main, V1/V2/Local UI/Launcher contracts/evidence, protected final V2 scoring and PR #5 approval boundaries remain unchanged. No external GPU, paid service, real Candidate, user data, real Tool execution, irreversible operations, automatic retry, promotion or main merge. ARK/JARVIS remains **NOT_PASSED**.

**Next:** inspect exact-head CI, repair only real regressions; then test stale-plan recovery with a separately retained generation witness, keeping all write permissions and trusted-clock audit outside this diagnostic.

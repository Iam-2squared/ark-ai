# Run1197 — Durable Planner journal and path-custody rebase

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD at branch creation: `2df6b261554428cd01871f2723ce87c4dd05e4b4`.
- Reconciled source: Draft PR #18 exact child HEAD `780af1ab58a90ab69c749fd8130ea33f53fa4e84`.
- Original source base HEAD: `326001af654078227641546a8f30c6954fcea4a3`.
- New child branch: `research/run1197-planner-durable-journal-rebase`.

## Change

Adds an append-only local SQLite Planner journal as a separate module. Its genesis binds plan identity, canonical topology digest and initial status digest. Each event binds sequence, step identity, transition, expected revision, resulting full status digest, previous hash and event hash; a metadata frontier advances by sequence/hash compare-and-swap in the same transaction.

Transitions replay the durable prefix into a new PlanGraph, verify the supplied graph is current, apply one existing transition policy, and return a new graph plus receipt. The caller replaces its old graph with the returned graph. Stale state, invalid transitions, malformed schema, or a broken hash/replay prefix fail closed. A COMMIT acknowledgement exception is surfaced as an unknown outcome; callers must recover the durable frontier and must not blindly retry.

Recovery preserves RUNNING states and reports them as ambiguous. It never resets them to PENDING, automatically replays them, or treats them as completed. The journal stores no ToolCall arguments, tool results, timestamps or backend output, and has no execution/dispatch API.

The journal's repeated local path preflight rejects lexical traversal, symlink/hardlink aliases, non-regular database/sidecar paths and orphaned sidecars; creation is limited to serialized bootstrap, while ordinary operations require the existing database. This is repeated `lstat` preflight, not atomic directory-descriptor custody or a TOCTOU-proof guarantee.

## Regression coverage

The two synthetic test modules cover genesis and cold recovery, durable transitions, terminal descendant blocking, stale graph/sequence/revision rejection, schema and hash-prefix corruption, content minimization, concurrency/CAS, ambiguous RUNNING recovery, path traversal, symlinked ancestors/leaves/sidecars, hardlink aliases, orphaned sidecars, no-recreation after removal and valid relative paths. Symlink/hardlink cases skip only when the fixture filesystem cannot create the alias.

## Validation and limits

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. No real Tool call, backend dispatch, consent, trusted clock, automatic replay, paid/external compute, Candidate, protected V2 evaluation, credentials, physical hardware, destructive operation, frozen-contract change, UI/frontend work or main merge is involved.

PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.

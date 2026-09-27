# JARVIS Foundations

This branch carries isolated, reversible foundations for ARK AI beyond the frozen released baseline.

## Safety invariants

- V1/V2/Local UI/Launcher evidence remains untouched.
- V3 Contract semantics and protected evaluation remain untouched.
- No foundation may assume Candidate training success.
- Memory is local-first, scope-isolated, revision-guarded, and physically deletable.
- Tool writes require exact capability/scope authorization and one-shot request binding.
- Plans use deterministic DAG dependencies with revision-guarded state transitions.
- Action audit stores argument digests rather than raw arguments.
- Real action backends remain disconnected until durable authorization, fail-closed audit, and replay protection are integrated and tested.

## Planner integrity

- Plan topology and externally returned status views must be immutable snapshots.
- Transition state and revision inputs use exact-type validation so `StrEnum`/string equality and bool/int coercion cannot bypass state-machine checks.
- Dependency readiness and descendant blocking remain deterministic.

## Memory integrity

- Persisted rows are untrusted input: deterministic memory identity, content digest, metadata shape, timestamps, revision, and scope must be revalidated when read.
- Updates and deletes must validate the current persisted row before mutating it.
- Expiry purge must be compare-and-delete safe against concurrent updates.
- A database claiming the supported schema version must also match the expected table shape; version number alone is insufficient.
- Store clocks must fail closed on invalid values and must not silently move a record backwards in time.

## Durable action boundary

- Write-effect one-shot authorization consumption must survive process restarts.
- Durable authorization storage records a digest of the token identifier, never the plaintext token.
- Consumption is atomic and exactly-once under concurrent callers.
- Action execution obtains time from an injected trusted clock; callers cannot provide an arbitrary authorization time.
- Authorization is consumed before the action backend runs. A failed audit or backend call never makes that one-shot authorization reusable.
- A pre-action audit write is mandatory and fail-closed before any real write backend is invoked.
- Same-version action/audit databases must validate their schema shape before use.

## Personal-context boundary

- Personal-context retrieval is explicitly owner- and namespace-scoped and fails closed on cross-scope records.
- Expired or integrity-invalid memories are never surfaced as context.
- Multi-namespace retrieval uses deterministic budgeting rather than allowing one namespace to starve all others.
- Context provenance binds memory identity, revision, and content digest while avoiding plaintext in provenance digests.

## Integration rule

Foundation work is not a roadmap PASS and does not authorize promotion, external compute, protected evaluation opening, or main merge. It may advance independently while earlier hard gates remain pending.

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

## Integration rule

Foundation work is not a roadmap PASS and does not authorize promotion, external compute, protected evaluation opening, or main merge. It may advance independently while earlier hard gates remain pending.

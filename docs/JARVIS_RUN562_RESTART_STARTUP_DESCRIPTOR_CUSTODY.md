# Run562 — Restart and startup original-denial custody (disconnected)

Work basis: PR #8 `research/jarvis-foundations`, `79374c8d6f0e013908ca3a832ee229fe87e7d5c3` (prior checkpoint CI [41495191899](https://github.com/Iam-2squared/ark-ai/actions/runs/41495191899), completed SUCCESS).

## What was changed

1. [Restart source `0401a3a6`](https://github.com/Iam-2squared/ark-ai/commit/0401a3a62c7b2421949fce3c492a0bb27a0532be) binds original deny-only descriptors **at module import** for the final restart report and all three independently held local witness types (Memory, Context, due-slot). Before SQLite inspection and at every reentrant stable boundary, replacement descriptors are rejected even if they return the same literal `False`. Prior code pinned report properties only **after** all six store read callbacks, which let a late False-only replacement define the supposed baseline.
2. [Restart tests `1f8a7002`](https://github.com/Iam-2squared/ark-ai/commit/1f8a7002da41c70811ce7d9570dd14711320611d) add **12 authored parameterized cases**: seven original report denials, three original witness denials and two during-callback substitution attempts. These are authored tests, not an independent local pytest PASS claim.
3. [Startup source `2a36313c`](https://github.com/Iam-2squared/ark-ai/commit/2a36313c790638152c2eaee0124408424852de42) binds original deny-only properties for the SQLite schema seal, registered READ preflight and final startup report. Checks bracket the schema and READ callbacks and input/preview stabilization, not just their Boolean values. It does not change grant evaluation, frozen contracts, or a ToolRegistry entry.
4. [Startup tests `420d0eb6`](https://github.com/Iam-2squared/ark-ai/commit/420d0eb6eadb4509b6401923c996f8e1a963ff40) add **15 authored parameterized cases**: five schema properties, four preflight properties, four report properties and two mid-callback substitutions. The mock backend must remain uncalled.

## Test/evidence state at documentation creation

- PR #8 restart test commit: [CI 41503218559](https://github.com/Iam-2squared/ark-ai/actions/runs/41503218559) **IN PROGRESS** at last read.
- PR #8 startup test commit: [CI 41503374519](https://github.com/Iam-2squared/ark-ai/actions/runs/41503374519) **IN PROGRESS** at last read.
- The documentation commit and later canonical checkpoint require their **own** exact-head CI verification. No later PASS is inferred from earlier success.

## Security limits / explicit non-goals

The reads concern synthetic local SQLite witnesses, schemas and mock registered-READ preflights only. This prevents a particular process-local authority-descriptor substitution; it does **not** authenticate an actor, consent, retained custody or SQLite provenance, guarantee multi-store atomicity, establish a trusted clock, prove exactly-once effects, dispatch a real tool, notify anyone, or grant startup authority. A same-process attacker with general code execution can still bypass local Python checks; they are fail-closed fixture integrity guards, not a security sandbox. No paid service, GPU, model training, Candidate, protected V2 evaluation, main merge, or frozen evidence change.

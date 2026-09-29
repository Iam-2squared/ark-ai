# ARK AI Project Status

**LATEST**

Saved at: **2026-09-30 02:10:49 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / Draft PR #8

Work-basis HEAD: `c417ac9ca05e49798b0e499e433f94115fa941e9`

Checkpoint-result HEAD: this file cannot contain the SHA of the commit that writes itself; use the commit produced by this checkpoint update.

Supersedes the prior canonical checkpoint saved at 2026-09-29 23:15:39 JST.

## Current state

V1/V2/Local UI/Launcher evidence remains frozen and unchanged. V3 remains Draft/unmerged under its frozen Contract. JARVIS foundation work remains isolated/reversible and is not a roadmap PASS. PR #8 is open, Draft, mergeable, **84 commits ahead / 0 behind** `main` at the work-basis HEAD.

## New work this session

- Foundation Gap Matrix was reconciled with the actual hardened Planner source at `c417ac9ca05e49798b0e499e433f94115fa941e9`: immutable topology/status snapshots, exact `StepState`, exact non-bool revision validation, immutable transition rules, ordered dependency input, and sorted traversal are now recorded as implemented rather than open source gaps.
- The same matrix now records newly verified Memory gaps: exact persisted storage-class validation, Memory lifecycle-event validation, identity-aware writer lookup, negative schema-version rejection, lock-before-clock ordering, and revision/expiry-bound purge.
- Action Audit gap tracking now explicitly requires serialized bootstrap, exact row/schema validation, negative schema-version rejection, and write-lock acquisition before trusted clock sampling.
- Planner focused regression tests were prepared for unordered dependency input, raw-string state, bool/negative revision, immutable snapshots, and deterministic ready ordering, but the normal test-file write was rejected; no executable/test patch from that attempt was saved.
- PR #5 was re-read at exact head `d6d4c1954a85fc716b1c593ac55c85417912418f`. The preflight authorization packet generator is still not consumed by the runtime entry point, and training authorization remains represented by snapshot booleans plus preflight-report binding rather than a distinct reviewed post-preflight approval artifact with durable one-attempt consumption.

## Tests / CI / evidence

- Exact work-basis CI #230 / run `36603394483`: **SUCCESS, 6/6 GREEN** across Windows/Ubuntu and Python 3.11-3.13.
- Job IDs: Ubuntu 3.13 `109526169761`; Windows 3.12 `109526169899`; Windows 3.11 `109526169915`; Ubuntu 3.11 `109526169960`; Windows 3.13 `109526170029`; Ubuntu 3.12 `109526170193`.
- No Planner focused regression tests were added because the executable/test write path rejected the prepared patch.
- Prototype/source-ready findings are not repository implementation evidence until source/tests are saved and exact-head CI is GREEN.

## Frozen boundaries unchanged

Frozen V1/V2/Local UI/Launcher evidence, V3 Contract semantics, protected evaluation state, Candidate state, PR #5 Draft/unmerged state, and `main` remain unchanged. No external compute, Candidate generation, promotion, protected-evaluation opening, new credentials, destructive action, or main merge occurred.

## Blockers / authorization boundaries

Normal executable-source/test writes remain intermittently blocked by the tool safety path. A Gap Matrix documentation update was saved normally; the prepared Planner tests and later documentation hardening attempts were rejected. No safeguard-circumvention path was used.

PR #5 still requires explicit authorization before external compute or real Candidate work. Its free guard closure still requires runtime consumption of the exact reviewed preflight authorization artifact plus a separate post-preflight/full-training approval bound to the exact snapshot/core/preflight evidence and consumed durably once.

## Next plan / 今後の方針

1. Retry the prepared Planner focused tests only through the normal Contents path on a later invocation.
2. Implement Memory row/event storage-class validation, deterministic identity/content integrity, serialized writer ordering, trusted-clock rollback checks, and revision/expiry-bound purge.
3. Harden Action Audit v1 with serialized bootstrap, negative-version/schema validation, persisted request identity validation, and lock-before-clock monotonic append.
4. Land immutable ToolRegistry source/tests reproducing the frozen registry and bound-action vectors.
5. Add registry-bound durable one-shot authorization and execution occurrence, then mock-only audit-before-action execution.
6. Continue planner recovery, startup readiness, Personal Context, proactive scheduler, and fixture-only multimodal foundations.
7. Continue free-only PR #5 approval-binding guard closure without external compute or protected evaluation.

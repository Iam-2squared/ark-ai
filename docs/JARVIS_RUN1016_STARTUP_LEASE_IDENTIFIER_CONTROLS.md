# ARK AI Run1016 — startup readiness lease identifier controls

**Work basis:** Draft PR #8 exact head `aac9ae76df364fe0b8230e36933bf1f0404e0add`. This is an isolated non-UI child; PR #8 and main are unchanged.

## Change

The disconnected `SyntheticReadinessRequirement` already bounded exact UTF-8 identifiers and rejected NUL, but it still admitted embedded ASCII controls and Unicode formatting controls. That differed from the existing `StartupComponent` identity admission and could make diagnostic labels visually misleading.

The requirement now rejects:

- ASCII C0 controls and DEL;
- C1 controls;
- bidi and Unicode formatting controls, including zero-width and line-separator characters.

Validation runs before a readiness snapshot is read or component matching occurs. Ordinary UTF-8 identifiers remain accepted. No startup, dispatch, notification, hardware, or external-effect authority is added.

## Regression coverage

The synthetic test covers both `component_id` and `schema_revision` with newline, tab, DEL, bidi, zero-width, line-separator and soft-hyphen inputs, plus a valid Japanese identifier.

## Prior evidence and current validation

Earlier isolated PR #56 exact head `8bade104459330439443e256bebea3eab429d3e7` passed exact-head CI run [#44685093660](https://github.com/Iam-2squared/ark-ai/actions/runs/44685093660) GREEN 6/6. That evidence applies only to the earlier base/head. This port on the current PR #8 work basis requires its own exact-head CI.

## Limits and safety

Synthetic local readiness only. A readiness lease remains diagnostic; it never authorizes startup, tool dispatch, notification, hardware, or external effects. No frozen contract, UI, paid service, external compute, credentials, Candidate, protected V2 evaluation, PR #5, PR #9, or main branch is changed.

**Current status:** exact-head CI pending; no PASS claimed. ARK/JARVIS remains NOT_PASSED.

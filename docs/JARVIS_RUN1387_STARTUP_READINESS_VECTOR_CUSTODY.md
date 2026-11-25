# Run1387 — Startup readiness constructor vector custody

Status: isolated source hardening and synthetic regression for Draft PR #8. No roadmap PASS is claimed.

## Finding

The startup readiness evaluator checks original field descriptors and lookup hooks for three frozen carrier classes. Its type, field-name, hook-name, descriptor and hook vectors were module-level mutable tuples. Replacing those vectors together with empty tuples could make the strict zip comparisons vacuous and allow a substituted carrier descriptor to survive the initial authority check.

## Change

The private constructor verifier now retains all five import-time vector objects in keyword-only function defaults, verifies each mutable module binding against the captured tuple, and performs the existing descriptor/hook checks using the captured vectors. The public readiness types and evaluator API remain unchanged.

## Regression coverage

The test jointly replaces the carrier type/field/hook/descriptor vectors, installs a hostile `StartupComponent.component_id` property, and supplies a probe generator with an observable first iteration. The verifier must fail before either the descriptor or generator executes.

## Evidence limits

Synthetic disconnected readiness probes only. This is in-process mutation hardening, not process isolation, trusted time, authenticated identity, startup authorization, dispatch, notification, hardware readiness, or external-effect safety. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.

No live service, credential, device, model, GPU, paid/external compute, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, main merge or UI/frontend work occurred. PR #8 remains Draft/unmerged.

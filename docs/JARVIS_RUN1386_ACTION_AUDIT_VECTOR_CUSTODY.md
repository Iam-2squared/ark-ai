# Run1386 — ActionAudit event validator vector custody

Status: isolated source hardening and synthetic regression for Draft PR #8. No roadmap PASS is claimed.

## Finding

ActionAudit checks its frozen receipt dataclass by iterating module-level field-name, descriptor, and hook tuples. The working tuples and their purported original comparison tuples are mutable module bindings. Replacing both members of each pair with empty tuples makes the strict zip checks vacuous and can let the audit path proceed without detecting a substituted event descriptor.

## Change

The private event-constructor verifier now retains all four import-time tuple objects in keyword-only function defaults. It checks that each mutable module binding still refers to its captured tuple before comparing the original class descriptors and hooks. The existing optional phase argument and public ActionAudit API remain unchanged.

## Regression coverage

For both append and read paths, simultaneously replace the field/descriptor/hook vectors and install a hostile event field descriptor. The verifier must reject before either the descriptor or SQLite connection callback is reached.

## Evidence limits

Synthetic local SQLite only. ActionAudit v1 DDL, event fields, append ordering, chronology and audit-before-action semantics are unchanged. This is an in-process mutation regression, not authenticated writer identity, trusted time, human consent, power-loss durability, exactly-once external effects, or action authority. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.

No live data, backend dispatch, notification, hardware, credentials, paid/external compute, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, main merge or UI/frontend work occurred. PR #8 remains Draft/unmerged.

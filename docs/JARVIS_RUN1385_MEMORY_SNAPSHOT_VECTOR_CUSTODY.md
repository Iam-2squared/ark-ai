# Run1385 — Memory coherent-snapshot validator vector custody

Status: isolated synthetic regression and narrow source hardening for Draft PR #8. No roadmap PASS is claimed.

## Finding

The coherent-snapshot request/result validators iterate module-level tuples containing field names, descriptors and lookup-hook names. The tuples and their comparison vectors were themselves mutable module bindings. Replacing both a working vector and its purported original with empty tuples could make the `zip(..., strict=True)` checks vacuous. A substituted request slot descriptor or result `__new__` hook could then execute before the validator rejected it.

## Change

The private validator functions now retain the import-time tuple objects in keyword-only function defaults. Before reading any request field or constructing a snapshot result, they verify that every module-level working/original vector is still the exact captured tuple. The existing field, descriptor and hook comparisons then run against the captured tuples.

The public request/result types, function signatures, Memory v1 DDL, schema, retention, query semantics, digest format and coherent transaction behavior are unchanged.

## Regression coverage

- Joint replacement of request field-name, descriptor, hook-name and hook vectors must be rejected before a substituted request field descriptor is accessed.
- Joint replacement of result field-name, descriptor, hook-name and hook vectors must be rejected before a substituted result field descriptor executes.

Synthetic local SQLite only. The tests do not use live personal data, external context sources, tool dispatch, notification, hardware, paid services or external compute.

## Evidence limits

This is a narrow in-process mutation regression. It is not a Python sandbox, process-isolation guarantee, authenticated provenance, trusted-time proof, consent/erasure proof, power-loss durability proof, or action authority. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required before any validation claim. PR #8 remains Draft/unmerged; no main merge or frozen-contract change is part of this package.

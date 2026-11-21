# ARK V3 — Run525: original validator pinned at detached comparison boundary

## Scope and evidence

- Source: `src/ark/learning/validation.py`, updated on commit `0d12d85397348b3bd61f6fa9717be623c771569e`.
- New tests: `tests/v3/test_validation_method_bypass_run525.py`, saved at commit `50989bcd27eef131a658d0727317bf02a982a41e`.
- Eight new pytest parameterizations/tests: seven invalid-input permutations plus a stable, non-authorizing baseline.

A caller can replace the public `ValidationReport.validate` class method in a synthetic Python fixture, causing `report.validate()` to return without checking the 30-case bounded V3 input. `compare_validation` now retains the original exact-type validation function and invokes it for **each** report immediately after its public callback boundary. Explicit source-epoch checks before and after both calls preserve the existing behavior for reentrant mutation tests.

The added negative fixtures cover non-bool passing/failure flags, duplicate IDs, blank case categories, invalid SHA-256 identity, blank model identity and oversized identity values even if the public method has been replaced with a no-op.

## Non-authorization and CI boundary

This is validation-only local logic. It does not instantiate a Candidate, train adapters, perform full V3 evaluation, inspect protected V2 results, authorize preflight, access a GPU, or promote a model. The historical V2 and frozen V3 contracts remain unchanged. Existing method callbacks are still exercised, but they cannot be the only validator.

New case count is **authored test count**, not a local or CI PASS claim. Exact source/test-head CI must be read separately. Human dataset approval, immutable HF revision and byte manifests, reproducible runtime identities and explicit paid-compute authorization remain unresolved blockers.

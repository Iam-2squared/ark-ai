# Run1184 — Complete Unicode format-control admission for Memory generation CAS

## Exact basis

- Parent branch: `research/jarvis-foundations` (Draft PR #8).
- Exact parent work-basis HEAD at child creation: `844e68078a6a9c2172b84a40ed828d02b3fc161a`.
- Child branch: `research/run1184-memory-generation-unicode-controls`.
- Exact child HEAD before this report: `61780d81a1355b99600d645e5d4f2f0401bfe5df`.

## Finding

The opt-in `generation_fenced_cas` path bounded Memory owner/namespace/source identities and rejected a manually enumerated set of C0/C1, bidi, separator and default-ignorable scalars. It did not reject every Unicode General Category `Cf` character. U+0600, U+FFF9 and U+E0001 could therefore pass the optional generation identity gate.

This change is deliberately limited to the opt-in generation-CAS API. The frozen MemoryScope/MemoryWrite constructors, Memory v1 schema, and ordinary Memory v1 read/write semantics are not tightened.

## Change

- Pin the import-original `unicodedata` module and `category` function in the generation-CAS module.
- Add one shared identity-control predicate that rejects all `Cf` characters while preserving the existing explicit C0/C1, bidi, line-separator and default-ignorable checks.
- Check Unicode dependency identity before inspecting source/scope text and recheck after scanning.
- Keep source/scope byte budgets, UTF-8 validation, generation tokens, CAS transaction ordering and no-retry-on-ambiguous-commit behavior unchanged.
- Both observation and update entrypoints already call these validators before opening the private SQLite connection; this change does not add any new database operation.

## Regression coverage

The synthetic test module has 12 cases:

- 3 source-ID cases for U+0600, U+FFF9 and U+E0001.
- 6 scope cases across owner ID and namespace for the same controls.
- 1 positive Japanese owner/namespace/source case.
- 2 Unicode module/classifier substitution cases that verify denial before the replacement callback receives private identity text.

## Validation boundary

No local pytest/Ruff result is claimed. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required on the final child HEAD. No previous CI result transfers.

This is an in-process dependency-integrity guard and local identifier validation, not a Python sandbox, authenticated writer provenance, independent custody, trusted time, consent, physical erasure or cross-store atomicity. The token remains non-authorizing.

No paid/external compute, paid API/service, Candidate generation/promotion, protected V2 evaluation, credentials, physical hardware action, destructive operation, frozen-contract change, UI/frontend work or main merge is involved. PR #5 remains gated Draft/unmerged; PR #8 remains Draft/unmerged; PR #9 remains paused and untouched. **ARK/JARVIS remains NOT_PASSED.**

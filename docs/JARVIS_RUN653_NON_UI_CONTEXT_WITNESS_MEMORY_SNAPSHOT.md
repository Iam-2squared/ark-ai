# ARK AI — Run653 non-UI Personal Context witness custody and Memory WAL audit

## Exact basis and safety scope

- Initial source/test work-basis: `b6ba8c8ece0dcad4a9a5dc7c17b22a35930ff569` (Run652 canonical checkpoint, whose GitHub CI #42165085750 subsequently finished six of six GREEN).
- All changes made through ordinary GitHub Contents API commits on `research/jarvis-foundations`, Draft PR #8:
  - `1daf3ec6f0834549ffa1d321fa9b0398ddd5a48a` — strengthen `src/ark/personal_context_replay_ledger.py`.
  - `f8ed4872c891a81f030dd11d3e35e2aa33e9327c` — three cross-connection Memory WAL snapshot regression cases.
  - `715975139b0add66d098467be42677ca84fcfad3` — twelve Personal Context retained-witness regression cases.
- This is disconnected synthetic metadata, not retained user context text. No personal data, actual tool actions, billing, external GPU, notification, model training, Candidate, protected evaluation or frontend changes. PR #5/#9 remain outside this branch and are not merged.

## Package A — exact-class Personal Context replay witness carrier

**Gap addressed:** the previous offline replay witness checker pinned only the `independent_custody_proven` False property. A frozen/slotted dataclass's own `count` or `chain_sha256` field descriptor, `__init__`, `__new__`, or `__getattribute__` could be reflectively replaced; a retained witness read then invoked attacker-controlled Python code before rejecting it. An exact `type(witness)` check is insufficient for that.

**Change:** retain the import-original field descriptors and constructor/lookup hooks, reject replacement *before* checking values, and revalidate originals and identical value carriers after the denial getter. Check the import-original carrier before synthetic genesis construction and before replay journal row inspection. Preserve the existing v1 SQLite schema, replay-denial semantics and no-authentication properties. This remains process-local defense-in-depth; it is not a Python sandbox.

**Regression:** 5 parameterized field/getter/constructor cases against direct witness inspection and 5 against genesis plus SQLite row inspection; an inherited `__new__` poisoning case runs only in a child Python interpreter to prevent CPython `tp_new` contamination of later tests; one unchanged-genesis/read-only-prefix case verifies legitimate behavior. **12 test cases authored, not a claim of 12 measured PASS.** No unsafe `__new__` reassignment in the persistent pytest interpreter.

## Package B — coherent Memory SQLite audit under committed interleaving

**Gap tested:** a Memory row/event reconciliation must not combine an old live-row scan with a new global event tail if a *second* WAL writer commits between the two scans. The audit is a diagnostic digest, not attribution, consent or secure-erasure evidence.

**Regression:** 3 parameterized transitions — a second owner's CREATE, same-key UPDATE, and DELETE plus CREATE of the same deterministic key — are committed through a separate `SQLiteMemoryStore` handle during the first record hydration. The in-progress read-only audit must exactly equal the pre-write report, and a subsequent audit must reflect the newly committed row/event generations and different digest. No schema/frozen source change, no writer lock acquired by the audit. **3 cases authored; CI result required before declaring PASS.**

A small local SQLite WAL experiment separately reproduced old-reader/new-writer snapshot semantics; it is **not** a repository pytest or CI success claim.

## CI and known limits

- Previous Run652 exact-head [#42165085750](https://github.com/Iam-2squared/ark-ai/actions/runs/42165085750) observed **6/6 GREEN** before this invocation.
- Personal Context source [#42170183665](https://github.com/Iam-2squared/ark-ai/actions/runs/42170183665): **IN_PROGRESS**, conclusion NOT FINAL at report drafting.
- Memory regression [#42170416676](https://github.com/Iam-2squared/ark-ai/actions/runs/42170416676): **IN_PROGRESS**, conclusion NOT FINAL at report drafting.
- Context regression [#42170569112](https://github.com/Iam-2squared/ark-ai/actions/runs/42170569112): **IN_PROGRESS**, conclusion NOT FINAL at report drafting.
- Full local `pytest` and Ruff on the actual repository source are not claimed; local public clone could not resolve `github.com`. Normal public-repository GitHub Actions use the existing 6-job CI, no manual rerun or new workflow.
- The new tests do not prove real consent, human review, trusted clock, historical writer identity, data deletion, external execution or automatic replay safety.

## Prioritized next work

1. Review the *exact-head* six CI jobs and actual failures. Fix test-only mistakes without weakening source safety invariants; do not count authored tests as passed tests.
2. After complete lower-level source CI GREEN, bind `personal_context_replay_recovery._witness_fields` to original, early-checked witness descriptors before any retained field access or local SQLite history callback. Include reentrant constructor/field injection and non-authorizing restart tests.
3. Preserve Memory event ID high-water and retained-prefix proof limitations; further verify ambiguous post-COMMIT same-writer attribution under real SQLite races before any replay semantics.
4. Progress Planner crash recovery and immutable registry, exact-type permission, audit-before-action and durable synthetic occurrence integration only where dependency evidence is GREEN. Keep all UI paused and PR #5/#8/#9 Draft/unmerged.

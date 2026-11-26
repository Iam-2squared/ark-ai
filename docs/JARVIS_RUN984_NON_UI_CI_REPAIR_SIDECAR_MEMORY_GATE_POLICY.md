# ARK AI Run984 — Non-UI CI repair, SQLite sidecar carrier custody, Memory COMMIT-UNKNOWN classifications, PermissionGate vectors

**Work basis:** Run983 checkpoint HEAD `5cad8a1c39e9eb1eb7d7b0936d13b1e8c8c3666e`. **Latest executable source/test HEAD:** `710232d64c65d9e33c831e0266c6eec683a4c2c5`. Draft PR #8, isolated from main and Draft PR #5/#9. **Overall ARK/JARVIS: NOT_PASSED.**

## Evidence-driven CI repair and three independent core packages

1. **Run983 CI repair.** [`3530feee`](https://github.com/Iam-2squared/ark-ai/commit/3530feee914db6404d10bc00107629b17fb68cc9): Run983 exact checkpoint [CI #44454337365](https://github.com/Iam-2squared/ark-ai/actions/runs/44454337365) failed all six platforms at Ruff I001 in `tests/test_privacy_revocation_path_alias_run542.py`. Removed only an extraneous import-group blank line. No production denial relaxed or test deleted. Recovery CI [#44460267316](https://github.com/Iam-2squared/ark-ai/actions/runs/44460267316) started.
2. **Detached SQLite sidecar inventories.** [Source `732f290f`](https://github.com/Iam-2squared/ark-ai/commit/732f290f875663786e849cc75424a11d9de9c393), [tests `28543df6`](https://github.com/Iam-2squared/ark-ai/commit/28543df6c081e3f4ef67b705b2fff6203f91ff9e): import-epoch identity checks pin all six field/constructor/denial inventories prior to any descriptor-relative main/-wal/-shm/-journal access. **20 newly authored synthetic cases**: 6 vectors × 3 mutations + forged consent descriptor and inert positive seal. No SQLite rows are read. This is not atomic future pathname custody or proof of transaction coherence.
3. **Memory post-COMMIT ambiguity.** [Source `eb88f8f7`](https://github.com/Iam-2squared/ark-ai/commit/eb88f8f76d59992dc48fec660baf75edc039e469), [tests `b4d45d57`](https://github.com/Iam-2squared/ark-ai/commit/b4d45d57c72d946f17f5505464d2a7ee92a9598b): pin the exact three disposition mappings, hex digest matcher and 16 field/denial inventories before access to caller-private Memory evidence. Reject altered classifications, missing checks or equal-valued vector replacements. **37 authored cases** (32 field-vector variations + 4 mapping cases + 1 normal manual-only case). No COMMIT attribution or automatic retry permission.
4. **Registry-bound PermissionGate.** [Source `647b2bdd`](https://github.com/Iam-2squared/ark-ai/commit/647b2bddfbffc783ca2e2ad7c87530fcc4faa6be), [tests `710232d6`](https://github.com/Iam-2squared/ark-ai/commit/710232d64c65d9e33c831e0266c6eec683a4c2c5): bind grant, ToolSpec, one-shot token field/method/hook name/descriptor arrays to their original import identity. Prevent truncation/rebinding from omitting a malicious class getter before registry/grant admission. **34 authored cases** (32 mutation variants + inert READ and denied unauthenticated WRITE). The local gate does **not** provide restart-safe approval, trusted time, consent or real backend dispatch.

**New test cases authored: 91**, plus Ruff repair. Full suite and remote exact-head CI are **not certified GREEN**. No new frozen contract, paid service, external tool, physical-PC operation, Candidate generation, protected V2 evaluation, main merge or UI work.

## CI checkpoints (observed while producing this report)

- **Run983 checkpoint `5cad8a1c`: CI #44454337365 FAIL all 6** on Ruff import grouping, before tests.
- Import repair `3530feee`: [#44460267316](https://github.com/Iam-2squared/ark-ai/actions/runs/44460267316) **IN PROGRESS**.
- SQLite sidecar test `28543df6`: [#44460523211](https://github.com/Iam-2squared/ark-ai/actions/runs/44460523211) **IN PROGRESS**.
- Memory ambiguity test `b4d45d57`: [#44460742329](https://github.com/Iam-2squared/ark-ai/actions/runs/44460742329) **QUEUED**.
- PermissionGate test `710232d6`: [#44461000423](https://github.com/Iam-2squared/ark-ai/actions/runs/44461000423) **QUEUED**.
- Previous older Run982 checkpoint `1236de889f62659d7009a34c2b125acf2c99452b`: [#44447458824](https://github.com/Iam-2squared/ark-ai/actions/runs/44447458824) **GREEN 6/6**; not evidence for the new commits.

All ordinary GitHub Contents API, no forced or raw-object writes, no duplicate workflow dispatch. CI can overlap but the latest exact source/test, technical-report, and status HEAD must still be reviewed independently. Unreviewed code/test correctness remains provisional.

## Next priorities

1. Inspect first CI FAIL on newest exact HEAD, repair only confirmed defects; preserve denial semantics and frozen tests.
2. Memory WAL/SHM alias and held-file races, CAS generation ABA, expiry/event coherent snapshots; continue manual-only COMMIT-UNKNOWN isolation.
3. Planner persistence/restart, immutable registry + exact permission, durable one-shot authorization and trusted-clock pre-action audit; mock-only integration after lower-level exact-head GREEN.
4. Privacy-safe Personal Context revocation/retention, proactive occurrence deduplication, observation fixtures and free V3 identity/reproducibility guards.

**Hard boundaries unchanged:** Draft PR #5 not merged or authorized for paid training; Draft PR #9 UI paused; no real ToolBackend action, Candidate promotion, automatic ambiguous replay, external GPU/paid services, protected final evaluation, credential provisioning or destructive action.

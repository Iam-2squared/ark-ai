# ARK AI Run926 — disconnected non-UI security and CI recovery

Work basis: `2d703564e6a4f2c09e3d1cc2ab8766a814f62f40` (Run925 checkpoint).
Complete source+test HEAD before this report: `be447bf6f26478acf7c7945651d3a76988215c62`.
Draft PR #8 remains the isolated `research/jarvis-foundations` lane; no main or UI change.

## 1. Repair Run925 exact-HEAD CI regressions (privacy and due-restart)

Run925 CI #43945718308 failed on all six Python/OS jobs. Ubuntu Python 3.11 logged **8 failed, 16,673 passed, 1 skipped**. These are not Run926 PASS evidence.

- [privacy source `d7a2c68`](https://github.com/Iam-2squared/ark-ai/commit/d7a2c68f95ee434eceb046c9ea34896ef5cff74b): preflight frozen `MemoryScope` class descriptors/validator before first private scope getter in `revoke` and `assert_not_revoked`, and before reentrant epoch reads. Reject altered descriptors without a veto insert. Do not change frozen MemoryScope definition.
- [due observation test `5f3904e`](https://github.com/Iam-2squared/ark-ai/commit/5f3904e322784917d9342f2deaef93f0b4575f46): assert earlier fail-closed restart digest identity denial, not a now-unreachable later prefix rejection.
- [due late mutation test `57f1262`](https://github.com/Iam-2squared/ark-ai/commit/57f12628a0277824f878d5eb84710a470c0d9766): keep witness unchanged/no callback execution and assert earlier `DisconnectedDueRecoveryRejected`, not the later due-ledger error.

Recovery CI [#43953657924](https://github.com/Iam-2squared/ark-ai/actions/runs/43953657924) at last inspection: Ubuntu 3/3 GREEN, Windows 3.12 GREEN, Windows 3.11/3.13 still IN PROGRESS. Not full exact-head matrix PASS.

## 2. Memory v1 SQLite row/event prehydration — five new synthetic regressions

- [source `2d6df52`](https://github.com/Iam-2squared/ark-ai/commit/2d6df52a689c25bd0202681e7e4aa10a211bd9fc)
- [test `b4cad8b`](https://github.com/Iam-2squared/ark-ai/commit/b4cad8bf0a7875b0b6956d1f4dcd950edc9862d6)

The read-only global event alignment auditor now performs SQL-side count and byte/type preflight for live rows and events under the same `BEGIN` snapshot, **before** untrusted SQLite TEXT is hydrated by either full-table row iterator. Existing codepoint validation, v1 schema, CAS, event order, tail marker and denial-only flags remain authoritative and unchanged. Four tampered disposable SQLite fixtures and one normal two-scope restart comparison were authored. Hash consistency still does not authenticate a historical writer, grant consent, or prove erasure.

[CI #43954423571](https://github.com/Iam-2squared/ark-ai/actions/runs/43954423571): at last inspection Ubuntu 3/3 GREEN, Windows pending; exact-head six-matrix not certified.

## 3. WAL/SHM independent disposable probe admission — six new synthetic regressions

- [source `beb2f72`](https://github.com/Iam-2squared/ark-ai/commit/beb2f722b1e421bbf1f9adecc61e82fb8ba6b8bc)
- [tests `82af4c4`](https://github.com/Iam-2squared/ark-ai/commit/82af4c4ef42e9882c4925ff2645482fbb2510088)

Require exact bounded iteration text before `int()`, exact boolean `keeper` before temporary database/process creation. Six malformed input cases prove denial without starting a subprocess or creating a disposable database. Existing normal single-/multi-client last-close evidence remains diagnostic only. Real SQLite WAL/SHM alias/process race remains unresolved.

[CI #43955057493](https://github.com/Iam-2squared/ark-ai/actions/runs/43955057493): latest inspected IN PROGRESS/QUEUED; no six-matrix PASS claimed.

## 4. Startup readiness grant pregetter — five new synthetic regressions

- [source `61d3535`](https://github.com/Iam-2squared/ark-ai/commit/61d353592e6c0bdfa0c54681bd5875390ddffdc6)
- [tests `be447bf`](https://github.com/Iam-2squared/ark-ai/commit/be447bf6f26478acf7c7945651d3a76988215c62)

In read-only local startup diagnostic, pin exact `CapabilityGrant` dataclass descriptors and lookup hooks in `_require_original_denials` before gathering private capability, scope or expiry values. Refuse in-process descriptor mutation before schema/registered-READ review, and never call a backend. Five replacement field/method scenarios authored. Startup signals remain non-authorizing: no trusted clock, external action, consent or atomic cross-store proof.

[CI #43956581585](https://github.com/Iam-2squared/ark-ai/actions/runs/43956581585): QUEUED at first inspection. New tests **authored**, not yet certified on exact HEAD.

## Preservation and next gates

**16 new synthetic regression cases authored** (Memory 5, WAL 6, Startup 5), plus Run925 CI compatibility repairs (existing tests). No full local pytest on this run; rely on exact GitHub CI evidence, which remains pending for complete new HEAD.

Frozen V1/V2/Local UI/Launcher and Observation v1 semantics unchanged. PR #5 and PR #9 remain Draft/unmerged/untouched. PR #8 Draft/unmerged. No UI/frontend development; no external GPU, paid APIs, subscriptions, Candidate weights/adapters, protected V2 evaluation, human-review fabrication, automatic Candidate promotion, physical PC/user databases, irreversible action, real ToolBackend effects, secrets, main merge, force push or hidden Git routes.

Blockers: final full exact-head six-job CI; actual WAL/SHM interprocess alias race; independent trusted audit clock and durable one-shot WRITE approval; Planner COMMIT-UNKNOWN manual recovery; Memory CAS/coherent expiry and independent history proof; protected V2/V3 and user-PC gates.

Priority: first resolve any new CI regressions without weakening semantics; next disposable WAL/SHM races, coherent Memory/Planner recovery, separate immutable registry/authorization/audit proof, offline-only mock integration, privacy safe Personal Context and V3 free guards. JARVIS overall **NOT_PASSED**.

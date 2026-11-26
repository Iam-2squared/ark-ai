# ARK JARVIS foundations — Run410 bounded ingress and receipt custody

> **Disconnected / synthetic only — no JARVIS PASS, trusted time, authenticated
> consent, real WRITE, network/backend dispatch or external side-effect receipt.**
> These source/test changes live only on Draft PR #8, not on main.

## Exact work basis and package commits

- Starting verified prior checkpoint: `3474d5326a42044c5bd00886f35f84f8785a1150`
  (Run409, CI #963 / `40157683231` all six GREEN on later read).
- Package A — `src/ark/agency/contracts.py` bounded ToolCall JSON ingress:
  source `50489c8dd24b90aece5819da89ae2f3a316695cc`,
  tests `0848e07bb3682ddb2911994e937d23d869152d4c`.
  A 4,096-value total-node budget, depth 32, 65,536-character single-string
  budget and 256 KiB accumulated UTF-8 text budget reject hostile/infinite
  mapping values, duplicate iterated keys and cyclic/deep payloads **before**
  registry admission. Accepted canonical request IDs are unchanged.
- Package B — `src/ark/agency/durable_occurrence_review.py` original
  ToolCall/OneShotAuthorization carrier custody across the first registry
  bind, local token digest, handle acquisition, BEGIN, schema read, monotonic
  reservation check, second registry bind, INSERT and commit:
  source `b1a53d2ce286b6d1ca677bfd21c818bbc2899c4f`;
  tests `7ab8a5b431d8d6483f5ee292a4234c25f8fce61a`,
  byte-prefix test correction `56996cb7cfe71370d7eb9eea5d71d0b21b6721f7`.
  A rejected callback **before** COMMIT must leave zero new rows. If an
  intercepted post-COMMIT callback changes input identity, the call rejects
  while the durable reservation remains consumed/UNKNOWN rather than replayed.
- Package C — `src/ark/observations.py` 1,024-character exact metadata ID
  budget, invalid UTF-8 rejection and direct `observation_id` source
  identity rechecks after JSON serialization and after SHA-256 hashing:
  source `9810027bc89336a2a5d3c39bc41af725104f9662`,
  tests `a93f1516d5e5940700f62d380858335af8ac7b57`.
  The existing valid Observation v1 digest vector must remain unchanged.
- Package D — standalone `src/ark/agency/planner.py` DAG admission bounded
  to 4,096 steps / 65,536 edges, with hostile non-tuple dependency carriers
  rejected before graph traversal: source
  `09219524714b46c4c229009bccf60e88b0e81eae`,
  tests `28e166cb71ba7523e895da5e3059d25af6222a21`.
  The pre-existing 1,500-step valid deep DAG remains within bounds.
- Package E — `src/ark/memory/contracts.py` MemoryWrite metadata ingestion
  rejects actual Mapping.items() streams after 64 yielded entries, irrespective
  of any dishonest __len__, and rejects duplicate yielded keys before SQLite
  persistence. Frozen Memory v1 DDL and accepted 64-entry mappings unchanged.
  Source `ad461148a93eb6e50b8693192b43ddea4fc76018`;
  tests `tests/test_memory_metadata_ingress_budget_run410.py`, initial
  `d9e5e3cbb1f02f2246ab361ea5f88c11f9a76743`, import-spacing correction
  `9948473c9bc2bf74af2a7b3ac169ab3bf94a4d84` (+6 regression cases).

## Threat/failure matrix

| Boundary | Reproduced input | Expected diagnostic |
| --- | --- | --- |
| ToolCall ingress | Infinite Mapping.items() | Fails closed within finite 4,096-item horizon |
| ToolCall identity | Duplicate map key / unbounded nesting / invalid Unicode | Rejects; no ambiguous identity hash or token spend |
| ToolCall identity | Canonically equivalent bounded inputs | Same deterministic request ID |
| Occurrence token digest | Reflected token ID swap during local hash | Reject before SQLite reservation |
| Occurrence subject | Equal-valued replacement argument mapping during hash/BEGIN/schema | Reject before commit; no result fabricated |
| Occurrence post-commit | Token ID swap just after COMMIT | Reject; persisted token remains consumed; automatic retry forbidden |
| Observation direct hash | JSON/hashing callbacks mutate source/privacy/timestamp | Reject rather than return mixed-field digest |
| Planner capacity | >4,096 steps or >65,536 dependency edges | Reject before graph materialization/traversal |
| Planner boundary | 4,096 standalone steps or 65,536 edges | Admit unchanged valid DAG |
| Memory v1 write ingress | Malicious Mapping.items() reports fake length then yields infinitely | Reject by the 65th item; no unbounded materialization |
| Memory metadata identity | Duplicate yielded key with different value | Reject before storing a misleading replacement |

All test objects are explicitly disconnected fixtures. No raw media is
loaded or exported; no actual ToolBackend is invoked or notified. The
synthetic ledger does **not** authenticate issuer, token, clock, storage or
external outcome. SQLite stores remain independently committed rather than a
global ACID transaction; local digest integrity is not an OS-file-handle or
external-side-effect attestation.

## CI evidence state at this document preparation

- Inherited Run409 exact checkpoint CI #963 / `40157683231`: **SUCCESS all six**.
- Run410 first package test HEAD `0848e07bb3682ddb2911994e937d23d869152d4c`,
  #965 / `40159514530`: **SUCCESS**.
- Occurrence correction HEAD `56996cb7cfe71370d7eb9eea5d71d0b21b6721f7`,
  #968 / `40159697018`: **IN_PROGRESS** at inspection.
- Observation test HEAD `a93f1516d5e5940700f62d380858335af8ac7b57`,
  #970 / `40159759500`: **IN_PROGRESS** at inspection.
- Planner final source/test HEAD `28e166cb71ba7523e895da5e3059d25af6222a21`,
  #972 / `40159811089`: **QUEUED** at inspection.
- Pre-Memory four-package CI #976 / `40160101058` for
  `6fbb6231d496c2f3612722a2f0b7149a73fcea01`: **Ubuntu 3/3 GREEN**
  (Python3.13 Ruff PASS and **2,179 pytest passed**); Windows 3 IN_PROGRESS
  at this doc edit. Older #968 and #970 failed **ten inherited assertion
  message matches** despite correct fail-closed behavior; fixed with precise
  source/token rejection messages by `abf29857b1e824448b8e36483bfcc464e5ec59bf`
  and three test regex expectations by `638cd02eaf6225f7c8a984942648c7c08389b4d1`.
  #972 and #975 failed all six **Ruff I001** at newly added Planner test
  import block; narrowed style fix `6fbb6231d496c2f3612722a2f0b7149a73fcea01`.
  These failed runs remain historical evidence and are never relabeled GREEN.
- Five-package total expected +8 ToolCall, +7 Occurrence, +9 Observation
  (three parameterizations), +5 Planner, +6 Memory = **+35**, 2,185 tests.
  Memory test-style HEAD `9948473c9bc2bf74af2a7b3ac169ab3bf94a4d84`
  CI #979 / `40160286078`: **QUEUED** at doc preparation. **2,185 PASS
  is not yet confirmed** until exact five-package CI finishes.
- Ruff and all six Ubuntu/Windows Python 3.11–3.13 jobs must be independently
  checked on the exact source/test HEAD and subsequent docs/checkpoint heads.

## Hard boundaries, preservation and next plan

Frozen V1/V2/Local UI/Launcher evidence, V3 Contract 1, Memory v1 and
ActionAudit v1 SQL schema remain unchanged. PR #5 remains Draft/unmerged/
NOT_PASSED; no Candidate or protected V2 final evaluation. No paid or
potentially billable API/service, GPU, additional credentials, real hardware,
private-data disclosure/deletion, destructive action, main merge or automatic
approval/promotion has been requested or undertaken.

Next: (1) verify the current five-package #979 exact-head CI, fix real
regressions only via normal Contents writes; (2) extend durable reservation/test crash boundaries
without conflating mock receipts with real exactly-once effects; (3) test
Memory v1 CAS/expiry and multi-store retained-witness partial erasure; (4)
continue privacy-safe Context and disconnected Scheduler/Observation lifecycle;
(5) gate trusted time/issuer interfaces, external effects, V3 approval and
hardware behind explicit human authorization.

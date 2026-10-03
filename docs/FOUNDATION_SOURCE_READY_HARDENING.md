# Foundation Source-Ready Hardening Queue

Status: implementation-preparation note for Draft PR #8. This is not PASS evidence.

## Planner

The next executable patch is intentionally narrow:

- require ordered dependency input and canonicalize it to tuple;
- expose immutable topology snapshots;
- make transition rules immutable;
- require exact `StepState` transition values;
- require exact non-bool non-negative revisions;
- use sorted traversal where registration order must not affect derived state.

Matching tests must cover set/frozenset/generator dependency rejection, raw-string state rejection, bool/negative revision rejection, topology immutability, status snapshot immutability, and transitive blocking.

## SQLite Memory

Preserve schema-v1 DDL compatibility while tightening behavior:

- serialize bootstrap with a write transaction before schema inspection;
- reject negative/newer schema versions and partial version-0 managed schemas;
- validate managed tables/indexes/triggers with exact schema fingerprints;
- validate persisted row storage classes and deterministic identity before conversion;
- sample trusted mutation time after the write lock;
- normalize create/CAS contention to domain conflicts;
- perform expiry cleanup with scope + revision + expiry-bound DELETE predicates and count only actual deletions;
- materialize read/search snapshots before trusted-time expiry filtering.

## Action Audit

Keep v1 compatibility first, then introduce any stronger schema through an explicit migration:

- serialized bootstrap and same-version schema validation;
- persisted event validation before exposure or append;
- write lock before trusted clock sampling;
- monotonic append time against the persisted tail;
- explicit v1-to-v2 migration for chain/anchor integrity rather than silent same-version DDL mutation.

## Execution safety chain

After the persistence primitives are GREEN:

1. immutable ToolRegistry with stable registration identity;
2. restart-safe one-shot authorization ledger storing only a token digest;
3. atomic authorization consumption plus execution-occurrence creation;
4. pre-action audit persistence before mock backend dispatch;
5. durable distinct outcomes for known-no-effect, outcome-unknown, and reported-success;
6. planner recovery journal and startup component readiness integration.

No item here authorizes paid/external compute, real Candidate generation, protected evaluation opening, promotion, frozen-contract changes, destructive work, new credentials, or main merge.


## Dependency-gated source-ready packages

The following packages have source-equivalent local validation but are intentionally not
integrated ahead of their lower-level prerequisites. They remain prototype/source-ready
evidence only until saved on an exact repository HEAD and CI is GREEN.

- **Observation fixture adapters:** exact immutable fixture-byte ingress, adapter-owned
  SHA-256, TEXT/TRANSCRIPT/IMAGE/SCREEN envelopes, transcript parent lineage, and no raw
  bytes retained in the envelope. Local focused suite: **9/9 PASS**. Integrate only after
  the ObservationEnvelope exact-type contract/source mismatch is closed.
- **Startup readiness:** immutable acyclic component graph, deterministic canonical
  readiness identity, lane-scoped dependency blocking, and registration-order independence.
  Local focused suite: **10/10 PASS**, including 256 randomized registration orders.
  Integrate only after component open/validate/recovery results are reliable.
- **Personal Context selector:** exact owner/namespace request scope, deterministic
  round-robin fairness, total/per-namespace budgets, content-free provenance, duplicate
  identity rejection, and plaintext-as-data behavior. Local focused suite: **14/14 PASS**.
  Integrate only after coherent multi-namespace Memory snapshots are GREEN.
- **Proactive scheduler state:** deterministic trigger identity, rolling notification
  budget, cooldown/minimum-interval semantics, restart-safe prepare deduplication,
  serialized SQLite writers, trusted-clock rollback rejection, and content-minimized
  persistence. Local focused suite: **9/9 PASS**. Integrate only after hardened durable
  state and action-safety prerequisites are GREEN.

The scheduler boundary sequence reproduced by the source-ready implementation is:
`notify @0 -> too_soon @50 -> cooldown @100 -> notify @200 -> window_budget @400
-> notify @1000`. A rejected too-soon evaluation does not advance the eligibility clock;
cooldown/window decisions do persist the new observation digest so unchanged observations
remain suppressible after the suppression boundary ends.

These packages add no live microphone/camera capture, no external service, no autonomous
write-effect authority, no paid compute, and no protected-evaluation access.

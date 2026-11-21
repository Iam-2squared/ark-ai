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


## Exact-PR8 staged integration preparation (2026-10-10 JST)

Work basis: PR #8 `27ef8a4b992a0a1bc5aae0f82c5b2179b3f53b8f` (Draft).
This is an **offline staged patch queue, not a saved source change, CI PASS,
approval artifact, or authorization to run any tool**.

Git blob SHA values were recomputed locally and matched the fetched branch tree
for the six agency source files (`__init__`, `registry`, `planner`, `contracts`,
`policy`, `audit`) and the two committed ToolRegistry reference fixtures.
The five local patches were applied in order with `git apply --check`, each
checked against its expected output bytes, and tested after application:

| Stage | Paths touched | Cumulative local tests | Status |
| --- | --- | ---: | --- |
| 00 registry frozen-vector tests | one new test file | 7/7 | local PASS only |
| 01 immutable Registry + public exports | two agency source files + six test files | 34/34 | local PASS only |
| 02 iterative/revision-guarded Planner | one agency source file + three test files | 53/53 | local PASS only |
| 03 exact-type Permission / JSON contracts | two agency source files + seven test files | 88/88 | local PASS only |
| 04 Action Audit v1 validation | one agency source file + six test files | 134/134 | local PASS only |

An independent V3 strict-JSON helper still has **16/16 local PASS**. It was not
included in the PR #8 patch queue and does not authorize PR #5 training,
Candidate generation, protected V2 evaluation, or contract modification.
The local assembled total is 150/150, using Linux Python 3.13.5;
**Ruff, a full live-repository suite, Windows matrix, and real Python 3.11
runtime are not proven for these patches.** Simple long-line/import formatting
was cleaned in the local candidate and tests rerun; this is not a substitute
for Ruff.

The normal GitHub Contents API again refused creation of the isolated Registry
vector regression test with an OpenAI safety-check rejection. Do not
repackage that rejected executable write through raw Git objects, ref movement,
or another hidden route. **No new GitHub source/test commit or CI run was
created.** Continue useful independent read-only audit, mock-only testing,
and preparation while the executable write path remains blocked.

Gate order: persist stage 00 through the normal allowed path; require exact-head
CI GREEN before stage 01; then require successive exact-head CI GREEN as each
stage is landed. Do not treat the compatibility `PermissionGate` as a
registry-authoritative durable WRITE authorization. Issuer provenance,
restart-safe occurrence/replay prevention, external audit anchors, and
mock-only audit-before-action require their own later review and evidence.
No frozen V1/V2/Local UI/Launcher evidence, main, or Draft PR #5 is changed.

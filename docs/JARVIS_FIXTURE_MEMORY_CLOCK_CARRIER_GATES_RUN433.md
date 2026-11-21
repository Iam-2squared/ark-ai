# ARK JARVIS — Fixture, Memory CAS and Synthetic Clock Source Custody (Run433)

This is a **non-normative, offline-only technical fault matrix**, grounded in
the named source/test commits. It does **not** alter the frozen V1/V2,
Local UI/Launcher, Memory V1 SQL, ActionAudit V1 SQL or V3 Contract 1.
All tests use disconnected caller-supplied fixtures or temporary SQLite.
They cannot authenticate human consent, hardware, a remote result or time.

## Work packages / exact source binding

| Lane | Normal Contents source commit | Regression commit | New parametrized cases |
| --- | --- | --- | ---: |
| Observation fixture result custody | `1ecf19ad27f14beaff791ea4744f24dbed4fc9f0` | `55c7ac9003ccedb7d9aef43ca903b33676f26dad` | 26 |
| Memory pre-COMMIT original carriers | `b8a9e2599a0824a2425434d699f8b913822aa8ff` | `adc2bd287a11ca4936c62b3fb5f0ec94ad5216d0` | 20 |
| Synthetic Clock numerical carrier custody | `9088a8718f3756eb1517a1646ea359b777b76cf4` | `73c10c2f372aaf1bfa50999d75a525924879213b` | 7 |

**Combined final executable/test HEAD:** `73c10c2f372aaf1bfa50999d75a525924879213b`.
The 53 added parameter-expanded tests are *introduced*, not asserted GREEN
until the exact-HEAD CI completes. No manual duplicate workflow run requested.

## Negative-path evidence boundaries

### A. Content-minimized Observation fixture construction

`src/ark/observation_fixture_adapters.py` seals both TEXT/TRANSCRIPT and
IMAGE/SCREEN results against a constructor (including its post-init hook)
returning a different envelope, forged type, mutated field or equal-text
replacement of a field carrier after the raw content hash was computed.
The original source, scope, adapter, time, content digest, parent and schema
carriers are required on the returned inert `ObservationEnvelope`.
Tests inject mutations across both text and binary fixtures; the unmodified
path still emits SHA-256-only envelopes with no raw text or bytes retained.

**Not established:** an authentic source, MIME/file safety, consent,
camera/microphone/display permission, model inference or dispatch authority.

### B. Atomic Memory row/event rollback on drift *before* COMMIT

`src/ark/memory/sqlite_store.py` already bound fields by equality during
the clock and after the audit event; those two pre-COMMIT fences now also
require original owner, namespace, source, content and expiry **object
carriers** (alongside the previously retained write/scope/metadata carriers).
Twenty test permutations target both create and CAS update, clock callback
and event callback, and five equal-value identity substitutions. The
expected invariant is **no partial row or event effect** for a rejected
pre-COMMIT write; a rejected update leaves its revision-1 row and create event.

**Not established:** external storage attestation, cross-SQLite atomic
transactions, whole-process crash durability beyond SQLite's own setup, or
physical deletion of every backup/cached personal-data copy. A successfully
COMMITted row/event must not be retroactively labelled rolled back.

### C. Caller-provided synthetic time carrier stability

`src/ark/agency/synthetic_clock_sequence_review.py` pins prior sample
sequence, source, wall-time and monotonic-time carriers, plus retained witness
numeric carriers. A newly constructed link must also hold the exact numeric
objects used to calculate it. Regression injects value-equal replacement
integers during iterator continuation, retained verification and link
construction, alongside a valid retained-prefix replay.

**Not established:** signed trusted time, real issuer authenticity,
anti-rollback hardware, OS-time synchronization, or authorization to act.
The result's `trusted_clock_verified`, `dispatch_authorized` and
`automatic_replay_authorized` properties remain False.

## Integration constraints / remaining work

1. Preserve UNKNOWN/RUNNING and reserved PENDING WRITE no-replay across the
   Planner → PermissionGate → Occurrence → ActionAudit → AuditLink restart
   chain. Memory and those ledgers are **not** one atomic cross-file commit.
2. Extend post-construction Clock result numeric-carrier custody; the
   present package covers *sample*, *retained witness* and *new link*
   carriers, not an externally authenticated time source.
3. Extend Memory multi-process CAS/expiry events and privacy revocation
   co-visibility using independent retained witnesses. No personal-context
   disclosure or genuine consent is inferred from a local veto absence.
4. Keep PR #5 Draft/NOT_PASSED. No real Candidate/adapter, V2 protected final
   evaluation, promotion, GPU, paid API, account connection or main merge.

## Structural source isolation

At final test HEAD `73c10c2f372aaf1bfa50999d75a525924879213b`,
nontruncated Git tree comparisons against main
`7a843f17eb96ed13d66f23b58b06406b3002e405` show:
main **94 blobs**, PR #8 **570 blobs**; **476 new files**,
**zero original-main blobs modified and zero deleted**.
This is path/blob isolation evidence, not a claim of system-wide integration
or proof that all new code passed the entire CI matrix.

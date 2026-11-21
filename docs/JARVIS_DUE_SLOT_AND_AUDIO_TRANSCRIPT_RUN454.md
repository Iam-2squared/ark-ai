# ARK AI — Detached Due Slot & Audio Transcript Binding (Run454)

## Evidence identity and scope

- **Work-basis HEAD:** `447174982ed181a369077b00639eabe850467d24` (Run453 checkpoint; verified before package writes).
- **Last source/test HEAD:** `d6efa7b5c85e9ec2a1c3527279756abdf4b2f5e1` (no claim of all-matrix GREEN).
- **Branch / PR:** `research/jarvis-foundations` / #8 Draft; PR #5 Draft, unmerged.
- **New files** (GitHub blob SHA-1, matched with locally tested `git hash-object`):
  - `src/ark/agency/disconnected_due_reservation.py` — `311b95a7f47833a226bb2ea274dd5a64e37f715c`
  - `tests/test_disconnected_due_reservation_run454.py` — `7cdd485a2890475450b5f6c406b37de278f237e0`
  - `src/ark/offline_transcript_binding.py` — `7baad5fc869c24c2314876bc16d2e2c7c3def098`
  - `tests/test_offline_transcript_binding_run454.py` — `2a1c1b8f15ca7a1d2d2f007ada38a87bffd09d42`

## Package A — restart-safe, *synthetic* due-slot reservation

A new isolated SQLite fixture `DisconnectedDueReservations` can initialize an explicitly
selected absolute local test database; independently inspect a counted digest witness;
and transactionally reserve a due slot exactly once for a given policy digest and due
millisecond. The source is a bounded, no-dispatch scheduler state machine—not a daemon.

- `BEGIN IMMEDIATE` serializes concurrent reservation transactions. An existing
  slot is never reissued after process restart; duplicate slot keys, stale witnesses,
  clock regression, future/late caller claims, boolean-for-int confusion and malformed
  digests fail closed. Tests cover both thread races and two spawned OS processes.
- Strict single-table schema, `user_version`, row structure, monotonic timestamps,
  deterministic policy/due slot identity, row budget <=512 and `quick_check` are
  reviewed before reservation. Only initialization creates storage; ordinary reads/
  writes use URI read-only/read-write modes and cannot resurrect missing databases.
- The retained `DueReservationWitness` **must be independently stored by a caller**.
  If an attacker erases/replaces the entire SQLite file *and* the independently
  retained witness is lost/replaced, this fixture CANNOT prove anti-rollback or
  exactly-once external effects. Test demonstrates local-file rewind and refusal
  with the original retained witness. Caller-supplied `observed_now_ms` is NOT
  a trusted clock. Receipt is never notification, user permission or execution.

## Package B — offline, claimed audio/transcript frame custody

`review_audio_transcript_binding` validates synthetic `AudioMetadataClaim` and
sorted, non-overlapping `TranscriptSegmentClaim` intervals in *audio frame* units,
then returns only a domain-separated fingerprint and bounded metadata.

- Exact carrier classes and bool-safe integer tests; supported sample rates
  8/16/22.05/32/44.1/48 kHz; claimed audio <=120s; 1–64 segments, <=2048 UTF-8
  bytes each and <=8192 bytes overall.
- Rejects invalid frame boundaries, segment reordering/overlap, checksum mismatch,
  non-NFC strings, control/format/bidi characters, surrogates and oversized text.
  Sensitive transcript strings are `repr=False` and are not included in the returned
  preview. They can still be accessed through input fields or explicit serialization.
- Audio checksum/owner/scope and transcript text are ALL CALLER ASSERTIONS.
  No audio is read, recorded or recognized; no real ASR, trusted observation,
  speaker identification, consent, privacy export, or Tool grant occurs.

## Local validation vs CI

- **Local isolated Python 3.13.5 / pytest 9.0.2: 55 PASSED**, including
  multithread/multiprocess SQLite races, duplicate prevention, simulated rollback,
  version/schema tamper, exact-input rejection, metadata binding and Unicode cases.
  Source/tests were byte-identical to the GitHub blobs listed above.
- `compileall` PASS; all new Python source and test lines <=100 columns.
- Additional independent seeded local property probes: **180** durable synthetic
  due-slot reservations with duplicate suppression, plus **500** framed transcript
  acceptance/checksum-tamper checks, all PASS. Not 680 extra pytest cases.
- **Exact final source/test HEAD CI:** #1367 / GitHub Actions run
  `40341699473`: QUEUED at inspection (2026-10-26 23:39 JST).
  Previous intermediate package CI is also pending. At inspection GitHub Actions
  showed **123 queued / 6 in progress**, including older historical Windows jobs.
  No duplicate manual workflow was triggered.
- Full repository pytest/Ruff, Python 3.11/3.12, Windows/Linux six-job matrix,
  packaging/UI and integrated lower-layer proof remain **UNCONFIRMED**. Local Ruff
  unavailable; whole clone blocked because github.com DNS resolution fails. This
  detached implementation does not authorize integration of queued-CI dependencies.

## Hard boundaries and next integration conditions

Existing frozen V1/V2/Local UI/Launcher evidence, Memory V1 and ActionAudit V1
schemas, V3 Contract 1, contamination/provenance/regression/reproducibility gates,
and protected V2 final-evaluation boundaries are unchanged. No paid API/GPU,
Candidate or weights, credentials, machine/microphone action, real scheduler,
external ToolBackend, export, protected evaluation, automatic promotion or merge.
PR #5 and #8 remain Draft/unmerged. **ARK full JARVIS = NOT_PASSED.**

**Next plan:** inspect exact-head Actions once runners advance; fix actual failures
only. Never auto-replay reserved, RUNNING or UNKNOWN occurrences. Require independently
retained witness and trusted clock/issuer/consent/audit evidence before any real
scheduler or Tool dispatch. Validate all dependent lower-layer exact-HEAD GREEN
before integration with proactive/observation/ASR/PermissionGate paths.

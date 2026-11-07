# ARK Run453 — Offline Memory delta & private-code diagnostics

**Scope:** PR #8 Draft `research/jarvis-foundations`, separate reversible research modules. **JARVIS NOT_PASSED.**

## Work basis and saved source

- Invocation work-basis: `883c786c4f9b2c922dfc62b6c6f5b8148ace8df6` (Run452 checkpoint).
- Package A source: `src/ark/offline_memory_delta.py` Git blob `a13e3f9dbd072bfcc4d2ce71f237f81f57c11b80`, and `tests/test_offline_memory_delta_run453.py` blob `65f188c5213b8458b2688ec1a85663c76ca64600`. Saved test HEAD `6cc10ab9459ea4b4a525cb6459258b908e555e1d`.
- Package B source: `src/ark/private_diagnostic_ledger.py` Git blob `db6acd49aa2de52372dc473934fa63524e7fb191`, and `tests/test_private_diagnostic_ledger_run453.py` blob `20b57ef7344ae0aa942059a59c62101cc036c7a7`. Saved source/test HEAD `b33945bb51c41a4050787086ec2c625e6ac48787`.
- Four normal GitHub Contents commits for these four **new files**; no frozen source/contract/evaluation or existing implementation changed. Git Blob SHA-1 for each saved file equals the byte-for-byte local `git hash-object` of its focused-test source.

## Package A: metadata-only Memory snapshot reconciliation

Pure, bounded, deterministic analysis of separately presented prior/current snapshot **claims** (up to 64 rows), using exact types, UTF-8-independent ASCII-safe canonical metadata, domain-separated SHA-256, strict owner continuity, sorted record membership, stable creation/scope identity, active expiry bounds, revision-guarded update classification, and explicit matching synthetic tombstones for removed records.

Rejects duplicate/reordered/missing removal receipts, unexpected/orphan receipts, invalid expiry claims, revision gaps/rollbacks, unrecorded changes, malformed IDs or SHA fields, stale snapshots, forbidden bool-as-int carriers, and post-capture identity substitutions. Summaries hide record IDs from Python repr. No plaintext content is requested or retained.

**Important:** `retained_prior_fingerprint`, `retained_current_fingerprint` and deletion event hashes are **caller-controlled strings**. Matching them is NOT an independently verified journal witness, trusted time, CAS database proof, erasure or authentic deletion. This parser deliberately does **not** open SQLite, mutate rows, delete or replay any WRITE. A revision increment across a prior expiry is not authoritative proof of timely renewal; real adoption needs independent trusted event/custody/clock proofs. Output authority flags remain false.

## Package B: strictly enumerated diagnostic code ledger

Produces canonical JSONL and a domain-separated SHA-256 chain from **fixed allowlisted public codes only** (component, stage, outcome, reason) plus bounded monotonic sequence numbers and a retained anchor supplied by the caller. Arbitrary user text/tool arguments/private content cannot enter the serialized fields, since exact `str` is required and the allowed vocabulary is fixed. Output is in-memory; no file or network write, no raw exception echo, and JSONL preview is hidden from `repr`.

The chain checks **syntactic self-consistency**, not provenance. A caller can fabricate an anchor/events; no trusted signer, human consent, immutable external reference, real ActionAudit record, privacy export permission, exactly-once execution or production logging integration exists. Do not mistake the outcome token `reviewed` for human review or any grant.

## Validation (local only; not GitHub all-environment GREEN)

- Python **3.13.5**, pytest **9.0.2**: **68 PASSED** on Git-blob-identical source/tests; 43 Memory delta and 25 diagnostic ledger cases.
- Local `compileall`: PASS; all new Python lines <=100 characters.
- Additional ad hoc independently seeded property/oracle checks: **1,200** bounded Memory change-set comparisons, incomplete tombstone denials and **500** diagnostic sequence + allowlist/adversarial rejection checks: **PASS**. These are separate probes, not extra pytest cases and not checked-in test artifacts.
- Ruff is **not installed** locally; GitHub clone still blocked by `github.com` DNS. No whole-repository pytest/Ruff, Python 3.11/3.12, Windows or all-six exact-head CI GREEN claim.
- GitHub source+test HEAD `6cc10ab...`: CI **#1358**, run **40335104634**: **QUEUED** on inspection.
- GitHub final source+test HEAD `b33945bb...`: CI **#1360**, run **40335857725**: **QUEUED** on inspection. Technical evidence and checkpoint result CI must be inspected after their commits; no manual reruns.

## Independent CI forensic lane (read-only)

At inspection on 2026-10-26, Actions had **113 QUEUED** and **7 IN PROGRESS** older runs. Historical source `b07efec...` run **#1243 / 40237184462** Ubuntu Python 3.13 failed **2**, passed **2941**, skipped **1**. Both failures were the historical `test_privacy_cross_process_veto_projection_run434.py` expected-number-of-successful-clearances mismatch. Current source blob `61b197bdf0728c25387a55a9f9beb7082836b418` distinguishes **2 attempts** from **1 successful clearance**; those older runs predate the Run448 correction and do NOT establish failure of current HEAD. Windows jobs from the same historical run remain IN PROGRESS in the observed job snapshot. The per-job 45-minute timeout added in Run452 does **not** retroactively apply to older already running workflow executions.

**Action:** do not dispatch duplicate CI, skip checks, shorten test coverage, or treat queued work as GREEN; wait for naturally scheduled current-HEAD evidence while progressing independent reversible modules.

## Hard gates and next integration

No frozen V1/V2/UI/Launcher, Memory V1 Schema, ActionAudit V1 Schema, V3 Contract 1, protected final-eval, contamination, provenance, regression or reproducibility evidence changed. PR #5 and #8 remain Draft/unmerged; no paid compute/API, GPU training/Candidate, credentials, account connections, physical PC, microphone, real ToolBackend, destructive filesystem/database operation or main merge.

**Next:** confirm exact new-HEAD six-job CI; audit Memory ledger independent tombstone/provenance and cross-process source snapshots, separately; integrate only after real lower-level GREEN and reviewed trusted evidence. For privacy-safe diagnostics, first prove scope/redaction/output handling with real (but disconnected) caller boundaries before wiring into audit or logging. Keep UNKNOWN/RUNNING and reserved PENDING WRITE under permanent non-auto-replay.

# JARVIS Run444 — detached synthetic READ journal and bounded result bindings

Two independent, reversible, zero-cost fixture-only foundations. Neither module imports ToolRegistry, PermissionGate, ToolBackend, MemoryStore, V3 runtime, the in-flight disconnected toolbox, or the detached batch planner. They do **not** operate on real personal data, run actual tools, open user databases, or authenticate issuer/clock/human consent. They **must not be integrated** until the exact lower-level CI dependencies are GREEN.

## Package A: durable, CAS-checked local READ digest journal

- Source `src/ark/agency/disconnected_read_journal.py`: **Git blob `bcb1192602eb1bcfe1a4909af243564492a7d969`**.
- Tests `tests/test_disconnected_read_journal_run444.py`: **Git blob `3bfcec924509e639cd1745bee02b5b4cef73c26c`**.
- **24 local pytest PASS** using Python 3.13.5, disposable tmp_path SQLite fixtures only.

The explicitly supplied absolute local Path must name a new file for creation; a reopen requires the existing marker and exactly the expected SQLite schema, with unexpected triggers/tables rejected. Only request/step IDs, allowlisted synthetic READ operation labels, input/result SHA-256 strings, contiguous sequence numbers and domain-separated local hash-chain digests are stored (never result contents). A separately retained `ReadJournalWitness(count, tip_sha256)` is required to verify a read snapshot and to append a record with `BEGIN IMMEDIATE`/CAS. Simultaneous Python spawn processes competing for the same original witness yield one winner; a stale writer fails rather than replays. Failures roll back insertions. Tests exercise cross-process racing, reopen, tail truncation, middle deletion, altered fields, altered schema/trigger, duplicate receipts, malformed IDs/digests, foreign SQLite files and symbolic links.

**Limitations:** caller-provided SHA-256 is not a verified Tool result; full control of both ledger and retained witness defeats local digest protection. This is not cryptographically authenticated storage, a trusted clock, an external receipt, a global cross-SQLite transaction, an erasure guarantee, or a verified exactly-once real-world operation. Opening or creating a selected local SQLite file is an *explicit local fixture operation* only; no automatic user filesystem discovery. Path checking does not eliminate arbitrary same-path hostile filesystem races. All permission, real external effect and replay flags are False.

## Package B: deterministic, bounded earlier-READ result reference substitution

- Source `src/ark/agency/disconnected_reference_binding.py`: **Git blob `56d92a71afe3928a6d81610ae7a0cca3c97149ae`**.
- Tests `tests/test_disconnected_reference_binding_run444.py`: **Git blob `530bcc92fbe1d0933a0af796f48da115b6f5680c`**.
- **33 local pytest PASS** using Python 3.13.5; in-memory synthetic JSON only.

A canonical argument JSON template can contain an exact `{"$from":{"step_id":"step_<16-hex>","pointer":"/..."}}` sentinel. The resolver reads only an explicit bounded prior-step prefix, validates ordered unique result fixtures and independently supplied per-result local SHA-256, walks JSON Pointer-like keys/indices with strict escape and bounds checks, and emits deterministic canonical arguments with a domain-separated binding digest. It rejects unknown/forward steps, reordered/duplicate results, missing pointers, ambiguous placeholders, repeated JSON keys, floats/nonfinite numbers, >64-bit integers, invalid Unicode and output expansion beyond 4 KiB. This is **substitution, not execution**. The caller must separately prove original batch membership; all source-authentication, dispatch, replay and real-result flags remain False.

## Exact-head evidence / scope

- Invoked from canonical Run443 checkpoint **`07d25a353537f02ceab5698c1081bd6ce3551ad3`**.
- Final two-package source/test HEAD after exact-byte correction **`4996840c1687b9f1a114821fb39f82dc57b19f44`**.
- GitHub compare `07d25a3...4996840`: **5 commits, exactly 4 new files, zero modifications/deletions of pre-existing files**. One initial source text transfer changed two occurrences of the word `external`; fixed through standard GitHub Contents `update_file` and independently checked all four final Git blobs equal the exact local pytest-tested file blobs.
- Isolated local `PYTHONPATH=/mnt/data/ark_run444/src python -m pytest -q /mnt/data/ark_run444/tests`: **57 passed (24 + 33)**, Python `compileall` PASS and all four new source/test files have no >100-character lines.
- No complete GitHub repository checkout locally (GitHub host DNS unavailable), no local Ruff, no full-repository pytest, no Python 3.11/3.12 or Windows proof. **CI #1293, Run ID `40277762483`, QUEUED** on final source/test HEAD at the post-commit audit; no six-job GREEN claim. Previous Run443 source CI #1286 and checkpoint #1288 were also QUEUED.
- Older Run434 checkpoint CI #1231 (Run ID `40228196762`) showed 3/3 Ubuntu GREEN but Windows 3/3 still IN PROGRESS in pytest. A single Windows job-log fetch failed with GitHub BlobNotFound; this supplies no traceback and does not show that the earlier oversized-test-name fix worked.

## Next plan / 今後の方針

1. Verify exact-head CI #1293 and its follow-up document/checkpoint commits when available. Diagnose genuine failures by job logs without repeating equivalent workflows, weakening tests, or altering the source being tested while CI runs.
2. Keep the journal and JSON resolver **detached** until their own source CI plus Run442 toolbox and Run443 batch planner dependencies are exact-head GREEN. Only then design a completely disconnected/mock multi-step READ pipeline with explicit result custody; never infer permission or real external execution from matching local hashes.
3. Separately advance Memory CAS/expiry integrity and Personal Context revocation/retention. Defer cross-store WRITE recovery integration until the relevant Run434/438/439 evidence is GREEN. UNKNOWN/RUNNING or reserved PENDING WRITE must not be replayed automatically.
4. Preserve frozen V1/V2/Local UI/Launcher evidence, Memory V1/ActionAudit V1 schemas and V3 Contract 1. PR #5 and PR #8 stay Draft/unmerged. No paid services/compute, credentials, Candidate/weights, protected V2 final evaluation, promotion, destructive action, real-world Tool dispatch or main merge.

**Complete JARVIS: NOT_PASSED.** This evidence documents only bounded, reversible synthetic/local capabilities, not a verified integrated assistant.

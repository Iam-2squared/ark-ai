# JARVIS Run442 — disconnected utility execution and bounded local context preview

Scope: **two reversible, isolated Python 3.11-compatible implementation/test packages**, plus read-only GitHub Actions backlog diagnostics. Neither package imports pending Run434 recovery evidence or Run439 multi-store quarantine reviewers. No V1/V2/Local UI/Launcher source, Memory v1 / ActionAudit v1 schema, V3 Contract 1, or protected evaluation was edited.

## A. Real deterministic calculations without external effects

- Source: `src/ark/agency/disconnected_toolbox.py`; exact Git blob `4f2ffb04d913ea4c5a9fc4ab935631cd15b0616d`.
- Tests: `tests/test_disconnected_toolbox_run442.py`; exact Git blob `88811b7b1ccd994b02a9fadfe33080a516b5ce0e`.
- Four narrowly allowlisted, pure in-memory fixture operations: `math.sum`, `text.stats`, `text.find`, `json.inspect`. No command interpreter, subprocess, file or network access, plugin installation, credential handling, or dynamic code execution.
- Exact request types and `req_` identity, canonical bounded JSON inputs, duplicate-key rejection, signed-64-bit math overflow denial, float/nonfinite denial, Unicode and depth/length budgets; domain-separated local SHA-256 input/result digests. Reflective mid-hash mutation is rejected.
- Result explicitly denies dispatch, automatic replay and external-outcome attestation. **This is not a ToolBackend, registry-bound authorization, consent or real-world action receipt.** It is an unprivileged fixture-calculation substrate for later disconnected/mock execution integration only after exact-head GREEN.

## B. Privacy-sensitive context is not silently exported

- Source: `src/ark/personal_context_offline_preview.py`; exact Git blob `959ed130b6a41b4ee29556784454ed77bf272b00`.
- Tests: `tests/test_personal_context_offline_preview_run442.py`; exact Git blob `14e4bb7d05e8899a1e35b52cadfa1c53e6e70356`.
- Explicit synthetic fixture batches only, up to 32 sorted unique records; fixed owner digest; exact allowlisted scope hashes, expiry checks, UTF-8 content hash verification, 4 KiB per record / 16 KiB total budget, canonical local JSON and a domain-separated local integrity digest. Mixed owners, stale/unknown scopes, duplicate IDs, changes during hashing and oversized batches fail closed.
- This preview **contains the caller-supplied synthetic text** and must remain memory-local. The record owner, content hash, allowed scopes and supplied clock are untrusted caller claims, not real consent, revocation freshness, secure retention, or provenance evidence. No Memory database is opened, no real user context is accessed and no external disclosure occurs. Returned consent, export, dispatch and retention authorization flags remain false.

## Exact local validation and known limits

- Independent Python **3.13.5**, staged local `PYTHONPATH=/mnt/data/ark_run442/src python -m pytest -q /mnt/data/ark_run442/tests`: **77 passed** (42 disconnected-toolbox cases; 35 context-preview cases). Source/test files also passed Python `compileall` and a simple 100-character line-length scan. No Ruff binary or full GitHub checkout was available to this container; **this is NOT full-repo, Windows, six-job or Ruff evidence**.
- Every GitHub-returned source/test blob SHA matches the exact bytes in the passing local test staging area. Initial transfer of the disconnected toolbox's embedded JSON negative cases omitted ten necessary escape bytes in its first test-file commit. A subsequent **normal GitHub Contents `update_file`** corrected those bytes, preserving all 42 cases; the final test blob matches the locally tested bytes. No raw Git objects, forced refs or relaxed test assertions.
- Opening work-basis/Run441 checkpoint HEAD: `7daa5d3fe58de663ecc30390ace4a484ba8be799`. Latest two-package source/test HEAD: `9ce4ef04dd403ea64c836e4e67d02d04724fbbaf`. GitHub compare reports **5 commits, 4 new paths, no existing-file modifications/deletions** from work-basis to that HEAD.
- First completed toolbox source+test HEAD (after escaping correction): `4dcd4af4ccb38e7e82c619f93a090afcfc3a8866`; associated CI **#1278 / 40266199569 QUEUED** at inspection. Second source+test HEAD `9ce4ef04dd403ea64c836e4e67d02d04724fbbaf`; CI **#1280 / 40266285725 QUEUED** at inspection. Latest checkpoint-result HEAD needs separate inspection after status write. Nothing in an older job can substitute for exact-head GREEN.

## CI throughput/read-only forensic finding

The existing `.github/workflows/ci.yml` runs a six-job Ubuntu/Windows × Python 3.11–3.13 matrix with full pytest, Ruff and packaged CLI/UI/evaluation smoke tests. GitHub Actions API returned **44 queued runs** and **7 in-progress runs** at this inspection, with the in-progress block around #1225–#1231. In older in-progress runs, the Ubuntu jobs were GREEN while the Windows jobs remained in the `Run pytest` step; several older runs completed CANCELLED, not PASS. The exact latest queued jobs have **not** reached GREEN, and Windows recovery after the Run437/438 bounded pytest IDs is unproven. An attempt to fetch two still-active Windows log blobs returned BlobNotFound, not a meaningful test traceback. No manual dispatch, rerun, cancellation, queue manipulation or workflow weakening was performed.

## Next gates

1. Inspect latest exact-head CI after it runs, including six-platform Ruff/full-suite/UI; fix genuine errors only via the normal GitHub Contents path after re-reading branch HEAD.
2. After this toolbox's exact HEAD turns GREEN, consider **only disconnected mock** ToolRegistry/PermissionGate integration with explicit exact-type binding; never promote fixture results to authority or external-effect receipts.
3. After local context preview and Privacy revocation validators each have exact-head GREEN, add an explicit bounded revocation-freshness admission path before any real Memory content is considered for an on-device context. A synthetic clock or allowlist does not substitute for consent.
4. Preserve the pending Run434/438/439 independent WRITE recovery components until their own GREEN; no replay of UNKNOWN/RUNNING/reserved PENDING WRITE. No new spending, Candidate training, secrets, protected evaluation, actual hardware use, destructive deletion, or main merge.

**Status: isolated, reversible, free-only foundation; complete JARVIS NOT_PASSED.**

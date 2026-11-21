# JARVIS Run441 — untrusted authority and privacy-erasure evidence boundaries

**Scope:** two independent, disconnected, read-only diagnostics and their focused
regressions. Neither module imports the other, executes a backend, opens a SQLite
database, reads a user file, captures a sensor, sends a notification or performs
data deletion. No real issuer/consent or trusted-time provider exists in either.
Both modules are reversible additions under Draft PR #8, not changes to a frozen
V1/V2/Local UI/Launcher contract, Memory v1 DDL, ActionAudit v1 DDL or V3 Contract 1.

## A. Claimed issuer, trusted clock, consent and audit gaps

New source: \`src/ark/agency/synthetic_authority_boundary_review.py\`.
Local exact Git blob: \`6166604041cb563a47fbd10e7eee78516c70ced2\`.
Tests: \`tests/test_synthetic_authority_boundary_run441.py\`;
Git blob \`d8db67a1758e3a44b6feebb4ed2d32be93ed4e1f\`.

The bounded review records only caller-provided synthetic identifiers, registry
revision, bound-action identity, occurrence digest and non-negative 64-bit time
claims with a strictly increasing expiry. It distinguishes six evidence gaps:
issuer signature, authenticated time, human consent, pre-action audit, persistent
occurrence/replay fence and external-result attestation. Accepted probe states
are **absent**, **unknown** or **caller_claimed**. A claimed "verified" state is
rejected, rather than silently promoted to trust. Every returned gap report
keeps issuer/clock/consent authentication, dispatch authority, automatic replay
and external outcome knowledge **False**, even if all six probe states say
"caller_claimed".

An optional independently retained local SHA-256 digest can expose drift
between observations, but cannot authenticate origin or make the observations
complete. Exact dataclass types, identity carriers and bounded canonical
serialization are checked across the hash callback. No cryptographic signing,
trusted clock, human approval or backend outcome verifier is implemented.

## B. SQLite/WAL privacy-erasure claim classification

New source: \`src/ark/privacy_erasure_evidence_review.py\`;
Git blob \`217a7d2cd5d1b6132ad1336467a9cc2a03ecda65\`.
Tests: \`tests/test_privacy_erasure_evidence_run441.py\`;
Git blob \`e7397ead82e8a8dc7281320da644a90a7d89fbe5\`.

The input contains caller-reported owner-scope digest, logical row presence,
reader/snapshot state, checkpoint status, secure-delete policy, backup exposure
and claimed WAL bytes. The result records why available *claims* are
insufficient: active/unknown readers, busy/unrun checkpoint, positive/unknown
WAL bytes, missing secure-delete configuration, or backups/snapshots.
**Even the most optimistic input** (row "absent", no readers claimed, complete
checkpoint claimed, secure-delete ON claimed, zero WAL bytes claimed, no backup
claimed) leaves both \`independent_storage_attestation_missing\` and
\`forensic_scope_not_attested\`. No returned result claims row-deletion proof,
WAL reclamation proof, forensic erasure or cleanup permission.

This faithfully separates the terminology in
\`docs/PRIVACY_ERASURE_SEMANTICS.md\`: application-level row absence is not
byte reclamation, and byte reclamation is not comprehensive forensic erasure.
A local SHA-256 digest is change detection, not authenticated evidence. No
SQLite connection, WAL truncation, deletion, VACUUM or backup modification runs.

## Local test and GitHub evidence

- Both new modules and both new test files match the above GitHub-returned
  Git blob SHAs byte-for-byte with the isolated local files.
- Isolated local Python **3.13.5**: \`PYTHONPATH=/mnt/data/ark_run441/src
  python -m pytest -q /mnt/data/ark_run441/tests\`: **47 passed**.
  Python \`compileall\` passed for new sources. No full-repo checkout or Ruff
  binary is available in the working container. No Windows execution or
  whole-project import/dependency integration is claimed.
- First coherent source+test package HEAD
  \`5d4ee804cae6a2056e963d2422b782ec72a182d1\`:
  PR CI **#1271 / 40261533715 QUEUED** on inspection.
- Second source+test package HEAD
  \`c44207564868bbd7c9422d8f39870e0b71d57e7d\`:
  PR CI **#1273 / 40261622594 QUEUED** on inspection.
- GitHub comparison from Run440 checkpoint
  \`031f93ee0d0492d3c3c891c63779f952060c460e\`
  through the new second-package HEAD reports **four commits** and exactly
  four **added** paths, with zero pre-existing files modified or deleted.
- Exact-HEAD six-platform Ubuntu/Windows Python 3.11–3.13 Ruff/pytest
  **GREEN remains unconfirmed**. Queued CI does not attest these packages.
  No manual duplicate workflow, cancelled run, paid API or external GPU was used.

## Non-authority and next gates

These results are *not* licenses to connect a live ToolBackend, start an
issuer, provide human consent, assert real-time accuracy, use a one-shot token
for real dispatch, erase user data, or call a Candidate validated. The
untrusted claims are intentionally unsuitable for any authorization or
forensic-erasure promotion.

1. Verify #1271/#1273 and the final checkpoint's own six-job CI, fix actual
   lint/test failures by the permitted GitHub Contents route only.
2. Keep prior Run434 recovery bundle and Run439 multi-store WRITE quarantine
   separate until their own exact-head GREEN. Complete independent original
   WRITE-list evidence before any deny-only cross-store connection.
3. Advance a separately authenticated clock/issuer/verifier *interface* only
   when authority requirements and independently retained receipts are
   defined; no caller flag can substitute for verification.
4. Treat irreversible erasure and new personal-data access as separate consent,
   coverage and evidence gates. Keep both PRs Draft/unmerged and all frozen
   evaluations, zero-cost boundaries and automatic WRITE replay restrictions.

# ARK AI Run829 — Personal Context restart custody & ActionAudit SQLite WAL forensics

**Scope:** Non-UI, disconnected/local-first, reversible Draft PR #8 work only.
**Starting basis:** `7109043fe1420387d0b0cad105cf72bb780cb76e` (Run828 exact checkpoint).
**ARK/JARVIS:** **NOT_PASSED**. Authored test cases are **not** equivalent to passing CI or a real-machine evaluation.

## Package A — Personal Context restart helper authority (9 regression cases)

- [Source `99586820`](https://github.com/Iam-2squared/ark-ai/commit/995868202d86d5bcf9bdcb8902c8f31d4b90643f) adds import-time witnesses for the restart review's copied and defining-module `_inspect` / `_check_witness` helpers and defining ledger's `_open` / `witness` class methods. Rechecks occur before the first private-local read and after synthetic callback boundaries. Replacements are refused; no personal content is exported.
- [Tests `bf77939b`](https://github.com/Iam-2squared/ark-ai/commit/bf77939b59d61efa81d569f3eebe37c3a6929220) cover six read/validator rebindings, two during-read rebindings, and unchanged denial-only restart. This does not authenticate prior historical data, grant consent, prove erasure, or authorize context disclosure or replay.

## Package B — ActionAudit sidecar refusal diagnostics (10 regression cases)

- [Source `232d4b25`](https://github.com/Iam-2squared/ark-ai/commit/232d4b254d6940db03fe096e1a9470de7ea5628a) preserves exactly the existing reject rule for nonregular or non-single-linked `-wal/-shm/-journal` sidecars. Rejected errors now include only suffix, filesystem file-type bits, and link count. No path, request ID, raw argument, row bytes, alias bypass, or unsafe retry.
- [Tests `bd79b55a`](https://github.com/Iam-2squared/ark-ai/commit/bd79b55aad71efd0dcb63e90286af72d141c3745) cover symlink/directory/hardlink sidecar refusal across all 3 suffixes plus an ordinary SQLite reopen.

## Package C — Disposable cross-process ActionAudit WAL reproduction (22 regression cases)

- [Diagnostic source `ca77bccf`](https://github.com/Iam-2squared/ark-ai/commit/ca77bccf97b72e21f6d803d27bb065ade8a40f48) adds `scripts/diagnose_audit_sidecar_startup.py`. Explicit, bounded 1–30 temporary-fixture iterations compare **sequential vs concurrent independent-process bootstrap**, with optional **read-only-in-effect WAL keeper**. Child responses use bounded strict JSON, duplicate-key/nonfinite rejection, allowlisted no-path output, failure phase and sidecar metadata, no raw arguments. It performs local synthetic ActionAudit rows only, not ToolBackend execution.
- [Tests `78668686`](https://github.com/Iam-2squared/ark-ai/commit/78668686653708219de37c52e44fb9c8b0265c39) cover limit/JSON security guards, benign WAL-keeper 2-child receipt and CLI disclosure constraints.
- [Targeted source repair `e5d0ccd0`](https://github.com/Iam-2squared/ark-ai/commit/e5d0ccd0986d77b434cbb9a9727bc4148840166a): child-side regular expression now matches the literal diagnostic parentheses, rather than over-escaped backslashes. No audit path protection weakened.

## Observed CI forensics and exact-head limitations

- **Previous Run828 checkpoint** `7109043fe1`: [CI #43314755648](https://github.com/Iam-2squared/ark-ai/actions/runs/43314755648) **GREEN 6/6**, individually inspected Windows/Ubuntu × Python 3.11–3.13 jobs.
- [Prior CI #43313725582](https://github.com/Iam-2squared/ark-ai/actions/runs/43313725582) **FAIL** on Ubuntu 3.13 independent audit child startup: existing `ActionAuditSchemaError("audit SQLite sidecar alias refused")`; other 5 jobs GREEN. This is not evidence of a malicious link or a successful audit effect.
- [Prior CI #43314091179](https://github.com/Iam-2squared/ark-ai/actions/runs/43314091179) **FAIL** on Ubuntu 3.12 Memory independent-process `separate-source`: the rejected `-shm` was **regular** with `link_count=0` during an independent writer lifecycle; other 5 jobs GREEN. The earlier unannotated refusal is now bounded filesystem evidence, not permission to allow zero-link aliases.
- Current package CI was triggered by GitHub Contents API commits, **not manually duplicated**. The exact final Run829 HEAD CI status must be read independently; source/test intermediate GREEN does not imply final GREEN.
- No local full suite, physical GGUF, real Candidate training, external action or runtime-independent provenance was run or claimed.

## Invariants unchanged

- No new UI/frontend work; Draft PR #9 remains untouched. Frozen V1/V2, Local UI and Launcher contracts/evidence unchanged. Draft PR #5 remains unmerged under its approval gate.
- Zero-cost local fixture only. No real GPU/paid compute/service/API, account connection, credential, protected final evaluation, Candidate promotion, irreversible operation or approval-required main merge.
- A file type/zero-link observation during WAL lifecycle is **not proof** of a harmless race or a safe retry. Path preflights remain fail-closed. Local audit rows/digests remain unauthenticated for external effects or consent.

## Next plan / 今後の方針

1. Read Run829 exact HEAD CI jobs/logs, repair narrowly if needed; do not use queued CI as evidence and do not trigger equivalent duplicate runs.
2. Use disposable WAL-keeper vs last-connection-close and sequential vs concurrent child startup to distinguish `-shm` zero-link lifetime behavior in **Memory and ActionAudit**; no unsafe path retries or guard relaxation.
3. After independent GREEN, strengthen Memory retained row/event/ABA and COMMIT-UNKNOWN coherence, Planner durable UNKNOWN quarantine/terminal restoration, registry-bound exact PermissionGate and trusted-clock audit-before-disconnected-mock.
4. Continue privacy revocation/replay lifecycle, proactive restart and offline multimodal fixture contracts. No UI until explicit permission.

**Overall ARK/JARVIS NOT_PASSED.**

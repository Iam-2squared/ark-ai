# Run852 — disconnected SQLite admission and bounded persisted evidence

Status: **source/tests saved; exact-head CI pending**. These are local,
synthetic, opt-in fixtures with **no real tool/notification dispatch**,
no trusted approval issuer, no independently authenticated storage root,
and no exactly-once external effect.

## Grounded work basis and changes

- Previous Run851 checkpoint HEAD:
  `54b8a3f7b488bab40d7521533d99b5fd1a6dbdad`.
  [Actions run #43466764546](https://github.com/Iam-2squared/ark-ai/actions/runs/43466764546)
  completed **GREEN all six** Windows/Ubuntu × Python 3.11–3.13 jobs
  (confirmed through actual job conclusions, not merely the run summary).
- **Atomic intent + preaction audit:** source
  [`2b9333f4`](https://github.com/Iam-2squared/ark-ai/commit/2b9333f4f7217d1ae2e9714d4bad84921544df6c)
  pins the SQLite module/connector and bounds both caller-supplied and
  absolute-normalized fixture paths before filesystem checks or connecting.
  [11 authored regression cases `ebc610d1`](https://github.com/Iam-2squared/ark-ai/commit/ebc610d110d1f2ae72a7104e1673b586382a7fb9)
  cover 4 mutations × create/reopen, overlong absolute/relative paths,
  and successful non-authorizing restart.
- **Proactive due reservation:** source
  [`0781114e`](https://github.com/Iam-2squared/ark-ai/commit/0781114e9ed4e19605a7c29e92a3befd0cb54cdb)
  pins storage connector, schema domain, input grammar and numeric capacities.
  A read-only SQL COUNT + typeof/length preflight rejects too many rows and
  oversized/nontext identities **before Python hydrates persisted contents**.
  [15 authored regression cases `7bf4a34a`](https://github.com/Iam-2squared/ark-ai/commit/7bf4a34a46b3b3aff11682bfabb8ecb346b188ee)
  include pre-open drift, oversized text/BLOB persisted rows and valid restart.
- **Disconnected WRITE slot reservations:** source
  [`a2ad37d4`](https://github.com/Iam-2squared/ark-ai/commit/a2ad37d49e1422cf740a05160567a98ab578710c)
  similarly pins SQLite module/connector and count/batch budgets, bounds
  identifier lengths ahead of regex, and preflights SQL row count/type/width
  before Python hydration of the hash-chain rows.
  [17 authored regression cases `70948f07`](https://github.com/Iam-2squared/ark-ai/commit/70948f073bd547ffdd067933b52e65643c9a2e04)
  include 8 create/reopen drift cases, 5 corrupted persisted row cases,
  3 oversized caller identity cases and 1 valid non-dispatching restart.

**43 authored regression cases** across three new isolated test modules;
this is the test count, **NOT a confirmed 43 PASS result**. The changes
preserve each existing SQLite DDL, digest chain, read-only restart decision,
rejection of stale retained witnesses, and all explicit non-authority flags.

## CI at initial report composition

- Previous exact checkpoint `54b8a3f7`: [#43466764546](https://github.com/Iam-2squared/ark-ai/actions/runs/43466764546)
  **GREEN 6/6** (older HEAD only).
- Atomic source `2b9333f4`: [#43476369050](https://github.com/Iam-2squared/ark-ai/actions/runs/43476369050)
  **IN PROGRESS**; due source `0781114e`:
  [#43476606139](https://github.com/Iam-2squared/ark-ai/actions/runs/43476606139)
  **IN PROGRESS**; WRITE slot source `a2ad37d4`:
  [#43476840800](https://github.com/Iam-2squared/ark-ai/actions/runs/43476840800)
  **IN PROGRESS**.
- Atomic tests `ebc610d1`: [#43477133516](https://github.com/Iam-2squared/ark-ai/actions/runs/43477133516)
  **IN PROGRESS**; due tests `7bf4a34a`:
  [#43477262116](https://github.com/Iam-2squared/ark-ai/actions/runs/43477262116)
  **QUEUED**; WRITE tests `70948f07`:
  [#43477389207](https://github.com/Iam-2squared/ark-ai/actions/runs/43477389207)
  **QUEUED**.

These status labels are observations at report creation, not immutable
outcomes. No duplicate manual CI workflow was launched. The report/checkpoint
commits themselves trigger automatic CI: verify their **own** exact HEAD
before claiming GREEN. No local full pytest/Ruff was executed.

## Remaining safety boundaries / independent audit

- SHA-256 chains and local in-process function pinning **do not authenticate
  user consent**, prevent tampering by a hostile interpreter, or attest a
  rollback-resistant clock or physical storage identity.
- A lexical `lstat` preflight and subsequent SQLite open are **not atomic
  descriptor custody**. A concurrent rename/replacement can still race.
  Existing Memory/ActionAudit `-shm` last-close/link-count anomalies remain
  unresolved, so no such guard is relaxed or bypassed.
- The Memory store's `_connect` and `_connect_readonly` still use
  separately resolved SQLite pathnames after their lexical custody preflight.
  This is a **read-only source audit observation** only, not a remediation,
  permission to mutate a frozen V1 contract, or proof that such a race occurred.
- Local slot/atomic rows are **not durable PermissionGate one-shot approval
  tokens**. `PermissionGate._consumed_tokens` remains per-process.
  No automatic replay after an uncertain commit/exit, tool execution,
  real scheduler notification or physical-PC access.

## Next plan / 今後の方針

1. Inspect the exact newest branch/PR HEAD and six CI job conclusions,
   repair any concrete failure with minimal semantics-preserving changes.
2. Continue disposable two-process WAL/SHM last-close forensics, including
   Memory/ActionAudit held descriptor vs pathname identity comparison.
3. Strengthen Memory COMMIT-UNKNOWN manual reconciliation and Planner
   persistent UNKNOWN/terminal quarantine without changing frozen evidence.
4. Only after exact-head GREEN and reviewed consent provenance, progress toward
   a reversible **disconnected Mock** Registry/Permission/Audit integration.
5. Keep PR #5 protected Draft/unmerged and PR #9 paused Draft/unmerged;
   no frontend, paid/external compute, protected final V2 evaluation,
   Candidate generation/promotion or main merge.

# ARK AI Run869 — Non-UI SQLite proposal, scheduler, atomic pre-action, READ admission

**Source basis:** Run868 checkpoint `2c9e5c328c7f8f94b2ef80eae1979570a4449351` on `research/jarvis-foundations` (Draft PR #8). This is a synthetic, disconnected security-hardening report; it does not certify ARK/JARVIS PASS, independent provenance, physical-PC behavior, or authority to execute a tool.

## Four independent coherent non-UI source/test packages (36 synthetic cases authored)

| Package | Source commit | Test commit | Cases | Exact behavioral boundary |
| --- | --- | --- | ---: | --- |
| Proposal SQLite store | `3111873fc7f51af788fbf1a4fee67eae874ddcf4` | `e731b1c290d29aa1328f6045f88f9e57fa104374`; portability fix `85060a92287fcc054a005a7aa111a031a02a5768` | 12 | Reject NUL/native overbudget SQLite main/-journal paths before lstat, reject >512 stored rows, BLOB/Unicode-false-width identifiers, digests and oversized states before Python row hydration; valid proposal lifecycle/restart retained |
| Schedule quarantine ledger | `45252e0b4b62acf3d64d3b359651c72865311864` | `9feb2c0445024d4f9a53ddda961a76e31398f494` | 5 | Persisted quarantine occurrence and chain identities use UTF-8 `length(CAST(... AS BLOB))`, not Unicode codepoint counts; expiry/clock policy unchanged |
| Atomic pre-action intent+audit | `115d9298100beb91ce9214ea1c9660e718d2f9c3` | `68cd219379539278d78dc4aa2132dc2d6f4ef998` | 7 | Five stored intent and audit identity/digest widths checked as native bytes; retain one-store atomic intent/audit and denial-only receipts |
| READ journal | `17ff14d7216c98a18f91c682da20264d7b0c61e3` | `d6bcdd1c06d781ff2ce8888fe277ec822b9a5e71` | 12 | Native SQLite path limits, marker TEXT byte admission, receipt row COUNT<=128 and exact storage class/encoded width before bounded Python hydration; no backend dispatch |

All changes are additive input validation. Existing database schema, state-transition semantics, CAS rules, fixed authority-denial properties, V1/V2/Local UI/Launcher evidence and frozen contracts are unchanged. These predicates operate on SQLite values **inside one existing local transaction**, not authenticated disk provenance, replay permission, independently witnessed action history or cross-store atomicity.

### CI and observed regression

- Run868 exact checkpoint `2c9e5c328c7f8f94b2ef80eae1979570a4449351`: [run #43583826579](https://github.com/Iam-2squared/ark-ai/actions/runs/43583826579), **6/6 GREEN**, Windows/Ubuntu Python 3.11–3.13. This evidence applies only to that preceding HEAD.
- New proposal test HEAD `e731b1c290d29aa1328f6045f88f9e57fa104374`: [run #43587076099](https://github.com/Iam-2squared/ark-ai/actions/runs/43587076099), Ubuntu job **FAIL**. The failure was a **test itself** calling `Path.exists()` on an intentionally longer-than-filesystem-limit name (`OSError: ENAMETOOLONG`), after the intended source refusal succeeded. On Ubuntu Python 3.12, the job recorded **15,472 PASS, one FAIL and one SKIP**. The test was fixed at `85060a92287fcc054a005a7aa111a031a02a5768` by asserting that its disposable parent directory remained empty, never stat-ing the invalid child. No bypass of native-path denial.
- Scheduler test [#43587134656](https://github.com/Iam-2squared/ark-ai/actions/runs/43587134656) observed Ubuntu 3.11/3.12 FAIL for the **same inherited earlier test**, not evidence of a scheduler regression. It predates the portability fix.
- Other automatic source/test checks: atomic pre-action [#43587251787](https://github.com/Iam-2squared/ark-ai/actions/runs/43587251787), READ journal [#43587394580](https://github.com/Iam-2squared/ark-ai/actions/runs/43587394580), corrected latest source/test [#43587511171](https://github.com/Iam-2squared/ark-ai/actions/runs/43587511171). These were QUEUED/IN PROGRESS at earlier observations: **NO latest exact-head six-job GREEN is claimed**.
- Four changed source blobs and four new test blobs re-read from GitHub: all lines <=100 chars. No local full pytest/Ruff, no machine GGUF check, no manual duplicate workflow dispatch.

### Remaining gaps and hard safety boundaries

SQLite WAL/SHM final-client-close and path-to-open races remain; receipt hashes do not provide an independent custody anchor, trusted approval or clock, exactly-once external effects, cross-file atomicity, nor a resolved COMMIT-UNKNOWN disposition. Synthetic READ/WRITE reservations remain **inert**; every real permission and backend access remains blocked. PermissionGate/ToolRegistry/mock executor integration depends on verified lower-level exact-head tests.

No new UI/frontend development (PR #9 untouched), no paid API/GPU/training/Candidate work, no protected V2 final evaluation, promotion, real-world action, destructive operation, credentials, new account connections or main merge. PR #5/#8/#9 remain Draft/unmerged.

## Next plan / 今後の方針

1. Resolve latest-head six-job CI and any legacy-compatibility FAILs minimally; do not inherit GREEN from a prior SHA or duplicate workflows.
2. Investigate Memory/ActionAudit WAL/SHM close and COMMIT-UNKNOWN with independent-process disposable fixtures, keeping uncertain writes non-replayable.
3. Verify Planner durable UNKNOWN lineage, terminal propagation and Memory CAS/expiry coherent snapshots, including restart.
4. Continue Personal Context revocation/expiry and scheduler/observation offline data minimization independently of in-flight CI.
5. Only after exact-head GREEN connect immutable registry-bound Tool identity, exact PermissionGate, durable occurrence and trusted audit-before-action to **mock-only** execution; no external side effect.

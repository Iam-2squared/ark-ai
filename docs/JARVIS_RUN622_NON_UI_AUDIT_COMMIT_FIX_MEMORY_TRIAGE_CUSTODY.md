# Run622 — Non-UI audit COMMIT-boundary fixture repair and manual-only Memory constructor custody

**Scope:** Draft PR #8 `research/jarvis-foundations` only. **Work-basis HEAD:** `23f4b52d0f39b10e0081d33e0dde3a33b41bf2e5` (Run621 checkpoint). No main merge, UI/PR #9 modification, frozen-contract change, external action, paid service, Candidate, or protected evaluation opening.

## Package A — repair real ActionAudit COMMIT-boundary tests

- Previous exact Run621 checkpoint CI [#41954599679](https://github.com/Iam-2squared/ark-ai/actions/runs/41954599679) **FAIL in six jobs**. The Ubuntu 3.12 job reported **8 failures, 8,659 passes, one skip**. Seven old post-COMMIT mutation cases had replaced `ActionAuditEvent.__init__`, which new constructor-custody protection correctly rejects *before SQLite*. A child-process hard-exit test similarly swapped the entire event class, preventing its supposed post-COMMIT exit.
- `tests/test_action_audit_pre_post_commit_custody_run425.py` now uses a proxy around the native SQLite connection context. Its `__exit__` delegates to sqlite3's actual COMMIT and **only afterward** induces path/call identity drift or a one-shot event field mutation on receipt validation read. The original protected `__init__` remains unchanged. Seven parameterized cases continue to demand a refusal *after COMMIT*, exactly one retained row, and no automatic retry. This exercises both persistent-row preservation and post-return authenticity, rather than weakening the earlier constructor guard.
- `tests/test_hard_exit_audit_privacy_run436.py` uses a child-process connection proxy that calls the native `sqlite3.Connection.__exit__` to finish the COMMIT **before** invoking `os._exit(52)`. The pre-COMMIT hard exit still occurs before native `__exit__`. It then reopens the disposable SQLite file and checks 0 versus 1 retained rows. No real executor or private data.
- Intermediate test-fix CI [#41957247451](https://github.com/Iam-2squared/ark-ai/actions/runs/41957247451) **six FAIL at Ruff E501** on a 102-character test line (not pytest semantics). [#41957623280](https://github.com/Iam-2squared/ark-ai/actions/runs/41957623280) also failed that same E501. The exact line was wrapped in an ordinary guarded Contents commit `5edecbb6bfea2fb98aafddcc48e8ba1fc9ff0535`; final pytest is not yet proven.

## Package B — retained Memory alignment constructor authority

- `src/ark/memory/sqlite_alignment_retained_review.py`: preserve import-original `RetainedMemoryAlignmentComparison.__init__` and verify its identity along with the original false-only authority descriptors, prior to SQLite access and after read/digest callbacks. No v1 SQLite schema, data or actual user Memory is modified.
- `tests/test_memory_retained_alignment_constructor_custody_run622.py`: **five authored pytest cases** (three constructor replacement phases, counterfeit replacement class, and normal deny-only baseline). Injected constructor must have zero invocations; normal no-append observation remains unchanged and non-disclosing.

## Package C — COMMIT-UNKNOWN Memory triage constructor authority

- `src/ark/memory/postcommit_uncertainty_review.py`: pin the import-original `MemoryCommitTriage` class and its `__init__`. Include these identity checks in the existing retained-token/metadata/source epoch checks. Compute the detached digest, revalidate the complete epoch, then construct the read-only receipt and revalidate afterward. This closes the callback window after SQLite close or digest computation. It neither attributes an ambiguous COMMIT nor permits retry.
- `tests/test_memory_commit_triage_constructor_custody_run622.py`: **five authored pytest cases**, including preinstalled constructor, reentrant snapshot, reentrant connection close, result-digest callback substitution, and normal manual-only receipt. All use disposable local SQLite data. A matching record is not a proof of who wrote it.

## Validation and safety interpretation

- **Ten authored pytest cases**, **eight legacy parameterized cases repaired** (seven receipt mutation cases and one child-process post-COMMIT case); these counts are *test definitions*, not a claim of a successful local run.
- GitHub normal Contents API changes, observed branch HEAD before each write; no raw Git objects, force-push, workflow re-dispatch, or concurrent modification of PR #9.
- No local pytest/Ruff evidence: the execution container could not resolve `github.com` when attempting `git ls-remote`. Use GitHub Actions exact-HEAD evidence as the decisive remote test result.
- CI for pre-report corrected source/test HEAD `5edecbb6bfea2fb98aafddcc48e8ba1fc9ff0535`: [#41957950284](https://github.com/Iam-2squared/ark-ai/actions/runs/41957950284) **IN PROGRESS when the report was prepared**. A later CI outcome must not be inferred from earlier jobs.
- **Boundaries:** frozen V1/V2/Local UI/Launcher evidence unchanged; PR #5/#8/#9 Draft/unmerged; UI paused; no paid/external GPU/API, real Candidate, V2 protected evaluation, ToolBackend, notifications, credential changes, main merge, or manual triage authorization. Local SQLite row/event/hash equality is never independently authenticated human consent, trusted clock, durable issuer custody, or exactly-once external side effects. All ambiguous Memory WRITE/COMMIT cases remain manual-only, never automatically replayed.

**Next:** establish final exact-HEAD Ubuntu/Windows × Python 3.11–3.13 CI; fix any real regressions without loosening guards, then advance Planner durable crash recovery and registry-bound audit-before-*mock*-action once dependencies have exact-head GREEN.

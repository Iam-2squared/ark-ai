# ARK AI Run908 — disconnected restart custody, occurrence frontier, and CI recovery

**Scope:** Free-only, non-UI, disconnected synthetic foundations. **Overall ARK/JARVIS: NOT_PASSED.** No new frontend work, real user data, live ToolBackend, external compute, training, human authorization, Candidate, protected evaluation, physical PC operation, or main merge.

## Exact work basis and packages

Initial work-basis / Draft PR #8 HEAD: `5b5deaf0fff1b0b9577b7084c805637cc1c7fa4e`.

1. **Run907 CI regression repaired without changing contract behavior.** Prior exact checkpoint [CI #43777100411](https://github.com/Iam-2squared/ark-ai/actions/runs/43777100411) **FAIL 6/6** at Ruff I001 in `tests/test_offline_text_preencode_budget_run907.py`; pytest never ran. Intermediate attempts [`919b3ec8`](https://github.com/Iam-2squared/ark-ai/commit/919b3ec8b76ab50ced0a2126b8631306c4f7e5e4) and [`0c5947f5`](https://github.com/Iam-2squared/ark-ai/commit/0c5947f5a23e2ce11c48069367aeb316845bc49f) did not repair I001. The actual [fix `65517523`](https://github.com/Iam-2squared/ark-ai/commit/65517523a2fa90281a8da9fbde066e698efbd212) removes an extra blank line between the last import and module constants, consistent with other passing tests. No underlying test assertions or production behavior changed. On [CI #43782773658](https://github.com/Iam-2squared/ark-ai/actions/runs/43782773658), **Ruff PASS in six environments**, but pytest and end-to-end CI were still **IN PROGRESS at report time**, not green certification.
2. **Retained synthetic occurrence frontier admission:** [source `7852797e`](https://github.com/Iam-2squared/ark-ai/commit/7852797eb631dd6e173eb34ff01a5fe92919fd89), [9-case regression `6b8af10e`](https://github.com/Iam-2squared/ark-ai/commit/6b8af10ef91fed3cc414f826295141598d9391c9). Reject retained SHA-256 values unless exact 64 characters **before regex inspection**, including huge strings, non-ASCII, NUL and reflected str subclasses. Test against missing SQLite confirms no storage creation on malformed retained evidence; a valid empty ledger remains read-only, inert, recheckable. Local hash is *not* independently authenticated approval, an append-proof, or external effect.
3. **Scheduler COMMIT-UNKNOWN review instance custody:** [source `ff1abbff`](https://github.com/Iam-2squared/ark-ai/commit/ff1abbff5486c1363492899c87f9702b6e290f3f), [6-case regression `91387f05`](https://github.com/Iam-2squared/ark-ai/commit/91387f059df021bfa0adb60727d9f118fdbb3f1f). Read-only schedule quarantine review now admits only the original instance's `_path` and `_epoch` state fields and invokes the **captured class `_open`** instead of a caller-shadowable `ledger._open`. Recheck the exact instance shape/path/policy epoch at each review boundary. Synthetic forged method or extra field must be denied *before* execution. Valid UNCHANGED, LOCALLY_QUARANTINED and restart PREEXISTING local states remain distinct; all manual-only and non-replayable. No schedule auto-dispatch or clock/consent authority created.

**15 regression cases authored in two independent core packages; none is claimed six-job PASS before final exact HEAD CI concludes.** No manual duplicate workflow reruns, no raw Git-object writes, no force push, no UI changes.

## Strict boundaries and unresolved failures

- Frozen V1/V2/Local UI/Launcher contracts/evidence unchanged; protected V3 Draft PR #5 and paused UI Draft PR #9 remain Draft/unmerged; main is unchanged.
- All edits on `research/jarvis-foundations` / Draft PR #8 through normal GitHub Contents API, re-reading HEAD before each write. Synthetic tests do not verify independent path custody, trusted source hashes, user permission, identity or exactly-once external effects.
- Existing Windows/Ubuntu SQLite WAL/SHM last-close cross-process contender race remains **UNRESOLVED**, with a durable winner and denied peer never interpreted as dual success or a safe automatic retry.
- Planner cross-store COMMIT-UNKNOWN, Memory event/CAS provenance, trusted-clock audit-before-action, physical offline GGUF gate and protected V3 human approvals remain **BLOCKED/NOT_PASSED**.

## Next plan / 今後の方針

1. Finish exact HEAD six-environment CI and fix any new semantic defect via normal permitted path; never extrapolate older GREEN to latest HEAD.
2. Compare disposable WAL-keeper vs last-close contender behavior without weakening strict sidecar denial.
3. Strengthen Planner UNKNOWN, Memory CAS/expiry/event-integrity independently, then connect immutable registry, exact PermissionGate and inert mock execution only after exact dependency GREEN.
4. Advance privacy-safe Personal Context, proactive/observation backend contracts and free V3 identity/path/reproducibility checks with no protected evaluation or compute.

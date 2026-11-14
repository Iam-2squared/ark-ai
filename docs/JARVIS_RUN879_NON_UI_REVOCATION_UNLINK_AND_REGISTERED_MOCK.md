# Run879 — Privacy sidecar unlink preflight and registry-bound mock-only authorization

Both packages are local-first, reversible fixtures, **not** consent or external action permission.

## Observed concurrency failure / decision

After correcting the Run878 proactive first-bootstrap bug, the unrelated [Run879 report commit CI #43634279883](https://github.com/Iam-2squared/ark-ai/actions/runs/43634279883) reported a **single Ubuntu Python 3.12 failure**, while Ubuntu 3.11 was GREEN at investigation. In `tests/test_privacy_revocation_cross_process_run425.py`, a losing synthetic revoker reported `LOSER_REJECTION_DETAIL: 'unsafe revocation SQLite sidecar'` instead of the test's required `already revoked`. This same category had occurred historically; actual durable row state cannot be inferred from a failed caller response.

`_check_local_revocation_path` was using a single `Path.lstat()` inode snapshot and rejecting any sidecar `st_nlink != 1`. During another SQLite process's final rollback-journal close, a regular inode that was successfully located by pathname can become already-unlinked (`st_nlink == 0`) before the inode is inspected. That observation is an ambiguous path race, **not** evidence of an alias or permission to retry any protected action.

## Narrow, fail-closed source repair

At exact branch HEAD `2e4d09ddff311d695a54a6e196c56f04bc760a7b`, updated only `src/ark/personal_context_revocation_review.py` via normal GitHub Contents API; source prior blob `ca955d538fe16397f9740e1114b81b079363e49f`, new blob `77e78b66dabfeda7b4297bebcf4cfd8af85066b1`, commit `302b5a56ebb49c217b1843f17693bee4873d121c`.

The preflight may do **one fresh pathname lstat only when the FIRST result is already-unlinked AND regular AND a main SQLite file already existed**. If that pathname vanished, its unlinked inode cannot be adopted; if its new inode is single-link regular, normal validation applies. An orphaned sidecar, symlink, hardlink, nonregular or still-unlinked inode remains denied without an alias fallback. No repair, deletion, migration or automatic replay occurs. The source still documents that pathname preflight is not atomic dirfd/open-handle custody or independently authenticated consent.

Added `tests/test_privacy_revocation_transient_unlink_preflight_run879.py`, blob `d70001d82392f693a95d1d28110ed54839b4e784`, commit `97883e9c4580272abd6a933ff7d365b838a96427` with **8 authored synthetic cases**: transient disappeared files for each -wal/-shm/-journal suffix (3), safe new regular inode/unsafe hardlink/unsafe symlink (3), permanently unlinked refusal (1), orphan rejection without retry (1). Existing alias and cross-process tests remain in place. These authored tests must not be described as CI-PASS before exact HEAD GREEN. Continued intermittent failure would still be a blocker, not justification to loosen the privacy deny.

## Independent ToolRegistry / PermissionGate / mock-journal boundary

Another work package saved `tests/test_registered_gate_mock_preaction_run879.py`, blob `35571e0a238bb231fd30f7b176a3bb447aec2e12`, commit `2e4d09ddff311d695a54a6e196c56f04bc760a7b` with **3 authored tests**. They combine an exact-scope `PermissionGate.authorize_registered`, registry-bound WRITE identity and existing `run_synthetic_mock_cycle` on **temporary fake SQLite**: a success marker has durable audit-before-mock but never invokes the registered backend; a mismatched grant never mutates any store; and a fresh process-local gate cannot override a Planner RUNNING→UNKNOWN journal, durable occurrence and audit after injected post-audit stop. The gate's in-memory token-spend is **not** durable exactly-once approval. The three stores are not cross-store atomic and neither the synthetic mock marker nor any local receipt proves a real-world action.

## Validation status / constraints

- Prior complete checkpoint `a493b60c3c7dc8142cf209f0e4a2c39b6ab17aed` [#43629239918](https://github.com/Iam-2squared/ark-ai/actions/runs/43629239918) **FAIL 6/6** from proactive bootstrap regression; see companion `JARVIS_RUN879_NON_UI_PROACTIVE_BOOTSTRAP_CI_REPAIR.md`.
- Proactive fix source `ab0b1116d0fe35a7568125fc5465249e021588c5` [CI #43633846086](https://github.com/Iam-2squared/ark-ai/actions/runs/43633846086) had Ubuntu 3/3 GREEN, Windows 3 in progress at prior observation.
- Registered gate/mocked preaction test commit `2e4d09ddff311d695a54a6e196c56f04bc760a7b` [CI #43634553642](https://github.com/Iam-2squared/ark-ai/actions/runs/43634553642) remains subject to exact 6-job validation.
- Privacy repair `302b5a56ebb49c217b1843f17693bee4873d121c` [CI #43634878508](https://github.com/Iam-2squared/ark-ai/actions/runs/43634878508) and new privacy tests `97883e9c4580272abd6a933ff7d365b838a96427` [CI #43634936965](https://github.com/Iam-2squared/ark-ai/actions/runs/43634936965) were in progress/queued at creation; no PASS evidence yet.
- Existing frozen V1/V2/Local UI/Launcher schemas and evaluations untouched. Protected V2 final evaluation closed, PR #5 Draft gated, PR #9 paused UI Draft/unmerged, PR #8 Draft/unmerged. No real backend call, Candidate training/promotion, private user file, paid compute/API, new secrets/account, physical PC operation or main merge.

## Next

1. Verify the above exact-HEAD CI results and specifically both Windows and Ubuntu cross-process privacy tests. If the flake persists, retain the actual error and re-check path races; **never** weaken symlink/hardlink denial or grant replay from UNKNOWN.
2. Prove independently retained privacy witnesses and Memory/ActionAudit COMMIT-UNKNOWN before real integration, not by green synthetic fixtures alone.
3. Continue Planner restart terminals, Memory CAS/expiry, durable exact authorization and auditable time with mock-only backends.

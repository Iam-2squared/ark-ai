# Run734 — Non-UI local path-custody preflight across READ, Planner and Audit

**Scope:** Draft PR #8 `research/jarvis-foundations` only. **No UI work, actual tool execution, external GPU/paid APIs, Candidate training, protected V2 evaluation, approval, main merge or destructive cleanup.** ARK/JARVIS/V3 **NOT_PASSED**.

## Basis and evidence

- Exact initial work-basis HEAD: `4f3ab54a7cedec9e2e7ae3dc20cf0072fee52420`; this Run733 checkpoint head is confirmed **6/6 GREEN** in Windows/Ubuntu Python 3.11–3.13 by [GitHub CI #42585499234](https://github.com/Iam-2squared/ark-ai/actions/runs/42585499234).
- Three distinct source hardening packages with matching synthetic regression tests, saved via **normal GitHub Contents API**. Each write was preceded by an actual PR head re-read. All paths remain outside the paused UI and frozen evidence.
- **No local pytest** was run: the GitHub-hosted CI is the available executable verification; newly authored tests must not be called PASS until a matching full-head run finishes.

## Package A — write-once READ input artifact

- Source commit [`8cbfd211`](https://github.com/Iam-2squared/ark-ai/commit/8cbfd211575017b2a6a46b8289e56df5170f20be) adds a shared pre-I/O path preflight in `src/ark/agency/disconnected_read_input_manifest.py` for both create and load: exact `str`/concrete `Path`, absolute/no `..`, every ancestor `lstat` is a real directory (no symbolic grandparent), leaf symbolic path denied.
- This closes a local alias path missed by final-component `O_NOFOLLOW`. The original `O_EXCL`, file and directory fsync where available, post-publication byte readback, independently retained hash and deny-only result remain unchanged. It does **not** authenticate the file or defeat concurrent ownership-controlled rename races.
- [`552e56b`](https://github.com/Iam-2squared/ark-ai/commit/552e56b23267355738b587981f4f10eec0c75a3a) adds `tests/test_detached_read_manifest_ancestor_custody_run734.py`: **10 parameter-expanded cases** (normal nested path, symbolic grandparent create/load, lexical traversal and relative paths, nondirectory parent, malicious pathlike callback without invocation).

## Package B — Planner SQLite transition journal

- [`e9a26d2`](https://github.com/Iam-2squared/ark-ai/commit/e9a26d272ad8508734c5a9762b656576139b733e) adds `_require_safe_journal_path()` ahead of *both* SQLite bootstrap and read/write connections. The journal refuses relative/parent-traversing sources, symbolic ancestors/leaf, directories-as-databases and nlink != 1. Existing no-implicit-recreate, source-epoch checks, event hash replay, CAS, `RUNNING` ambiguity and no dispatch remain intact.
- [`c4ea4ca`](https://github.com/Iam-2squared/ark-ai/commit/c4ea4ca20f25e12471281d3bab3857795062f51e) adds `tests/test_planner_journal_path_ancestry_run734.py`: **8 cases** for ordinary nested durable `RUNNING` recovery, ancestor redirects, lexical/relative escape, nondirectory ancestor, directory and hardlinked database denial.
- Only process-local path preflight is asserted, not a sandbox, cross-file atomicity, external source authentication, or automatic replay rights.

## Package C — Action audit SQLite path custody

- [`9294975`](https://github.com/Iam-2squared/ark-ai/commit/92949754ced957169d4b1dc9189e866e2c0b291c) adds an ancestor/leaf `lstat` guard **before directory bootstrap** and on every subsequent writer/read-only SQLite connection in `src/ark/agency/audit.py`. The existing deliberate creation of new parent directories is kept, but not through an existing symbolic ancestor. Rejects `..`, non-regular and multiply-linked database paths, and untrusted custom pathlike objects before evaluating their callback.
- [`0669380`](https://github.com/Iam-2squared/ark-ai/commit/066938031ba44e780d8031b6e8155e4b49332bb4) adds `tests/test_action_audit_path_ancestry_run734.py`: **10 cases** including normal nested parent bootstrap and event reopening, parent symlink redirect, late leaf symlink append/read, lexical traversal, hardlinked audit source, nondirectory parent and no hostile `__fspath__` callback.
- This is a *local* audit-evidence safeguard. Audit SQLite remains a distinct store; a timestamp or audit record is **not** a trusted clock, consent, independent provenance or proof of an external side effect.

## CI separation and irreversible boundaries

- Previous exact Run733 checkpoint [CI #42585499234](https://github.com/Iam-2squared/ark-ai/actions/runs/42585499234) **GREEN (6/6)**.
- Intermediate Run734 CIs were spawned by normal PR pushes: [#42589503817](https://github.com/Iam-2squared/ark-ai/actions/runs/42589503817), [#42589955010](https://github.com/Iam-2squared/ark-ai/actions/runs/42589955010), [#42590257304](https://github.com/Iam-2squared/ark-ai/actions/runs/42590257304), [#42590402160](https://github.com/Iam-2squared/ark-ai/actions/runs/42590402160). Their outcomes are HEAD-specific and cannot prove later source/test commits. **The final audit additions and checkpoint require their own exact-head CI verdict; no 28-case all-platform PASS claim before that evidence.**
- CI overlap was used for read-only free V3 guard audit of Draft PR #5: inspected `docs/v3/PRE_PAID_COMPUTE_GATE.md`, preflight and training CLI, confirmed separate preflight/training authorization plus unresolved input, legal, hardware, budget and approval blockers. PR #5 was not edited, unlocked or run.
- V1/V2/Local UI/Launcher frozen contracts and evidence unchanged. Draft PR #5 and paused Draft PR #9 untouched. No raw Git object path, force push, migration, auto-delete, automatic WRITE retry, credential/API spend, real sensor or private-user data.

## Next safe work

1. Complete exact latest `research/jarvis-foundations` Windows/Ubuntu Python 3.11–3.13 CI; inspect any failed logs and fix narrowly without relaxing safety or confusing earlier GREEN with final GREEN.
2. Consider descriptor-relative `dirfd`/no-follow and platform-specific file identity evidence as **separate, reversible** follow-on design; current preflight is explicitly subject to path replacement races.
3. Continue Memory CAS/ABA and manual-only COMMIT-UNKNOWN reconciliation; Planner READ manifest/witness restart; one-shot registry-bound authorization and audit-before-action into **mock/disconnected only**.
4. Preserve User UI stop, Draft PR #5 approval gate and protected/frozen evidence.

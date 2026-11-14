# ARK JARVIS/V3 — Run478 disconnected READ journal, atomic Memory epoch and local V3 provenance

Status: technical evidence for independently reversible, **free-only / disconnected** work. This is not a JARVIS completion report, real Tool outcome, independently authenticated consent, trusted clock, V3 PASS, human approval or license resolution.

## Work basis and preservation

- Canonical PR #8: `research/jarvis-foundations` (Draft/unmerged), basis `4575adfdf7442d322814e6b7478d3c5d6d04d7fe`; source+test head `ec2fb3d6dbc6904ad77ee776ca7c6fd401ab92e4`.
- V3 PR #5: `research/v3-learning-evaluation` (Draft/unmerged), basis `ede4ccffb10e381291500bea522e0067390520de`; source+test head `da3d18994af5dcc74f93cbab99095ba2876ffe6d`.
- Frozen V1/V2/Local UI/Launcher evidence, Memory v1 DDL, protected V2 final evaluation and frozen V3 experiment contract untouched. Neither PR merged.

## Four work packages / 48 authored pytest cases

1. **Request-bound fixture READ -> detached CAS journal bridge (16 cases)**. New `src/ark/agency/disconnected_read_receipt_bridge.py` (blob `d1f569fe4ad87d4e3c143f8b1f9f6b9648c2b5ac`), `tests/test_disconnected_read_receipt_bridge_run478.py` (`264df7cf1320650f6aed749ac5e2074562bf4df9`). Recomputes the exact memory-only fixture and its per-request binding before preparing a frozen v1 ReadReceipt. Optional caller-opened SQLite journal append uses existing CAS, never retries a possibly committed append; restart verification uses a separately retained witness. The journal row **does not contain** the extra request-bound fingerprint and cannot independently prove its custody; no ToolBackend, authenticated grant, or real external result is involved.
2. **One-transaction Memory row/event epoch (18 cases)**. New `src/ark/memory/atomic_epoch_review.py` (`4fcc91a65ae6dda3dd3b17888ddc75d683bbc758`), `tests/test_memory_atomic_epoch_review_run478.py` (`3b7e838344a1d4b621a12ed3366bc54fd709ac4e`). Uses an existing read-only SQLite file and one pinned read transaction to observe bounded row/event metadata across ordered same-owner scopes. The first SELECT anchors the snapshot before the supplied clock callback; the returned digest omits plaintext and denies disclosure/dispatch/writer-provenance authority. Checks schema, persisted row/event validity, counts and per-scope tips. This is atomic **within one SQLite database only**; it does not authenticate writers, history outside the selected bounded window, or other stores.
3. **V3 local file identity read-epoch and alias guard (8 cases)**. `src/ark/learning/identity.py` (`eca613513d6a27e40fd0575c59e3426031ab9e5f`), `tests/v3/test_local_identity_file_epoch_run478.py` (`372a9480a90a6f60314401f379a0920ae73d38a0`). Rejects path parent traversal, symbolic ancestors, hardlink aliases and file changes detected between pre/post hash stat comparisons; output manifest shape unchanged. A pre/post metadata check **does not guarantee** race-proof file-handle custody or defend against hostile writers that can manipulate metadata. Only test fixture bytes used; no model files/GPU started.
4. **V3 pre-approval packet input-epoch custody (6 cases)**. `src/ark/learning/authorization.py` (`c0152e84947e9e43456d05317f8edaaaa0169cb0`), `tests/v3/test_authorization_packet_epoch_run478.py` (`fd8d7a6a62934cb2b6deb2ac0841e36000808239`). Pins the complete original execution snapshot across validation, core hash, nested copies and final packet hash; copies review sections without aliasing. Prevents a callback from silently moving budget/identity/approval fields while assembling the user-review packet. It **never authorizes preflight/training** and changes no immutable experiment defaults.

All eight file blobs were independently re-fetched from the intended branch after normal GitHub Contents API updates. Authored test counts describe pytest definitions/parameterizations, not standalone local PASS. Local whole-repository pytest/Ruff was not run: container GitHub DNS clone failed. GitHub Actions is the actual test runner; every status must be attributed to its own exact HEAD.

## CI observations at technical-note creation

- Prior PR #8 checkpoint `4575adf...`, workflow #1587 / `41045591097`: completed success; six Windows/Ubuntu Python 3.11–3.13 jobs independently inspected GREEN.
- PR #8 new source/test `ec2fb3d6...`, workflow #1591 / `41050781096`: Ubuntu Python 3.11/3.12/3.13 GREEN, Windows three jobs still in progress at last check. No six-job PASS claimed yet.
- Prior PR #5 baseline `ede4ccf...`, workflow #1585 / `41044944974`: six jobs GREEN.
- PR #5 new identity head `82332c7...`, workflow #1593 / `41050997004`: completed SUCCESS at last run lookup; packet head `da3d189...`, workflow #1595 / `41051214897`: QUEUED. Do not substitute the earlier head's result for packet tests.

## Hard boundaries / next actions

No paid GPU/compute, paid API, account/credential, actual Candidate/weights, protected V2 evaluation, live Tool/OS/notification/camera/microphone operation, human review, promotion, destructive action or main merge. PR #5 and #8 stay Draft/open/unmerged.

Next: inspect exact PR #8/#5 CI job completions, correct only evidenced failures by normal Contents API, then advance Memory CAS/retained witness, Planner UNKNOWN WRITE restart quarantine, real-clock/audit-before-action **contracts** without real authority, and local privacy/observation/scheduler fixtures. The remaining real-world approvals/identities/compute ceilings and physical PC evidence remain blocked pending explicit user decisions.

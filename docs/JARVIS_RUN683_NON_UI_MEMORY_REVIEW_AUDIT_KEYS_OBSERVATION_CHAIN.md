# ARK AI — Run683 non-UI: dual-review digest, durable uniqueness, observation lineage

## Scope and work basis

FREE-ONLY, disconnected/mock-only work on Draft PR #8, branch
`research/jarvis-foundations`. Initial inspected work-basis HEAD:
`dc0e3103d312b950467584d7263d9371f973e2c0`.
Its automatic [CI #42357603412](https://github.com/Iam-2squared/ark-ai/actions/runs/42357603412)
was independently checked **COMPLETED GREEN (6/6, Windows/Ubuntu × Python 3.11–3.13)**.
All changes are isolated from main, frozen V1/V2/Local UI/Launcher evidence,
V3 PR #5 and paused UI PR #9.

## Packages

### A — Memory ambiguous-commit reconciliation SHA/JSON/domain custody

- Source `src/ark/memory/ambiguous_commit_pair_review.py`, commit
  `118406b998f6c9902f6eb3fe89b7b7f18a51180d`.
- Captures original SHA-256 module/function, JSON module/dumps function, and
  domain *object identity* at import time. Checks these in the existing
  `_require_original_review_carriers` guard **before** either SQLite child
  review/private row access and at every existing stability checkpoint.
- Test `tests/test_memory_dual_review_digest_custody_run683.py`, commit
  `93a07c342fc854b751a35794c0646346449d24b9`: **6 cases**, including
  equal-valued but replaced domain, a replaced module, and forged hash/dumps
  callbacks. Assert no callback or SQLite entry, normal deny-only result after
  monkeypatch restoration.
- No claim of authenticated writer, consent, trusted time or safe automatic retry.

### B — Durable mock WRITE reservation key independence across crash gaps

- Test `tests/test_offline_audit_crash_gap_double_key_collision_run683.py`,
  commit `54c86052117044ed213dd43c61c9bf15c38ee6ae`:
  **6 cases** covering 3 durable phase boundaries (reservation only, pre-action
  audit committed, linked audit committed) × 2 collision axes (reused token
  with new occurrence, reused occurrence with fresh token).
- Reopens all three disposable SQLite fixture stores; requires duplicate denial,
  unchanged audit/link snapshots, exactly one reservation and zero backend calls.
- This is a synthetic once-only reservation *guard*, not proven atomically
  exactly-once external execution, trusted audit time or authenticated approval.

### C — Closed observation-fixture chain hash/domain custody

- Source `src/ark/observation_fixture_chain_review.py`, commit
  `fb386f8b603da8c127546a0e318cc487daab9041`.
- Pins original hashlib module, SHA-256 implementation and domain object.
  Rejects substitutes at first reviewer guard, before inspecting caller-private
  envelope fields; rechecks through the existing per-envelope callback epoch.
- Reconciled old injection test without weakening source guards at
  `8e25340d868b004a9d6736d9c30fd8f7348b00b4`: now explicitly demands
  no execution of a substituted callback.
- Test `tests/test_observation_chain_digest_epoch_run683.py`, commit
  `fc6612428d169b794e000ffa6a50df48d83136eb`:
  **4 parameterized cases** for module, SHA-256, changed domain and
  equal-byte identity replacement; restored legitimate closed chain remains
  denial-only. No camera, microphone, image collection or UI change.

## Evidence and limits

**16 newly authored cases (6+6+4), one existing callback test adapted to
earlier fail-closed semantics, two guarded non-UI production modules.**
These are authored cases; **do not call them full-matrix PASS until the
corresponding exact-HEAD six-job CI finishes**.

Automatic PR CI run IDs observed during implementation:
- Source A: [#42360868183](https://github.com/Iam-2squared/ark-ai/actions/runs/42360868183)
- A + tests: [#42360898947](https://github.com/Iam-2squared/ark-ai/actions/runs/42360898947)
- B: [#42360939761](https://github.com/Iam-2squared/ark-ai/actions/runs/42360939761)
- Final C source+tests: [#42361110462](https://github.com/Iam-2squared/ark-ai/actions/runs/42361110462)

## Intermediate CI regression and narrow repair

[CI #42360939761](https://github.com/Iam-2squared/ark-ai/actions/runs/42360939761)
at the initial audit-test HEAD `54c86052117044ed213dd43c61c9bf15c38ee6ae`
reported Ubuntu Python 3.11/3.12/3.13 **FAIL**; Python 3.11 log:
**2 FAIL / 10,346 PASS / 1 SKIP**. Both FAIL were the
`linked`-phase cases: the new fixture used outcome
`synthetic_preaction_only`, while the untouched linker explicitly requires
`synthetic_audit_before_mock`. The tests were corrected **only** in
`a6423956ccc4c6f0f4b26ac17b7ead2ea06efac7`.
No synthetic audit source, actual permission check or early denial was relaxed.
The superseded FAIL is not evidence against the corrected exact HEAD;
automatic new-head CI must separately pass.

The automatic jobs may be in progress when this report is written; a
documentation/status commit creates a newer exact HEAD and a distinct CI.
Do not inherit GREEN from an ancestor. No duplicate manual workflow runs.

## Safety and prioritized next work

1. Confirm CI for the latest checkpoint-result HEAD, all six jobs. If a
   regression exists, repair by normal Contents update, not raw Git bypass.
2. Extend Memory CAS/ABA/expiry/COMMIT-UNKNOWN and independent-handle WAL
   row+event coherence; matching bytes never identify the writer.
3. Integrate mock-only Planner exact step+ancestor READ receipts with immutable
   Registry/PermissionGate and restart-safe reservation→audit→link fences
   after their independent exact-head gates. No WRITE dispatch or replay.
4. Advance privacy-safe Personal Context, proactive scheduler and observation
   backend contracts on separate free lanes. Keep V3 approval/path/identity
   guard under its human/paid boundary and all UI work paused.

No paid/external GPU, cloud service, new account/secret, physical PC use,
real Candidate training, protected V2 evaluation, irreversible action,
main merge or frozen contract modification occurred. ARK/JARVIS/V3:
**NOT_PASSED**.

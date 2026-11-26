# ARK AI Run821 — Non-UI exact receipt epochs and preaccess WRITE admission

**Scope:** Draft PR #8, `research/jarvis-foundations`, reversible local-only reviewer hardening. **Overall ARK/JARVIS: NOT_PASSED.** This report is a review record, not model evaluation, user consent, independent storage provenance, trusted time, or execution authorization.

## Exact work basis and new packages

- Initial exact work-basis HEAD: `45a4b8687d77f41d6ea6c8649a55c2a1c3d35022` (Run820 checkpoint), whose [Actions run #43233054394](https://github.com/Iam-2squared/ark-ai/actions/runs/43233054394) was verified **GREEN 6/6** (Windows and Ubuntu, Python 3.11/3.12/3.13) before edits.
- **Memory retained coherent expiry identity, 7 new cases.** Source commit `3239b94e5e4393ed90b5011cabbb863e73899ea6`, test commit `2703342721d53848e3649d567c9c946a8db25116`. A prior expiry page and cohort now require precisely the same captured field objects across the live SQLite callback. Prior tuple value-equality admitted reflected substitutions with `True == 1`, `0 == False`, `1500.0 == 1500`, or a fresh but equal string/tuple. New tests mutate the frozen receipt *inside the read-only connection opening callback*; expected result is a fail-closed `CoherentExpiryRestartRejected` before the second read can be accepted. This is source epoch consistency, **not** historic integrity attestation or purge permission.
- **Cross-domain recovery helper and leaf custody, 9 new cases.** Source commit `d34fa38b2b2f94a92ccaf294086293b1fec13136`, test commit `7a5931b4ef7dedc93d54e794585a041bcd8b7ac3`. The inventory now pins its own hash/validation/epoch helpers before invoking them and compares nested receipt leaf **identities** instead of coercive equality. Tests exercise hostile monkeypatch hooks (not called), bool/int/float and nested structural drift, hostile `__eq__` avoidance, and deterministic inert canonical receipts. No SQLite writes, dispatch, replay, trust, or human approval.
- **Planner independent WRITE ID preaccess, 3 new cases.** Source commit `31569e1755e673e80b8f9715ba48aec6ef92514b`, test commit `82437724e7f18fd02c83f1b345789ba37b8eb1d7`. Validate exact bounded string IDs before the independent expected-write tuple reaches equality, sorting, or downstream Planner/SQLite reviewers. Prevent a `str` subclass with hostile `__eq__`/`__hash__` from executing on input rejection; reject blank and overbudget inventories. Original WRITE isolation is unchanged.

**Total new regression cases authored: 19 (7 + 9 + 3).** No local full checkout, pytest, Ruff, physical-PC GGUF verification, or real tool execution was performed. All GitHub changes used the normal contents API after re-reading the live PR head; no alternate writes or force pushes.

## GitHub Actions observation (not final PASS)

- Source `3239b94e5e4393ed90b5011cabbb863e73899ea6`: [#43241396004](https://github.com/Iam-2squared/ark-ai/actions/runs/43241396004) started.
- Memory tests `2703342721d53848e3649d567c9c946a8db25116`: [#43241590000](https://github.com/Iam-2squared/ark-ai/actions/runs/43241590000) started.
- Recovery source `d34fa38b2b2f94a92ccaf294086293b1fec13136`: [#43241770755](https://github.com/Iam-2squared/ark-ai/actions/runs/43241770755) started.
- Recovery tests `7a5931b4ef7dedc93d54e794585a041bcd8b7ac3`: [#43241935290](https://github.com/Iam-2squared/ark-ai/actions/runs/43241935290) in progress at last read.
- Planner source `31569e1755e673e80b8f9715ba48aec6ef92514b`: [#43242707295](https://github.com/Iam-2squared/ark-ai/actions/runs/43242707295) in progress at last read.
- Planner tests `82437724e7f18fd02c83f1b345789ba37b8eb1d7`: [#43242814578](https://github.com/Iam-2squared/ark-ai/actions/runs/43242814578) queued/in progress at last read.

**No final exact-head 6/6 GREEN is asserted here.** Later workflow results must be checked against exact `head_sha`; a prior commit's GREEN is not proof of later test changes. A checkpoint commit will have its own SHA and CI.

## Boundaries, residual risks, and next steps

Preserved V1/V2/Local UI/Launcher frozen evidence/contracts. PR #5 remains DRAFT/unmerged under protected final evaluation and Candidate boundaries; paused UI PR #9 remains untouched DRAFT/unmerged. This work does not change V3 paid-compute policy, generate real weights or Candidate evidence, access paid/external compute, ask for credentials, use unavailable PC hardware, run real backends, purge Memory, approve actions, auto-retry UNKNOWN, or merge main.

Remaining gaps: caller-controlled retained receipts are not independent provenance; inter-process and across-store transaction atomicity are not established; real clock/consent/external-effect attestation and safe automatic retry are absent; earlier intermittent independent-owner SQLite sidecar race deserves an exact-head regression investigation but must not be relaxed.

**Next plan / 今後の方針:** (1) Confirm exact-head 6-job CI for all three packages and fix only observed semantics-preserving failures; (2) investigate SQLite sidecar cross-process race without deleting or weakening path safeguards; (3) extend durable Memory CAS/ABA/COMMIT-UNKNOWN plus Planner permanent UNKNOWN quarantine; (4) integrate immutable ToolRegistry / exact PermissionGate / trusted-clock audit-before-action / disconnected mock executor **only after** lower-layer exact-head GREEN; (5) continue privacy-safe Personal Context, proactive/observation fixture and V3 free-only guard audits as separate, reversible non-UI lanes.

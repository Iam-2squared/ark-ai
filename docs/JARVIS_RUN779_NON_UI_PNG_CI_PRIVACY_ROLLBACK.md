# Run779 — Non-UI PNG CI repair, privacy veto rollback, registry budget integrity

All work is **free-only**, in isolated, disconnected Python fixtures on Draft PR #8,
without UI/frontend changes or any live ToolBackend. This report records observed
behavior and evidence, not authenticated issuer identity, trusted time, deletion,
consent, immutable custody, billing authorization, or actual effect completion.

## Work basis

- Initial checkpoint HEAD: `24537f8e1859f18ad057cda61407575b7d5ecdb2` (Run778).
- Branch `research/jarvis-foundations`; PR #8 open, Draft and unmerged.
- Initial source/test compare to latest test HEAD
  `c0043e72629183bccaab537c9dbc571af9dcd164`:
  ahead 2, behind 0; exactly two test paths, no production module touched.

## Package A — actual six-environment PNG test failure

Run778 [CI #42922562769](https://github.com/Iam-2squared/ark-ai/actions/runs/42922562769)
exposed the same new test failure in the reported Ubuntu and Windows jobs:
`test_in_place_depth_table_mutation_rejected_and_restored` expected a valid
post-restore PNG but received `OfflinePngRejected: PNG signature mismatch`.
The real logged source was
`tests/test_offline_png_format_limits_run778.py:72`; source's reference
signature is the real eight-byte `b"\\x89PNG\\r\\n\\x1a\\n"`.
The fixture had mistakenly used a *double-escaped* byte literal containing
literal backslash characters. PNG production signature enforcement was correct.

Normal GitHub Contents update at
`6fc6c994926dfac0b6c04fecbbb24945ef6ba50e` replaces exactly
that malformed test fixture literal with its canonical eight-byte signature.
All mutation/restore assertions remain, and production PNG admission policy,
hashing, limits and privacy denials were **not** changed.
[Replacement-head CI #42925888711](https://github.com/Iam-2squared/ark-ai/actions/runs/42925888711)
was IN PROGRESS when inspected; do not substitute prior successful CI.

## Package B — independent, valid privacy veto source replacement

`tests/test_privacy_veto_valid_source_rollback_run779.py` added at
`c0043e72629183bccaab537c9dbc571af9dcd164`: two parameterized scenarios
replace a disposable initialized SQLite veto source with another *valid*
database, either genesis or an unrelated one-veto history with the **same
row count**. Explicit `require_existing=True` can reopen a valid replacement:
that guard prevents accidental missing-file creation, but it does not
authenticate earlier history. The original separately retained witness must
reject `review(..., retained=original_witness)` via local count/digest
mismatch. A newly read local-only witness remains **non-authorizing**, even if
it reports no current marker. No real user data, privacy export, deletion
or physical file is touched; replacement is confined to pytest `tmp_path`.

[Fixture-head CI #42926203904](https://github.com/Iam-2squared/ark-ai/actions/runs/42926203904)
was IN PROGRESS when sampled. The new cases have not been declared GREEN.

## Package C — ToolRegistry budget integrity, independent backend lane

`src/ark/agency/registry.py` strengthened at
`4ca80954e3653ade401a42d4278fd7e19de84b00`.
The import-original `_MAX_REGISTRATIONS=256` and
`_MAX_REGISTRATION_TEXT=256` were previously mutable admission knobs.
Pin both values as exact integers and check them before any untrusted
registration string or backend descriptor is inspected, and during digest
and revision reads. This does **not** relax existing registry requirements
or grant backend execution. A previously constructed registry also rejects
limit drift instead of returning a new identity.

`tests/test_registry_admission_limit_custody_run779.py` added at
`8f2e5e8b8038ecdb650d25898e3fb2f4a312b8fa`.
Eight parameterized negative/restore tests cover rebound, bool, zero and
negative budgets; invalid backend preflight is refused with an explicit
admission-limit diagnostic before backend inspection. A local synthetic
registry remains usable after temporary monkeypatch restoration. Tests use
only an inert backend which raises if ever executed. There is no live
tool authorization, external permission or actual effect.

[Registry source CI #42926729041](https://github.com/Iam-2squared/ark-ai/actions/runs/42926729041)
was IN PROGRESS and [source+test CI #42926836527](https://github.com/Iam-2squared/ark-ai/actions/runs/42926836527)
was QUEUED when first sampled. Exact-head six-job GREEN is not claimed.

## Limitations and next checks

- Full six-environment exact-head CI success is **not yet verified** for
  either changed test HEAD; inspect completed jobs and actual failing logs.
- The baseline 1 failed / 12,770 passed / 1 skipped Ubuntu log for
  `#42922562769`, and the Windows 3.11 log's 1 failed /
  12,697 passed / 74 skipped, are *prior failure evidence*, not proof of
  corrected work. Remaining job statuses should be read from Actions.
- A retained witness is a caller-supplied, potentially losable comparison
  value. It is not immutable external custody. A valid replacement DB and a
  newly generated witness alone never attest retention or grant consent.
- All changes are reversible test-only additions/corrections. No new
  credential/account, paid API/GPU, Candidate generation/promotion, protected
  V2 evaluation, live executor, real notification/microphone/camera, frozen
  V1/V2/Local UI/Launcher contract changes, or main merge.
- PR #5 protected V3 Draft and PR #9 paused UI Draft remain untouched.
- Next: verify repaired PNG and privacy-veto exact-head CI; apply minimal
  semantics-preserving test corrections if needed. Then continue independent
  Memory CAS/COMMIT-UNKNOWN and Planner/audit/mock-executor backend work.

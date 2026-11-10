# Run778 — disconnected PCM/PNG privacy fences and cold schedule identity

**Work basis:** `dbc378ccc8a470ffb7ec3ba7e6730c83fb016a5a` (Run777 checkpoint),
`research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8).
**Last source/test HEAD:** `ebe555fdb02a310b1248ce3a3bf313c71b06d23b`.
Three independent, reversible **non-UI, free-only** packages; five touched
source/test files (two production helpers and three new tests), **23 new
parameterized cases**. These are local synthetic fixtures, **not** an
authenticated capture, trusted clock, grant, external execution or JARVIS PASS.

## Package A — private offline PCM callback preflight

- `src/ark/offline_pcm_mono16.py`, commit
  `385866b615acdd2777b695aea8c3195637880ca7`;
  `tests/test_offline_pcm_codec_preaccess_run778.py`, commit
  `907b6102c01ceca398eff094da2b6a838339a71a`, **8 cases**.
- Import-original SHA-256/JSON functions, module identities, digest regex,
  inventory domain and input/output/duration bounds are checked before
  accessing a request's private audio fields. They are rechecked during
  processing, ahead of raw and output digests and before serializing the
  digest-bound inventory.
- A hostile replacement of either codec callback must receive **zero** raw
  PCM bytes; changed limits/identity fail closed. Synthetic reference
  conversion and all four denied-authority properties remain unchanged.
- Not an in-process adversarial sandbox; it cannot prevent arbitrary code
  already running with equal privileges from inspecting Python memory.

## Package B — cold-process synthetic schedule identity

- `tests/test_schedule_preview_cold_identity_run778.py` at
  `7f142c11850e72d5e1e242bedc380d42df581c8d`, **6 cases**.
- Spawn an independent Python interpreter for due, not-due, expired
  quarantine and exhausted next-slot previews; require deterministic
  occurrence identity and exact fingerprint equality across interpreters.
- Retargeted recurrence policy cannot reuse a previously derived cursor;
  the inclusive signed-64-bit maximum due timestamp is supported without
  rollover, while the out-of-range final due must be rejected.
- This exercise neither advances a durable cursor nor proves real wall
  time, delivery or consent. All five authority fields remain False.

## Package C — bounded PNG format admission

- `src/ark/offline_png_inventory.py`, commit
  `2398c9a618b151f387ae70d2cd904bc6f29d2c5e`;
  `tests/test_offline_png_format_limits_run778.py`, commit
  `ebe555fdb02a310b1248ce3a3bf313c71b06d23b`, **9 cases**.
- Preflight now pins the parser module references, regex, signature, exact
  integer budgets and reviewed color/depth admission table. This includes
  catching an **in-place** mutation to the mutable depth table.
- The existing SHA/CRC/framing preaccess tests and canonical metadata-only
  inspection are preserved. No pixel decompression, camera access or
  disclosure/consent permission.

## Evidence and limitations

Initial-to-last-source comparison
`dbc378c...ebe555f`: five commits ahead, no behind commits, exactly five
source/test paths touched. All writes used ordinary GitHub Contents API,
with the branch HEAD re-read before each write; no force update, raw-object
bypass, merge or user-data deletion.

- Run777 latest checkpoint `dbc378c...`:
  [CI #42921251907](https://github.com/Iam-2squared/ark-ai/actions/runs/42921251907):
  Ubuntu 3/3 GREEN, Windows 3 in progress at last query; **not** full GREEN.
- PCM source-only `385866b...`:
  [CI #42922131920](https://github.com/Iam-2squared/ark-ai/actions/runs/42922131920):
  Ubuntu 3.11 GREEN, others incomplete at last query.
- PCM test `907b610...`:
  [CI #42922211789](https://github.com/Iam-2squared/ark-ai/actions/runs/42922211789):
  running/queued.
- Schedule test `7f142c1...`:
  [CI #42922350033](https://github.com/Iam-2squared/ark-ai/actions/runs/42922350033):
  queued.
- PNG source `2398c9a...`:
  [CI #42922497588](https://github.com/Iam-2squared/ark-ai/actions/runs/42922497588):
  queued.
- PNG test `ebe555f...`:
  [CI #42922562769](https://github.com/Iam-2squared/ark-ai/actions/runs/42922562769):
  queued.
- The report and canonical checkpoint themselves create **newer HEADs**
  and trigger their own CI. **All-six GREEN for the final checkpoint HEAD
  remains unverified.** No local full-suite Python result, physical PC or
  GGUF performance result is claimed.

## Frozen boundaries / prioritized next plan

- **Unchanged:** Draft/unmerged PR #5 V3
  `805b377697472268db02650a89c7a94b1c5337c8`, paused UI Draft PR #9
  `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`, `main`, frozen
  V1/V2/Local UI/Launcher, protected evaluation, and existing observation
  envelope semantics.
- No paid service/API, external compute, Candidate generation/promotion,
  new accounts/credentials, human-review fabrication, real sensor,
  notification, real ToolBackend or protected evaluation.
- **First:** inspect actual failing logs if any; make only minimal
  semantics-preserving test/source corrections through the normal Contents
  path. Verify final exact-HEAD six-job Windows/Ubuntu CI before GREEN.
- **Then:** return to Planner durable terminal/UNKNOWN recovery, Memory
  CAS/expiry/COMMIT-UNKNOWN coherent reads and privacy veto continuity.
- **Later:** immutable registry-bound execution, exact PermissionGate,
  trusted-clock audit-before-action and isolated mock Executor. Real
  dispatch remains blocked by missing authenticated consent, independent
  custody, cross-store transaction and external exactly-once semantics.

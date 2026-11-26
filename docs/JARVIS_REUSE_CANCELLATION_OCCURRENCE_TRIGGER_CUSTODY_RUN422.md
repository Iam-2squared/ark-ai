# Run 422 — disconnected receipt custody and post-transaction witnesses

**Scope:** `research/jarvis-foundations` / Draft PR #8, free-only, no merge.
**Work-basis canonical checkpoint HEAD:** `1a9c28e1d818fc87234207e8bbf6d013fcc7b340` (Run421). Its automatically triggered CI **#1118 / 40186837160** is SUCCESS, as observed on opening inspection.
**Run422 final source/test candidate HEAD (before this document):** `d35b3a97483e7591fc4eff62f50437323ac877e8`.
The previous checkpoint is not evidence that this new candidate is GREEN. Confirm this candidate's **own** jobs before treating it as validated.

## Independent source + regression packages

| Package | Source commit | New regression-test commit | Parametrized cases |
|---|---|---|---:|
| Observation lineage reuse and returned receipt | `e928a2800f6271aaec946b8a0a93b4f597c691c6` | `dde2e011d8fddb065d27f0a093aa934f04417305` | 9 |
| Synthetic approval cancellation fence | `c63d4c6a81b6f3bb3eecf09956d65fcccfdf3819` | `8c8cdb5a8cbb6398b85fbb0b330f5d95e95b6d82` | 8 |
| Occurrence reservation retained-history reader | `48e4ea6703a6c12b9b7e8e769d69ac2f633378e9` | `dbe051626bb678f2e8d22ec53f0ac74c577540c5` (test-hook repair `d35b3a97483e7591fc4eff62f50437323ac877e8`) | 5 |
| Proactive trigger retained-history reader | `c40196310d5c8b0eeb235a04e4c8acfb8b9d7dbd` | `e894a503b47072225d348f4ed0db658431ea58f3` | 5 |

**New pytest cases:** 9 + 8 + 5 + 5 = **27** relative to the Run421 tests. Counts describe declared parametrizations, not verified PASS claims. The source/test candidate above supersedes intermediate source-only and test-adding HEADs for whole-package validation.

### 1. Observation reuse

`src/ark/observation_reuse_review.py` now pins every original envelope metadata carrier *before* calling the observation-ID property, checks the original cached witness by exact carrier identity across both lineage callbacks, and preserves both historical and current lineage witnesses through final receipt construction. A content-equal but different string object is still a suspicious source substitution, even when a canonical digest would be unchanged. The current synthetic lineage result must refer to the requested scope, check time and actual fixture count. Test fixture: `tests/test_observation_reuse_result_carriers_run422.py`. This remains metadata-only and does not authenticate cameras, microphones, screens, captures or disclosure consent.

### 2. Approval claim + cancellation custody

`src/ark/agency/synthetic_approval_cancellation_fence_review.py` now pins input claim/action/revision and retained-witness scalar carriers rather than only their equal values. The first cancellation receipt, the reviewed synthetic claim receipt, and the second cancellation receipt are separately pinned before further callbacks and rechecked **after** the final review object is constructed. The two independent SQLite state reads remain **non-atomic** and retain a post-check revocation race. No valid grant, authenticated issuer, real human consent, dispatch, or exactly-once result is inferred from an absence of local veto markers. Tests: `tests/test_approval_fence_result_custody_run422.py`.

### 3–4. Occurrence/trigger read-only SQLite witness lifecycles

`src/ark/agency/synthetic_occurrence_continuity_review.py` and `src/ark/proactive_synthetic_continuity_review.py` now retain digest and tuple-element identities and check the final constructed witness before/after its integrity check, continuity comparison, SQLite read-transaction COMMIT and SQLite connection closure. The tests inject equal-valued witness replacements on COMMIT or CLOSE (without a real reservation or notification). This is **read-only** and never repairs, recreates, truncates or consumes persisted rows. The old independently retained history remains required for meaningful rollback diagnostics.

The occurrence test hook was scoped to the fixture database rather than SQLite's separate schema-validation `:memory:` handle; this is a test-only fixture correction, not a production DDL change.

## CI / verification discipline

Source-only and source+test commits trigger distinct CI automatically. No duplicate equivalent workflows were manually dispatched. Run421 exact checkpoint **#1118 / 40186837160** is independently SUCCESS. Run422 source/test candidate must obtain its own exact-HEAD GitHub Actions CI result; intermediate GREEN does not prove subsequent commits. Ruff and Python 3.11/3.12/3.13 Ubuntu/Windows success counts must be cited only after inspecting matching jobs and logs. If an unintentional test/formatter mismatch fails, preserve the FAILED run and apply the smallest semantics-preserving fix through ordinary GitHub Contents writes.

Reproduce locally, without any external services:
```sh
python -m pytest -q tests/test_observation_reuse_result_carriers_run422.py tests/test_approval_fence_result_custody_run422.py tests/test_occurrence_witness_commit_custody_run422.py tests/test_proactive_witness_commit_custody_run422.py
ruff check src/ark/observation_reuse_review.py src/ark/agency/synthetic_approval_cancellation_fence_review.py src/ark/agency/synthetic_occurrence_continuity_review.py src/ark/proactive_synthetic_continuity_review.py
```

## Frozen boundaries and next integration checks

All changes are within the isolated JARVIS foundation branch. Existing main V1/V2/Local UI/Launcher frozen contracts, Memory v1/ActionAudit v1 schemas and protected V2 evaluation were not edited. V3 PR #5 remains Draft/unmerged/NOT_PASSED. Do not claim valid human issuer, signed clock, authentic media or trusted hardware, cross-database transaction atomicity, external backend result, true exactly-once external WRITE, automatic Candidate promotion or live autonomous dispatch.

**Next:** (1) close exact-head CI evidence and repair only demonstrated failures; (2) crash-window and partial-prefix replay tests across Planner/Occurrence/ActionAudit/AuditLink without executing an action; (3) Memory CAS, retained scope expiry, coherent snapshots and privacy revocation; (4) disconnected startup/clock/observation/proactive fixtures; (5) V3 free-only provenance and approval path checks. Payment, new account links, real GPU, frozen evaluation opening, contract changes, Candidate generation/promotion or main merge require separate explicit authorization.

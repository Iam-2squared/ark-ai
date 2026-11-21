# Run958 — Non-UI synthetic proactive/privacy quarantine, registry token isolation, Memory WAL CAS

## Boundaries and work basis

- Basis: `f06f0d20eb12f8ad2053f73adc9a3d18e2b43709` (Run957 checkpoint; [CI #44225551315](https://github.com/Iam-2squared/ark-ai/actions/runs/44225551315) GREEN 6/6).
- Target: `research/jarvis-foundations` / [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), **not main**. No merge or branch rewrite.
- All new fixtures use temporary local SQLite files, mock backends, and digest-only synthetic markers. No paid API, GPU, Candidate generation, real hardware, external operation, approval, notification, capture, or protected evaluation. Existing frozen contracts untouched.
- These tests check *fail-closed local assumptions*, NOT authenticated user consent, deletion proof, physical path custody, cross-store atomicity or exactly-once real-world effects.

## Four independently scoped code packages — 20 new parameterized cases authored

1. **Proactive persisted marker corruption** [`b263ca9b`](https://github.com/Iam-2squared/ark-ai/commit/b263ca9b5c5051ccc17eac7b3aa317ded80cc3cd): 7 tampered fields (foreign trigger ID, binary/malformed/renamed digest, binary observed time, reversed clock) require cold constructor/count/prepare denial and preserve the raw row. A healthy synthetic preparation remains no-dispatch/no-notification.
2. **Privacy cold veto corruption** [`af88c0a3`](https://github.com/Iam-2squared/ark-ai/commit/af88c0a38508e20a61180d1f5745903ebd976bd2): 6 malformed scope/time row variants must deny cold-open, private and unrelated scope reads, and new veto writes without repairing history. One healthy monotone-restart case. A perfectly valid-looking but replaced digest file *requires an independent retained witness*: this test does not claim to detect that attack.
3. **Registry-bound WRITE scope denial** [`cb686af5`](https://github.com/Iam-2squared/ark-ai/commit/cb686af5f683f8a49fda98e4d6a8a22f64f1842f): 3 invalid-scope variants (NUL, lone surrogate, over-budget UTF-8) must not consume an unrelated process-local one-shot token; a subsequent exact valid action can consume it once, without running its disconnected mock backend. This is not restart-safe authorization.
4. **Memory WAL checkpoint / generation CAS** [`4e296f95`](https://github.com/Iam-2squared/ark-ai/commit/4e296f95fc4e550a8d7574682ec727e114ea7818): 3 physical SQLite WAL checkpoint modes (PASSIVE/FULL/TRUNCATE) while preserving the logical Memory generation token, a cold update, stale-token rejection, and exact create/update event history. No frozen Memory v1 API/schema change.

**Total: 7 + 7 + 3 + 3 = 20 parameterized test cases authored, not yet verified as latest-HEAD GREEN at report creation.** Only tests and this evidence document were changed; no production source was changed.

## Exact-head CI evidence

- Prior basis [#44225551315](https://github.com/Iam-2squared/ark-ai/actions/runs/44225551315): completed GREEN 6/6; evidence belongs solely to `f06f0d20`.
- Proactive [#44232114844](https://github.com/Iam-2squared/ark-ai/actions/runs/44232114844): started for `b263ca9b`, IN PROGRESS at initial report preflight.
- Privacy [#44232172759](https://github.com/Iam-2squared/ark-ai/actions/runs/44232172759): started for `af88c0a3`, IN PROGRESS at initial report preflight.
- Registry [#44232290469](https://github.com/Iam-2squared/ark-ai/actions/runs/44232290469): started for `cb686af5`, IN PROGRESS at initial report preflight.
- Memory [#44232505230](https://github.com/Iam-2squared/ark-ai/actions/runs/44232505230): QUEUED at initial report preflight for `4e296f95`.
- The newest test-containing head does not inherit GREEN from an earlier SHA. Check every Windows/Ubuntu × Python 3.11–3.13 job and repair any newly observed failure before making a PASS claim.
- Remote tests cannot be treated as locally verified; no offline source or test runner was available for this GitHub-only working session.

## Contracts and frozen gates preserved

V1/V2/Local UI/Launcher evidence, V2 protected final evaluation, V3 frozen Contract 1, all frozen scoring/contamination/reproducibility constraints and paused UI Draft PR #9 are untouched. PR #5 and #8 remain Draft/unmerged. No credential, paid service, external GPU, Candidate artifact, actual device operation, or main merge is authorized.

## Next plan / 今後の方針

1. Verify all six matrix jobs on the latest code head. If a job fails, use logs and the smallest semantics-preserving correction; no duplicate workflow run.
2. Prioritize real cross-handle Memory WAL/SHM and CAS/ABA monotonicity, then Planner COMMIT-UNKNOWN and terminal persistence, with exact-head evidence.
3. Strengthen registry-bound PermissionGate plus durable audit-before-action and occurrence replay fences before any connected executor.
4. Continue privacy-safe Personal Context, proactive/observation fixture contracts, startup readiness and zero-cost V3 approval/path/identity safeguards, without opening protected gates.

**Overall ARK/JARVIS: NOT_PASSED.**

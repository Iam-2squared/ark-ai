# ARK AI Run947 — opt-in Memory NUL admission, Planner terminal waves, atomic prefix triage, privacy veto churn

> Synthetic and disconnected non-UI development only. **Overall ARK/JARVIS NOT_PASSED**. No real tool backend, owner-PC operation, actual consent, trusted clock, external outcome, protected V2 final-evaluation or Candidate execution. This report is a development record, not a PASS gate.

## Exact work basis and saved changes

Run946 checkpoint basis: `e006401e24f91c16491fe0d65fe8fa54c91e79a0` on `research/jarvis-foundations` (Draft PR #8). Latest source/test HEAD prepared for verification in this report: `2993cdb310715e52c3b1810951b5c95cb877004f`. The checkpoint that follows may have a newer SHA; do not conflate them.

1. **Memory generation-CAS NUL hardening**: [`d458f127`](https://github.com/Iam-2squared/ark-ai/commit/d458f1273e808e028ec1840530c68b6e6c63d966) restricts *optional* generation-fenced owner, namespace and source IDs to exact bounded UTF-8 with no embedded NUL. Frozen Memory v1 schema/contracts/put API are unchanged. Initial CI exposed literal `\\n` in a Python condition introduced by this update: [`9197ff40`](https://github.com/Iam-2squared/ark-ai/commit/9197ff40b5b7ffd131323a02f99b5f4078348d53) fixed the syntax without relaxing its new reject condition. [`2993cdb3`](https://github.com/Iam-2squared/ark-ai/commit/2993cdb310715e52c3b1810951b5c95cb877004f) adds 9 NUL identity rejection scenarios plus one valid multibyte update control, checking no persisted row/event change for the rejected path.
2. **Planner two terminal waves**: [`88c335d7`](https://github.com/Iam-2squared/ark-ai/commit/88c335d74b34b71bf44d8fb189835cb90135a5c3) adds 9 FAILED/CANCELLED/BLOCKED × FAILED/CANCELLED/BLOCKED combinations for independent branches with a shared fan-in. The first failure blocks its descendants; the second never republishes the already terminal shared descendant, no blocked revision increments twice, and stale transitions remain rejected.
3. **Atomic local COMMIT-UNKNOWN review**: [`9fce44b7`](https://github.com/Iam-2squared/ark-ai/commit/9fce44b7a4457b3f1b6ed32c8678360e5fee2692) adds 9 retained-prefix/occurrence combinations across four inert SQLite audit-paired commits, then checks independent Python interpreter classifications and all no-authority dispositions. CI caught a test-only Ruff import-block spacing error, corrected in [`a5300f24`](https://github.com/Iam-2squared/ark-ai/commit/a5300f2402592fbe1ba2848c018498eba245ce79).
4. **Personal Context durable revocation veto**: [`e255fc64`](https://github.com/Iam-2squared/ark-ai/commit/e255fc642a44aefd3d74f0baa9171812cf066268) adds 6 scoped cases (Memory update/delete/append × alternate owner/namespace). A cold reopened local review keeps a revoked scope denied while separate foreign scope remains distinguishable; private synthetic content stays outside `repr`. This **does not** automatically erase Memory rows or establish atomicity across the two SQLite stores.

**New cases: 34 (10 + 9 + 9 + 6).** Synthetic/focused changes, not proof of operational exactly-once semantics. No whole-suite local pytest or physical GGUF claims.

## CI/evidence and known corrections

- Baseline Run946 final HEAD `e006401e`: [CI #44118887877](https://github.com/Iam-2squared/ark-ai/actions/runs/44118887877) **GREEN 6/6**, covering only the previous source/test state.
- New source head `d458f127`: [CI #44129957088](https://github.com/Iam-2squared/ark-ai/actions/runs/44129957088) **FAIL 6/6**: source Python literal backslash-newline syntax, not evidence of a runtime Memory violation.
- Intermediate `88c335d7`: [CI #44130111880](https://github.com/Iam-2squared/ark-ai/actions/runs/44130111880) **FAIL 6/6**, same source syntax.
- Corrected source/test `9197ff40`: [CI #44130399999](https://github.com/Iam-2squared/ark-ai/actions/runs/44130399999) **FAIL 6/6**: Ruff I001 in newly authored Atomic test (extra blank after import block). Normal Contents update `a5300f24` corrected it.
- Latest source/test head `2993cdb3`: [CI #44130943727](https://github.com/Iam-2squared/ark-ai/actions/runs/44130943727) **IN_PROGRESS** at report read; this is **not** a six-job GREEN claim. Further result updates belong in the end-of-invocation PROJECT_STATUS checkpoint, after fresh job reads.

CI is PR-triggered; no duplicate equivalent workflow was manually dispatched.

## Explicit guardrails and priorities

Leave PR #5 Draft/unmerged under its V3 gate, UI PR #9 Draft/unmerged/untouched and all frontend work paused. Keep main unchanged; preserve V1/V2/Local UI/Launcher evidence and frozen contracts. No paid/external compute, API purchase, real Candidate/preflight, V2 protected final evaluation, hardware action, external ToolBackend, new credentials, or destructive action.

Next: confirm exact latest source/test HEAD six-job CI, repair only proven failures via ordinary Contents API; then prioritize durable Memory event/generation high-water and WAL coherent snapshots, Planner crash-unknown quarantine, ToolRegistry/PermissionGate and trusted-clock audit-before-action as isolated, reversible, free-only non-UI components. Do not infer real consent, provenance or permission from any synthetic receipt, digest, or cold subprocess.

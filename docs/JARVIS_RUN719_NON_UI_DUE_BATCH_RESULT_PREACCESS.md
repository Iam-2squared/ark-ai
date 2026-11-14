# ARK AI — Run719 FREE-ONLY non-UI integrity and preaccess hardening

## Scope and work basis

- Repository: `Iam-2squared/ark-ai`; work branch `research/jarvis-foundations`, **Draft PR #8**, unmerged. Initial inspected HEAD `100345b4436a8966093dff55d28545ca1b3b5958` (Run718 status checkpoint); source and test writes used normal GitHub Contents API, re-reading latest head before writes. No force updates or raw Git-object bypass.
- Production changes are isolated to three disconnected/mock-only backend modules. No frontend/UI work, backend execution, live scheduler, account access or remote network action.

## Package A — due reservation SHA/JSON dependency custody

- [Source `f5478767`](https://github.com/Iam-2squared/ark-ai/commit/f547876762a6e3439b5fbb3d0e7abf8dfcaab456) pins original `hashlib.sha256` and `json.dumps` identities in `disconnected_due_reservation.py` before path/ledger work and at each synthetic digest transition. Refuses substituted callbacks before ledger access. The check is an in-process fail-closed fence, **not** trusted-clock or independent history authentication.
- [Eight authored regressions `cd6c0728`](https://github.com/Iam-2squared/ark-ai/commit/cd6c07289817969782902298d4ddeca315f2d5cb) across create, witness, reserve, and genesis operations require the replaced digest callbacks to remain uncalled; original fixture remains unchanged after restoration.
- An initial source+test CI revealed **five inherited test failures** in Ubuntu 3.11 [run #42513602245](https://github.com/Iam-2squared/ark-ai/actions/runs/42513602245), caused by stronger early refusal changing the observed diagnostic/exception in the separate due-restart read review. The source security check was **not weakened**. [Four inherited parameterized assertions corrected `4ff27001`](https://github.com/Iam-2squared/ark-ai/commit/4ff270013ffc3f9efe0698fabf5870e4d145f919) and [one late-prefix fixture corrected `bf7a1093`](https://github.com/Iam-2squared/ark-ai/commit/bf7a1093b1f2815ea526403d93ccd5b982cb27ad) to demand earlier denial and no mutation. The corrected exact HEAD remains CI-unverified at report time.

## Package B — detached batch wavefront digest custody

- [Source `b4059247`](https://github.com/Iam-2squared/ark-ai/commit/b4059247682d03117ba3ed71ca392e2caa427c8e) pins SHA-256 and canonical JSON serializer in `disconnected_batch_schedule.py` at entry before caller plan inspection, as well as before/after wavefront canonicalization and hashing. No real parallel scheduling or backend call is added.
- [Four authored regressions `4d729da0`](https://github.com/Iam-2squared/ark-ai/commit/4d729da07440a58ff9cf52b25f0c994c0d599904) cover both original callback substitutions during build and verification with zero intercepted plan data.

## Package C — complete detached READ result privacy

- [Source `105707ff`](https://github.com/Iam-2squared/ark-ai/commit/105707ff010b77e22d8c2745fc9905109c856aae) validates the original SHA-256, JSON loads/dumps and strict parser callbacks (`_pairs_unique`, `_int64`, `_no_float`) before inspecting content-bearing `DetachedReadResult` fields, with repeated guards around decoding/normalizing. Raw result payload is not included in the sealed output. This does **not** prove a real tool produced the result.
- [Six authored regressions `0b0addcd`](https://github.com/Iam-2squared/ark-ai/commit/0b0addcdebae030f253c6a85b3159cb8ffeb9107) require all six categories of substituted callbacks to remain uninvoked when sealing synthetic content.

## Evidence and limitations

- **18 authored synthetic parameter-expanded tests** across three new test files, three production modules, plus two inherited test files corrected. These are **authored, not locally executed or all-platform verified**. The connector environment does not provide an executable checked-out repo and no full local pytest/Ruff run was made. Prior run [#42512883594](https://github.com/Iam-2squared/ark-ai/actions/runs/42512883594) had Ubuntu 3/3 GREEN and Windows 3/3 still IN PROGRESS when reviewed; this is on an **earlier Run718 HEAD**, not this invocation's commits.
- Early Ubuntu failures were observed on test-head [#42513602245](https://github.com/Iam-2squared/ark-ai/actions/runs/42513602245): 5 failed / 11,235 passed / 1 skipped for Python 3.11. The corrected last source/test HEAD [#42514041992](https://github.com/Iam-2squared/ark-ai/actions/runs/42514041992) was **QUEUED** at report time. Neither this HEAD nor the later report/checkpoint HEAD may be declared 6/6 GREEN without exact run evidence; intermediary runs do not certify later commits.
- The imported-callback checks catch substitutions **after import** only. They are not process isolation, independent provenance, trusted permission, confidentiality against arbitrary code in the same Python process, or cross-process exactly-once execution. Failure around SQLite COMMIT remains potentially ambiguous and must not trigger an automatic retry.
- Preserved main, Draft PR #5 protected V3 gate and Draft PR #9 paused UI, plus frozen V1/V2/Local UI/Launcher contracts and evidence. No paid service, external/GPU compute, Candidate generation/promotion, protected evaluation opening, live tool or user data, hardware action, credential connection or main merge.

## Next plan / 今後の方針

1. Verify the corrected exact-head Windows/Ubuntu Python 3.11–3.13 CI. For failures inspect actual job logs, make only semantics-preserving corrections; use unrelated non-UI modules during CI.
2. Integrate **detached READ input manifest** custody with independently retained expected hash only when complete journal and topology validation are GREEN; evaluate folder durability, symlink/ancestor races, and bounded malformed JSON handling without weakening fail-closed semantics. No real backend dispatch.
3. Strengthen Memory generation CAS/ABA, WAL coherent row/event commitments and human-reviewed COMMIT-UNKNOWN classification; no automatic ambiguous-write replay.
4. Progress registry-bound authorization, durable one-time approval, audit-before-action and disconnected mock-only execution under exact-head prerequisite tests. Continue privacy/proactive/observation contracts free-only; **no UI work**.

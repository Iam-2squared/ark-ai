# ARK AI — Run724 / Detached READ Windows correction and Memory global high-water closure

**Scope:** free-only, disconnected, non-UI JARVIS foundations; Draft PR #8 (`research/jarvis-foundations`). **ARK/JARVIS/V3: NOT_PASSED.** No actual tool/model execution, paid service, GPU, Candidate, protected V2 final evaluation, UI changes, promotion or main merge.

## Exact work basis and concurrent state

- Initial exact branch HEAD: `69486c6a84d4d6f1199468f236476a82ce21e797` (Run723 checkpoint).
- The last source/test HEAD before creating this report: `6cd955cf568a27324da3c140715f7db3cdb23c3f` (PR #8 remained Draft and unmerged when checked).
- main at `7a843f17eb96ed13d66f23b58b06406b3002e405`; protected Draft PR #5 at `805b377697472268db02650a89c7a94b1c5337c8`; **UI-paused/untouched** Draft PR #9 at `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`.
- Frozen V1/V2/Local UI/Launcher evidence, V3 Contract 1 and final-evaluation barriers unchanged.

## NEW packages (ordinary GitHub Contents API writes; no raw Git object mutation)

### A. Windows expected-READ manifest publication/load integrity and actual CI failure

- [Prior checkpoint CI #42533084475](https://github.com/Iam-2squared/ark-ai/actions/runs/42533084475) completed **4/6 GREEN, 2/6 FAIL**: Ubuntu Python 3.11/3.12/3.13 and Windows 3.11 GREEN; Windows 3.12 **6 FAIL / 11,272 PASS / 62 SKIP**; Windows 3.13 **7 FAIL / 11,271 PASS / 62 SKIP**. Failures concentrated in detached READ manifest creation/loading and metadata-race fixtures. These are real observed CI failures, not generalized claims about other modules.
- [Production `50fc1ee2`](https://github.com/Iam-2squared/ark-ai/commit/50fc1ee2ea4b61975508d912c166dac04f923784) distinguishes same-source metadata epochs from Windows handle-versus-path timestamp differences. On Windows publication must **reopen the named artifact and compare its exact bytes** with the write-once payload, verify opened-file identity and stable same-handle epochs; both OSes retain size, inode, link-count and baseline/late-file checks. Read path observes same-handle and two named-file epochs, and refuses read-time drift. POSIX original cross-handle/path epoch check remains. These local checks are NOT an immutable or independently authenticated receipt.
- [Race fixture `048a4961`](https://github.com/Iam-2squared/ark-ai/commit/048a496148c35e7bc566ec0bd14529684e05287a) now injects the changed *late* named-file stat after an untouched baseline. This is a realistic race on both Windows and POSIX instead of a permanently substituted named-file timestamp. Neither test nor production guard authorizes replay or dispatch.

### B. Memory expiry candidate read-only snapshots

- [Production `d85261e7`](https://github.com/Iam-2squared/ark-ai/commit/d85261e72ff76d88efaa1e4abae3327354588aa6) checks **all** `sqlite_sequence` entries for `memory_events` inside the existing SQLite read snapshot, instead of trusting `fetchone()`. SQLite does **not** make `sqlite_sequence.name` unique; a valid first marker plus an injected second marker must be refused even for an empty due page.
- [Three new parameter cases `8d2b3323`](https://github.com/Iam-2squared/ark-ai/commit/8d2b332360d400dee5fad73cba991459bff9541d) cover due page, no-due page, and foreign owner; include retained-receipt recheck and no-repair assertion. This is local corruption detection, not authenticated event custody, erase consent or trusted time.

### C. Atomic Memory epoch snapshot

- [Production `86b56762`](https://github.com/Iam-2squared/ark-ai/commit/86b56762d4418f423037f5364eb3431f9d796ffb) closes the same `fetchone()` ambiguity in the **multi-scope atomic** row/event reviewer, before any content-free receipt may be returned.
- [Three new parameter cases `d6c2272e`](https://github.com/Iam-2squared/ark-ai/commit/d6c2272e8a6318e360bcd2a890bdb858f911a453) require refusal with selected-owner, foreign-owner-only, and mixed-owner histories. No memory data is returned or repaired by the review.

### D. Memory CAS/ABA generation reuse review

- [Production `36a921f2`](https://github.com/Iam-2squared/ark-ai/commit/36a921f2b7a3d424dd7c08f2713fee08a46e5667) refuses duplicate `memory_events` AUTOINCREMENT sequence markers even if a currently observed row or an absent source could otherwise yield an internally coherent diagnostic.
- [Three new parameter cases `6cd955cf`](https://github.com/Iam-2squared/ark-ai/commit/6cd955cf568a27324da3c140715f7db3cdb23c3f) cover current row, foreign history, and never-existent requested source. Generation review remains **read-only** and non-authorizing; revision reuse is not consent, caller identity or a safe automatic retry.

## Verification / evidence limitations

**Nine authored synthetic parameter-expanded test cases in three new test files** (3+3+3), one existing manifest race test corrected, four non-UI production modules modified. Existing prior CI failure logs inspected on the exact old HEAD; no local full Ruff/pytest or Windows runner is available in this invocation. The post-change CI runs were queued/in-progress when last observed, so **neither latest exact source/test HEAD nor this report/checkpoint has certified 6/6 GREEN**. Do not infer PASS from the earlier successful four jobs.

No manual duplicate workflow runs were dispatched. GitHub Actions may queue automatic PR checks for each normal Contents API commit. No changes to PR #5/#9, frozen contracts/evidence, paid compute, real external backend or hardware.

## Limits and next plan / 今後の方針

1. Verify **exact checkpoint-result HEAD** all six CI jobs. If a Windows or Ruff failure persists, use the actual job traceback for the smallest semantics-preserving correction; switch to independent core lanes while CI runs.
2. Continue Memory CAS/ABA, expiry and COMMIT-UNKNOWN review, emphasizing transaction coherence and independently retained external witnesses; sqlite_sequence and unkeyed digests remain mutable local signals.
3. Continue Planner detached READ input receipts and WAL/restart integrity, Windows byte/handle publication limitations and no automatic replay of UNKNOWN states.
4. Advance ToolRegistry-bound exact-type PermissionGate, durable once-only approval, audit-before-action/occurrence replay prevention and **disconnected/mock-only** executor integration after exact-head GREEN.
5. Preserve free-only V3 identity/path/approval gates and observation/proactive/privacy backend work. Keep PR #5/#8/#9 Draft/unmerged and UI paused. No protected evaluation, Candidate, real tool dispatch or irreversible promotion.

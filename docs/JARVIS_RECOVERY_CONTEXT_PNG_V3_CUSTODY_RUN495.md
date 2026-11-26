# Run495 — V3 file provenance, Planner recovery, Context expiry, and PNG receipt authority

Date: 2026-10-31 Asia/Tokyo/JST. All changes are reversible, local-only,
and confined to isolated Draft PR branches. This report does not establish
JARVIS end-to-end completion or permit real Tool execution.

## Changed source and focused regression coverage

1. **V3 local artifact identity (Draft PR #5).** Prior exact source HEAD
   `ebc83999d83fb108db08be67fea0ece178523f90` failed only on
   Windows Python 3.13 in CI run [#1782](https://github.com/Iam-2squared/ark-ai/actions/runs/41165719631)
   because comparing pathname `st_ctime_ns` to descriptor `st_ctime_ns`
   rejected a stable regular file. Source fix
   `a3fb7ba1d60e6ca77dbb82bac31244d20b288b4c` preserves exact
   file-ID (`os.path.samestat`), size, mtime and single-link checks across
   sources and compares full metadata epochs **within each source**.
   Test commit `c42521c16b7d52cd39c4c2aff413ab001c321b29` adds
   same-length replacement, descriptor-ID mismatch and Windows ctime
   portability regressions (3 functions / 3 cases). Exact test HEAD CI
   [#1787](https://github.com/Iam-2squared/ark-ai/actions/runs/41169960149)
   **6/6 GREEN** (Ubuntu/Windows, Python 3.11–3.13, per-job verification).
   Local path hashing remains best-effort; it is not trusted writer evidence.

2. **Planner offline WRITE recovery fence (Draft PR #8).** Source
   `4efc312a9e8aaec7baf156ca1de43c8c7cc62d6b`, test
   `af8d2b56a322730ef85ee7d0abb0a2b71e45cc18`.
   A reflected non-authorizing result getter could return False while
   changing original step state, disposition or report digest **after**
   prior checks. Revalidate all original carriers and result fields after
   final flag inspection. Three regression functions/cases. UNKNOWN and
   RUNNING WRITE remain quarantined; no automatic replay or dispatch.

3. **Privacy-safe Context membership (Draft PR #8).** Source
   `61c0404d6c88bcb3f6ae9a39eab22a8b7dedaab1`, test
   `0859da4e9bf1adef47bf518dab018eaa7a00d4f2`.
   Recheck record and scope-veto carriers after non-authorizing result
   getters to reject late revocation, expiry and forged result SHA.
   Two test functions / three expanded cases. No actual consent, context
   disclosure or durable revocation action.

4. **Disconnected PNG observation inventory (Draft PR #8).** Source
   `5d26550f63c1cc1cbd046636d7e37e6de61d21a0`, test
   `fb8843bd331fae3f122b878be0a97aaa02c1a575`.
   Validate exact result type, original image identity fields, bounded
   image metadata and all four denied authority descriptors. Recheck
   original request and result fields after final reflected getter.
   Six test functions / nine expanded cases. No image decoder, camera,
   live input, privacy release or real observation integration.

**Total NEW: 14 test functions / 18 parameter-expanded cases across four
independent packages.** No preemptive PASS claim is made for PR #8 until
the exact latest source-and-test revision completes all six matrix jobs.

## Strict CI/evidence at report drafting

- PR #8 previous Run494 source `8e9fcccf5112617bf49ad6b6547ca5564d81dbb8`,
  CI [#1783](https://github.com/Iam-2squared/ark-ai/actions/runs/41165783405):
  **6/6 GREEN**; later Run494 checkpoint CI #1785 also GREEN.
- PR #5 previous Run494 source `ebc83999d83fb108db08be67fea0ece178523f90`,
  CI #1782: **FAIL 1/6** (Windows 3.13). Run495 fixed as above, latest
  #1787: **6/6 GREEN**.
- PR #8 Run495 latest source/test `fb8843bd331fae3f122b878be0a97aaa02c1a575`,
  CI [#1793](https://github.com/Iam-2squared/ark-ai/actions/runs/41170158527):
  **QUEUED at drafting**, not yet GREEN. Planner #1789, Context #1791 and
  observation #1792 are source-stage checks, not substitutes for #1793.
- Independent local full pytest/Ruff: **NOT VERIFIED**, direct git network
  DNS failed. No workflow rerun dispatched manually.

## Frozen boundaries and next priorities

Frozen unchanged: Memory v1 `b6e93821ecd69270a7634aceb20775dc36e9953c`;
Agency v1 `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`;
V3 contract `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`;
V3 companion hash blob `176154514bd6be22685ca0555bc682c3bd8d45dc`.
No V1/V2/Local UI/Launcher freeze modification.

No paid/external GPU, paid API, purchased resource, real Candidate,
protected V2 final suite, user secrets, external account connection,
real Tool, irreversible operation, main merge or automatic promotion.
PR #5 and PR #8 remain Draft/unmerged. Current local metadata cannot
authenticate independent writers, trusted clocks, humans, consent,
coherent cross-database atomicity, or real-world outcomes.

Next: confirm latest #1793 six-job matrix and repair any exact-head
regression; advance Memory CAS/history source integrity, Planner manual
WRITE recovery, trusted-clock audit-before-action, durable Scheduler
replay fences and opt-in multimodal mock readiness without crossing gates.

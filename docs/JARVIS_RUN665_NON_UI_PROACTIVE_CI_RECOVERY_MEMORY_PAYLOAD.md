# ARK AI — Run665: proactive preaccess CI recovery and exact Memory payload custody

Scope: **free-only, disconnected non-UI** work on Draft PR #8,
`research/jarvis-foundations`. This is an implementation/test evidence
note, not an independent security certification, consent, signed provenance,
or authorization to dispatch anything.

## Initial evidence and failure diagnosis

Initial work-basis HEAD: `53e1d1c4efd10ae9671c2b0226959cde84f3dfba`.
The previous checkpoint's exact-HEAD
[Actions run #42247009650](https://github.com/Iam-2squared/ark-ai/actions/runs/42247009650)
completed **FAIL (all 6 jobs)**, contrary to the earlier queued status.
Actual Ubuntu Python 3.11 job `127991747735` recorded **10 failed,
9878 passed, 1 skipped**. The failures were limited to old proactive
receipt tests: a newly introduced *preaccess* receipt-class authority check
now rejects altered constructors/descriptors **before** SQLite COMMIT,
whereas older tests expected a row to have already committed. A hard-exit
test also tried to inject `SyntheticTriggerReceipt = lambda ...`, which
cannot reach COMMIT under the now-correct ingress check. These failures
are real mismatches in prior regression fixtures, not GREEN evidence.

## Work packages saved (sequential normal GitHub Contents writes)

1. `7577f253b742ab403afb184e011c53a8656487a4` —
   `tests/test_proactive_receipt_original_authority_run593.py`: update
   previously post-COMMIT assumptions for preinstalled descriptor/getter
   drift to require **zero** durable markers; injected getters must not run.
   Add one new **true post-COMMIT** test using a SQLite connection wrapper
   that mutates a False-only descriptor only after `raw.commit()`, proves
   a rejection while the persisted marker remains, and denies duplicate
   re-admission. The production preaccess guard is *not* weakened.
2. `c1a09727d03e83b9a442837b202eaa6506cf0b8e` —
   `tests/test_proactive_commit_policy_custody_run416.py`: a receipt
   class rebinding at ingress must be refused **before persistence**, rather
   than pretending to be a post-COMMIT forgery. Verify an unmodified
   subsequent preparation succeeds once and duplicate use is rejected.
3. `b98b9438f157585ba9f6de28ba5e3acb1ffb2dcd` —
   `tests/test_hard_exit_local_durability_run436.py`: use a disposable
   child-process SQLite `mode=rw` connection proxy, exit `44` immediately
   after the real `raw.commit()`, then reopen to inspect a single marker
   and ensure duplicate preparation cannot occur. The preaccess authority
   check stays intact and the fixture still performs **no** external action.
4. `b08523684bb97fdaf59d42f55787f3ea419f1e44` —
   three new parametrized Memory cases
   (`tests/test_memory_ambiguity_exact_payload_run665.py`). A second
   independent SQLite handle writes a same-looking but not exact proposed
   update: **different metadata**, **different finite expiry**, or
   **composed/decomposed Unicode content**. The independent read-only
   COMMIT-UNKNOWN pair reviewer must return `DIVERGED_MANUAL_REVIEW`,
   not authenticate caller commit/retry/write/trusted clock. The fixture
   re-reads events and row to ensure review did not mutate persisted state.

Total **4 authored new test cases** (one post-COMMIT receipt regression,
three Memory parameter cases) plus corrections to previously existing
receipt/hard-exit tests. No production-source modification this run.

## Actions verification at report creation

- Original failing HEAD: [#42247009650](https://github.com/Iam-2squared/ark-ai/actions/runs/42247009650) **FAIL, 6/6**.
- [#42255813457](https://github.com/Iam-2squared/ark-ai/actions/runs/42255813457),
  [#42255884939](https://github.com/Iam-2squared/ark-ai/actions/runs/42255884939),
  [#42255933764](https://github.com/Iam-2squared/ark-ai/actions/runs/42255933764),
  [#42256308747](https://github.com/Iam-2squared/ark-ai/actions/runs/42256308747):
  **IN PROGRESS at last sampled run listing**, not exact combined GREEN.
  These runs are on successive HEADs and cannot automatically validate
  a later checkpoint. No manually duplicated workflow or local all-suite
  PASS is claimed. Inspect individual six job results before asserting
  a combined exact-head PASS; correct any further failure by normal Contents
  writes only, not Git-object/ref bypasses.

## Preserved boundaries and limitations

No UI/Frontend work. PR #9 `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`
remains Draft; PR #5 `805b377697472268db02650a89c7a94b1c5337c8`
remains Draft/blocked. `main` observed at
`7a843f17eb96ed13d66f23b58b06406b3002e405`.
Frozen V1/V2, Local UI, Launcher, and evaluation contracts/evidence are
unchanged. No real tool backend, credentials, paid services, external
GPU/compute, physical-PC operation, Candidate generation/promotion,
protected V2 evaluation opening, or unauthorized merge.

The mock SQLite commit boundary is a **local test oracle**, not a trusted
external effect, caller attribution, durable consent or exactly-once proof.
Current ARK overall JARVIS/V3 state remains **NOT_PASSED**.

## Prioritized follow-up

1. Verify corrected **exact-head** CI all six jobs. If FAIL, inspect actual
   job logs, repair the smallest semantics-preserving regression, and work
   on an independent non-UI lane while the next CI executes.
2. Continue Memory coherent snapshots, expiry/ABA and manual-only
   COMMIT-UNKNOWN evidence without any automatic ambiguous WRITE replay.
3. Require verified Planner SUCCEEDED result/effect receipts before connecting
   recovery to registry and permission gates; preserve fail-closed mocks.
4. Advance immutable ToolRegistry, exact-type PermissionGate,
   trusted-clock audit-before-action and replay barriers in reversible
   disconnected fixtures only. Personal Context, proactive and observation
   privacy paths remain separate non-UI lanes.

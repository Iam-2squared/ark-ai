# ARK AI — Canonical Project Status

**LATEST — 2026-10-31 / Run495: four free-only packages, 14 new pytest functions / 18 expanded cases; V3 Windows regression repaired and verified 6/6.**

**Saved at:** **2026-10-31T13:51:40+09:00 Asia/Tokyo/JST** (local-time source read immediately before this Contents write; **not** a trusted or attested clock).

**Overall ARK/JARVIS: NOT_PASSED.** Local, detached/mock foundations are advancing; no end-to-end JARVIS PASS, authenticated independent SQLite custody, real execution, user consent, model Candidate, protected V2 final evaluation, or human review is established.

## LATEST branch and SHA provenance

- **JARVIS foundations:** [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), branch `research/jarvis-foundations`, OPEN / DRAFT / UNMERGED. **Initial invocation work-basis HEAD** `5ec2ed88d09f44b7ecddbcc7cb4db111118b6bf8` (Run494 checkpoint). **Final source/test HEAD** `fb8843bd331fae3f122b878be0a97aaa02c1a575`. **Checkpoint-write-basis HEAD** `be65aacb4b2b986a659cb33da93e1b37eda60928` (Run495 technical report). **Checkpoint-result HEAD** is the new commit from the GitHub Contents write, verified with a subsequent branch read, not asserted by a self-referential SHA inside the checkpoint.
- **V3 independent:** [Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5), branch `research/v3-learning-evaluation`, OPEN / DRAFT / UNMERGED. Initial invocation HEAD `ebc83999d83fb108db08be67fea0ece178523f90`. **Final source/test HEAD** `c42521c16b7d52cd39c4c2aff413ab001c321b29`.
- **main** `7a843f17eb96ed13d66f23b58b06406b3002e405`, no changes by this invocation.
- Full code/test provenance: [Run495 technical report](JARVIS_RECOVERY_CONTEXT_PNG_V3_CUSTODY_RUN495.md), saved as `be65aacb4b2b986a659cb33da93e1b37eda60928`.

## NEW work this invocation — four independent, reversible packages

1. **V3 file/hash portability:** `src/ark/learning/lineage.py`, source `a3fb7ba1d60e6ca77dbb82bac31244d20b288b4c`; tests `c42521c16b7d52cd39c4c2aff413ab001c321b29` (3 functions/cases). Windows pathname/descriptor ctime semantics no longer falsely reject a stable file, while same-file identity, size, mtime, link-count and intra-source metadata changes remain guarded. One previous Windows Python 3.13 CI regression resolved.
2. **Planner mixed READ/WRITE restart quarantine:** `src/ark/agency/disconnected_write_recovery_fence.py`, source `4efc312a9e8aaec7baf156ca1de43c8c7cc62d6b`, tests `af8d2b56a322730ef85ee7d0abb0a2b71e45cc18` (3 cases). Recheck original step/disposition/report after reflected result permission getters. UNKNOWN/RUNNING WRITE stays quarantined.
3. **Privacy-safe Personal Context:** `src/ark/offline_context_membership_guard.py`, source `61c0404d6c88bcb3f6ae9a39eab22a8b7dedaab1`, tests `0859da4e9bf1adef47bf518dab018eaa7a00d4f2` (2 functions/3 cases). Late revocation, record expiry and forged result SHA are rejected after result getter evaluation.
4. **Offline PNG observation fixture:** `src/ark/offline_png_inventory.py`, source `5d26550f63c1cc1cbd046636d7e37e6de61d21a0`, tests `fb8843bd331fae3f122b878be0a97aaa02c1a575` (6 functions/9 cases). Exact result metadata, denied sensor/consent/disclosure authority and post-construction request/result custody now checked. No camera, image decode, or content release.

**Total NEW: 14 pytest functions, 18 expanded cases.** The new PR #8 tests are not counted as GREEN before their exact-head CI completes.

## CI / tests — exact source HEAD only

- **Previous PR #8 Run494 source** `8e9fcccf5112617bf49ad6b6547ca5564d81dbb8`: [#1783 / 41165783405](https://github.com/Iam-2squared/ark-ai/actions/runs/41165783405) **6/6 GREEN**, reverified on all Ubuntu/Windows Python 3.11–3.13 jobs; last checkpoint #1785 also 6/6 GREEN.
- **Previous PR #5 Run494 source** `ebc83999d83fb108db08be67fea0ece178523f90`: [#1782 / 41165719631](https://github.com/Iam-2squared/ark-ai/actions/runs/41165719631) **FAIL 1/6**, Windows Python 3.13 ordinary file rejected by pathname/handle ctime mismatch; source repaired without dropping tests.
- **Current PR #5 Run495 final source/test** `c42521c16b7d52cd39c4c2aff413ab001c321b29`: [#1787 / 41169960149](https://github.com/Iam-2squared/ark-ai/actions/runs/41169960149) **6/6 GREEN**, verified job-by-job.
- **Current PR #8 Run495 final source/test** `fb8843bd331fae3f122b878be0a97aaa02c1a575`: [#1793 / 41170158527](https://github.com/Iam-2squared/ark-ai/actions/runs/41170158527), **1 job IN PROGRESS + 5 QUEUED at last job read**, not GREEN. Earlier independent Planner #1789, Context #1791 and PNG-source #1792 also running or queued. Report-only [#1794 / 41170205011](https://github.com/Iam-2squared/ark-ai/actions/runs/41170205011) **6 QUEUED**, not source proof.
- Independent full local pytest/Ruff: **NOT VERIFIED** (container direct git DNS unavailable). No manual duplicate workflow runs.

## Frozen contracts/evidence and authorization boundaries — unchanged

- Frozen Memory v1 `src/ark/memory/contracts.py` blob `b6e93821ecd69270a7634aceb20775dc36e9953c`, Agency v1 `src/ark/agency/contracts.py` blob `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`.
- Frozen V3 `docs/v3/CONTRACT.md` blob `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23` and companion hash-file blob `176154514bd6be22685ca0555bc682c3bd8d45dc`; all four re-read unchanged. V1/V2/Local UI/Launcher gates and evidence retained.
- **No paid/external compute, paid API, GPU training, real Candidate/weight generation, protected V2 final suite, promotion, external Tool execution, account connection, secrets, irreversible action, main merge, or frozen-contract change.** PR #5 remains Draft/unmerged under its controlling gate; PR #8 likewise Draft/unmerged.
- Detached local hashes/SQLite witnesses do **not** prove an independent writer, consent, trusted time, coherent cross-store atomicity, or a real-world outcome. UNKNOWN WRITE retains fail-closed quarantine. PR #5 still lacks authorized human review/real identities/cost approval.

## Next plan / 今後の方針

1. **CI closure:** confirm #1793 and the final checkpoint run's six jobs; investigate any failures at the exact commit and repair smallest source/test issue through the normal permitted path. No redundant workflow re-dispatch.
2. **Memory:** schema, row/event integrity, CAS concurrency, expiry, independently retained tip evidence and coherent state diagnostics.
3. **Planner and Agency:** manual UNKNOWN WRITE recovery diagnostics, immutable registry identities, exact-type permissions, trusted-clock audit-before-action and occurrence/replay fencing; integration only after lower-level exact-head GREEN.
4. **Personal Context, Scheduler and multimodal:** independent revocation/retention veto, durable due/replay gates, disconnected observation fixtures; preserve no-sensor/no-disclosure defaults.
5. **V3 free lane:** local identity/provenance/reproducibility/approval guards only; do not open the protected V2 evaluation or initiate real training.

---

**Prior intact latest checkpoint:** [Run494 at `5ec2ed88d09f44b7ecddbcc7cb4db111118b6bf8`](https://github.com/Iam-2squared/ark-ai/blob/5ec2ed88d09f44b7ecddbcc7cb4db111118b6bf8/docs/PROJECT_STATUS.md). Earlier statuses and Run487–494 reports remain in git history/docs; no frozen or historical evidence rewritten.

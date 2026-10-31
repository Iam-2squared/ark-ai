# ARK AI — Canonical Project Status

**LATEST — 2026-10-31 / Run493: five free-only source packages, two CI regression repairs, V3 Windows identity fix, inert Observation lineage and Personal Context retention reviews; 4 new pytest functions / 8 cases.**

**Saved at:** **2026-10-31T11:48:18+09:00 Asia/Tokyo/JST**, reported by a local-time source immediately before the normal GitHub Contents update; **not authenticated trusted time**.

**Overall ARK/JARVIS: NOT_PASSED.** These are isolated, reversible local/mock foundations, not verified autonomous JARVIS, real Tool execution, independent writer provenance, actual user consent, protected V2 evaluation, V3 Candidate, or end-to-end launch PASS.

## LATEST branches / SHA provenance

- **JARVIS foundations:** [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), `research/jarvis-foundations`, OPEN / DRAFT / UNMERGED. **Run493 initial work-basis HEAD:** `2283b700b682ad710c648009d14f230d657ed899` (Run492 checkpoint). **Final Run493 source/test HEAD:** `b3a9c941ee80c768ed8e9db0a69d4195c18dae7d`. **Evidence and checkpoint-write-basis HEAD:** `cb0870e09e86c5596d6769b52ffa760d6de2e501`. The **checkpoint-result HEAD cannot be included** in the commit's own content without circular self-reference. GitHub's returned commit SHA and a subsequent PR-head recheck establish it.
- **V3 independent branch:** [Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5), `research/v3-learning-evaluation`, OPEN / DRAFT / UNMERGED. **Initial Run493 HEAD:** `d96ac89ac576483514bc6d715015a5f0736faaca`. **Final source/test HEAD:** `7bd2ad6450c3a887351705f11054313de49c809c`.
- **Main:** `7a843f17eb96ed13d66f23b58b06406b3002e405`, unchanged. No main merge, force push, raw Git-object bypass or irreversible operation.

## NEW work in this invocation — five packages

1. **Scheduler due witness**: Reordered custody-carrier identity and semantic checks so callback swaps of retained witness count/hash reject with the pre-existing custody-drift diagnostic before committing. Commit `e80161e7c61ed703c1c9fb680e965a6e742b4566`; previous `test_due_reservation_receipt_epoch_run474.py` remains unchanged.
2. **Memory CAS witness**: Verify retained caller epoch after SQLite read callback and before validating the observed witness; prevents scope/authority drift from masking its original failure. Commit `04520d17373d9cfe78ad2d6920bc6d68a80b7265`; previous `test_memory_witness_authority_drift_run491.py` remains unchanged.
3. **V3 file descriptor**: Compare path/fd via nonzero file IDs, `os.path.samestat`, size/mtime; check the complete descriptor epoch against itself and path epoch against itself. Windows path `st_ctime_ns` can differ from `fstat` while the file is the same; do not conflate that with a hostile redirection. POSIX also compares cross-source mode/ctime. Commit `7bd2ad6450c3a887351705f11054313de49c809c`. No base/tokenizer download, GPU, weights or training.
4. **Observation inert lineage witness**: Forbid a reflected exact DTO class-property spoof from asserting media capture, disclosure or dispatch authorization. Source `4be98d3b836cf3a75c382750bece9d2bc08c7d50`; test `3865f053f94d56fcfbe43a1cc823e5f4af16a657`. Three parametrized rejection cases + one positive.
5. **Personal Context retention inventory**: Forbid an exact DTO class-property spoof from asserting completed erasure, deletion authorization or context use. Source `1adac559a7822371c22884ba9826ecf4c9a025e0`; test `b3a9c941ee80c768ed8e9db0a69d4195c18dae7d`. Three parametrized rejection cases + one positive.

**Totals:** 4 new pytest functions / 8 expanded cases. Two earlier failing regressions repaired in source without removing or broadening tests. All work remains offline and non-authorizing.

**Detailed evidence:** [Run493 technical report](JARVIS_CI_RECOVERY_OBSERVATION_PRIVACY_RUN493.md), saved at checkpoint-write-basis `cb0870e09e86c5596d6769b52ffa760d6de2e501`.

## Tests and CI — exact source HEAD required

- **Earlier Run492 PR #8 source** `ca92275b755d502a9e1ddfa69b04272d1667c7ae`, [#1762 / 41157215683](https://github.com/Iam-2squared/ark-ai/actions/runs/41157215683): **FAIL**, 6/6 jobs; two mismatched exception-message expectations despite preserved denial semantics. Both fixed by the new source changes, old tests retained.
- **Earlier Run492 PR #5 source** `d96ac89ac576483514bc6d715015a5f0736faaca`, [#1761 / 41157173741](https://github.com/Iam-2squared/ark-ai/actions/runs/41157173741): **FAIL** Windows 3.12/3.13, other four success. Fixed portability issue in local identity descriptor handling.
- **PR #5 final source** `7bd2ad6450c3a887351705f11054313de49c809c`, [#1767 / 41161362307](https://github.com/Iam-2squared/ark-ai/actions/runs/41161362307): **6/6 GREEN** on Windows/Ubuntu Python 3.11–3.13, verified per job.
- **PR #8 intermediate fix source** `04520d17373d9cfe78ad2d6920bc6d68a80b7265`, [#1766 / 41161305228](https://github.com/Iam-2squared/ark-ai/actions/runs/41161305228): **IN PROGRESS** at prior inspection; not current head.
- **PR #8 intermediate Observation source/test** `3865f053f94d56fcfbe43a1cc823e5f4af16a657`, [#1769 / 41161452273](https://github.com/Iam-2squared/ark-ai/actions/runs/41161452273): **IN PROGRESS** at prior inspection; not current head.
- **PR #8 final Run493 source/test** `b3a9c941ee80c768ed8e9db0a69d4195c18dae7d`, [#1771 / 41161548147](https://github.com/Iam-2squared/ark-ai/actions/runs/41161548147): **6 jobs QUEUED** at last exact-head inspection. **Not GREEN**. Documentation/checkpoint-only commits do not prove this changed source/test SHA.
- **Independent local full pytest and Ruff:** **NOT VERIFIED**; evidence is from GitHub Actions only. No duplicate manual workflow dispatch.

## Frozen contracts and explicit authorization blockers

- Frozen **Memory v1** `src/ark/memory/contracts.py` blob `b6e93821ecd69270a7634aceb20775dc36e9953c`; **Agency** `src/ark/agency/contracts.py` blob `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`: unchanged by fresh read.
- Frozen **V3 Contract** `docs/v3/CONTRACT.md` blob `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`, hash-companion blob `176154514bd6be22685ca0555bc682c3bd8d45dc`: unchanged. V1/V2/Local UI/Launcher evidence, protected V2 final-evaluation, Contract 1 Experiment 001, provenance, contamination, reproducibility and regression gates were not modified.
- **No paid/external compute, GPU, paid APIs/services, new credentials/account, real Candidate/adapters/weights, protected V2 final suite, promotion, actual Tool dispatch, physical-PC operation, user consent or human-review decision, deletion/erasure, or main merge.**
- SQLite hashes/CAS are not independent writer authentication, trusted clocks, globally atomic snapshots or exactly-once external effects. UNKNOWN/RUNNING WRITE remains quarantined without automatic retry. V3 remains Draft, blocked on verified actual model/tool/runtime identities, human dataset review, billing/cost cap and explicit gates.

## Next plan / 今後の方針

1. Confirm [PR #8 #1771](https://github.com/Iam-2squared/ark-ai/actions/runs/41161548147) on all six exact-head matrix jobs; investigate logs if any fail, make only minimal semantics-preserving fixes via normal GitHub path, no duplicate CI dispatch.
2. Advance Memory row/event CAS and independently retained coherent history; Planner registry-bound Tool identity and manual UNKNOWN WRITE recovery; trusted-clock audit-before-action and occurrence/replay fencing in mock-only fixtures.
3. Extend Scheduler durable reservations, Personal Context revocation/expiry/consent-denial, Observation input-lineage and startup readiness; integrate only after exact-head GREEN evidence.
4. Continue **free-only V3** identity, approval and reproducibility guards. Explicit authorization required for anything potentially billable, Candidate, protected V2, frozen-contract changes and main merge.

---

**Previous unchanged status:** [Run492 canonical checkpoint `2283b700b682ad710c648009d14f230d657ed899`](https://github.com/Iam-2squared/ark-ai/blob/2283b700b682ad710c648009d14f230d657ed899/docs/PROJECT_STATUS.md). Older Run491–487 snapshots and through-Run487 history remain accessible via earlier commits and `docs/history/`; no frozen historical evidence rewritten.

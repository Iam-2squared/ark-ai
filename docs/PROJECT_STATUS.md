# ARK AI — Canonical Project Status

**LATEST — 2026-10-31 / Run491: five free-only source/test packages, 11 new pytest functions; V3 recovered from Ruff failure; Planner/Memory/Personal Context/Scheduler witness custody hardened.**

**Saved at:** **2026-10-31T09:47:05.694+09:00 Asia/Tokyo/JST**, observed from the current runtime immediately before requesting the normal GitHub Contents update. This is local wall-clock time, **not authenticated trusted time**.

**Overall ARK/JARVIS completion: NOT_PASSED.** New work is reversible, disconnected, mock/local-first safety engineering; not an integrated JARVIS, trusted-clock proof, independently authenticated consent or audit, exactly-once external execution, Candidate promotion, protected V2 final evaluation, or a merge gate.

## LATEST: exact branch/PR/head checkpoint basis

- **JARVIS foundations:** [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), `research/jarvis-foundations`, **OPEN / DRAFT / UNMERGED**. **Initial work-basis HEAD**: `e1ae5e350d1c90c21f994687a1d14fc68bc72ca1` (Run490 checkpoint). **Run491 final source/test HEAD**: `d70d48a889d0481a6c98178a2c8c2d27f469c5c2`. **Technical-evidence and checkpoint-write-basis HEAD**: `26bd9fca45255ed5a0825d6001e52eec28535c17`. The precise **checkpoint-result HEAD** cannot be embedded in its own pre-commit file; it is the commit SHA returned by this normal GitHub Contents write and must be verified separately against the latest branch HEAD.
- **Separate free-only V3:** [Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5), `research/v3-learning-evaluation`, **OPEN / DRAFT / UNMERGED**. Initial work-basis/source HEAD `7cebbbbd3e0915028a1aa447b0baf7511df8a49e`; Run491 final source/test HEAD `7d3d1fe69e5d8e550ea444510c793395047d99f7`.
- **Main:** `7a843f17eb96ed13d66f23b58b06406b3002e405`, last verified this invocation. No main merge, force push, Candidate promotion or destructive operation was done.

## NEW Run491 work — five packages / 11 new pytest functions

1. **V3 Artifact lineage Ruff fix** (PR #5). Restored Ruff E501 compliance in `src/ark/learning/lineage.py` by splitting one existing `ValueError` string into multiple lines. The error message, stable SHA-256 path/file custody checks and frozen V3 evaluation gates remain unchanged. Latest blob `2e747b340b97a9f22bfb64b611c9507fb3aa3ef1`.
2. **Planner SQLite WRITE-slot custody** (PR #8, **3 tests**). Pin the exact path carrier across startup/inspect/reservation and require exact retained witness identity and denied-authority flags after callbacks. `tests/test_write_slot_custody_run491.py` exercises equal-text path rebinding, equal-value SHA carrier replacement and pre-insert mutation. UNKNOWN/RUNNING WRITE remains quarantined without automatic replay.
3. **Memory SQLite witness CAS/startup** (PR #8, **2 tests**). Reject source-path rebinding during existing-store startup and re-check denied-authority flags on every append callback before SQLite INSERT/COMMIT. `tests/test_memory_witness_authority_drift_run491.py` covers restart source tampering and permission-property spoofing; no Memory content bytes are persisted in this witness fixture.
4. **Personal Context replay ledger read-side authority** (PR #8, **3 tests**). Read-only startup and `witness()` now reject spoofed classes and forged custody flags while preserving the exact source path across startup. `tests/test_context_replay_readonly_authority_run491.py`. Hash-only identifiers remain linkable metadata, not consent or permission to disclose.
5. **Scheduler due-slot witness read-side authority** (PR #8, **3 tests**). Validate exact witness type/shape and non-authority at startup, retained restart, read-only snapshot, and synthetic CAS inspection, including after reading. `tests/test_due_witness_readonly_authority_run491.py`. No actual dispatch, notifications, or trusted-clock authentication.

**Technical evidence:** [Run491 report](JARVIS_WRITE_MEMORY_CONTEXT_V3_RUN491.md), saved under evidence HEAD `26bd9fca45255ed5a0825d6001e52eec28535c17`. This is separate from the source/test HEAD. All changes used the normal GitHub Contents API; no raw Git-object bypass or force push.

## CI and tests — exact source SHA, no optimistic PASS

- **V3 prior FAIL:** [#1734 / 41146607177](https://github.com/Iam-2squared/ark-ai/actions/runs/41146607177), all six jobs FAIL due to Ruff `E501` at `src/ark/learning/lineage.py:111`. This failure was inspected directly in Ubuntu 3.12 logs.
- **V3 fixed exact source:** `7d3d1fe69e5d8e550ea444510c793395047d99f7`, [#1740 / 41151476912](https://github.com/Iam-2squared/ark-ai/actions/runs/41151476912), **all 6 Ubuntu/Windows Python 3.11–3.13 jobs GREEN**. No protected evaluation or training took place.
- **JARVIS intermediate:** Planner source/test `d08be0f17fffd4f9f19ad0ac57a5261f895a49fa`, [#1742 / 41151591156](https://github.com/Iam-2squared/ark-ai/actions/runs/41151591156), previously IN PROGRESS; Memory source/test `f9c5a0074efd1f3af7e83f4e6d6c21c86ecc9268`, [#1744 / 41151670013](https://github.com/Iam-2squared/ark-ai/actions/runs/41151670013), previously IN PROGRESS; Context source/test `416504daed39d35cebd59da3f4d13deb79f5ad02`, [#1746 / 41151728454](https://github.com/Iam-2squared/ark-ai/actions/runs/41151728454), previously QUEUED. These do **not** prove success of later HEADs.
- **JARVIS latest source/test** `d70d48a889d0481a6c98178a2c8c2d27f469c5c2`, [#1749 / 41151918888](https://github.com/Iam-2squared/ark-ai/actions/runs/41151918888), **QUEUED as checked before this checkpoint**. Six-job GREEN is not claimed unless verified for this exact SHA.
- **PR #5 latest run at checkpoint:** COMPLETED / SUCCESS. No manual duplicate equivalent run dispatched.
- **Local full pytest/Ruff:** **NOT VERIFIED**; direct local git access failed DNS resolution. GitHub connector reads, GitHub Actions and local execution are distinct evidence sources. No test results or human review have been invented.

## Frozen evidence, limits, approval boundaries

- Frozen Memory contract `src/ark/memory/contracts.py` blob `b6e93821ecd69270a7634aceb20775dc36e9953c` and Agency contract `src/ark/agency/contracts.py` blob `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9` re-verified unchanged this run. V1/V2/Local UI/Launcher evidence, V3 Contract 1, provenance/contamination/regression/reproducibility controls, and protected V2 final suite were not modified by this work; not an exhaustive read-only audit.
- No paid compute/external GPU, paid APIs, services or subscriptions, new credentials/account connections, real Candidate/weight generation, protected final evaluation opening, actual OS/microphone/network/tool actions, consent assertion, automatic WRITE replay, irreversible operation, or main merge.
- Detached SQLite witnesses and hash chains cannot authenticate writers, independently custody a retained tip, prove a monotonic trusted time source, give privacy consent, guarantee erasure or exactly-once external effects, or atomically coordinate independent databases. Unknown WRITEs remain isolated. PR #5 remains Draft under its frozen human review, real model/tokenizer/environment identity, cost/billing cap and evaluation gates.

## Next plan / 今後の方針

1. Confirm final **PR #8 source/test** [CI #1749](https://github.com/Iam-2squared/ark-ai/actions/runs/41151918888) across all six jobs. If FAIL, inspect exact failing job logs, apply minimal correctness-preserving fix via normal write path, then validate the new HEAD; no duplicate manual runs.
2. Strengthen Memory CAS/coherent snapshots and independent custody boundary; Planner exact registry-bound PermissionGate, UNKNOWN WRITE manual reconciliation, durable restart and audit-before-action.
3. Keep trusted-clock/occurrence fixtures **inert** until a real authenticated authority design can be proven; Scheduler idempotent due recovery and privacy-safe Personal Context consent/revocation/expiry; mock multimodal Observation.
4. V3 free-only artifact/model/tool/runtime identity, approval scope and reproducibility checks; **no** paid preflight, actual training, Candidate promotion, protected V2 final evaluation, or main merge without explicit gates.

---

**Previous checkpoint (immutable):** [Run490 `e1ae5e350d1c90c21f994687a1d14fc68bc72ca1`](https://github.com/Iam-2squared/ark-ai/blob/e1ae5e350d1c90c21f994687a1d14fc68bc72ca1/docs/PROJECT_STATUS.md). Earlier [Run489](history/PROJECT_STATUS_RUN489.md), [Run488](history/PROJECT_STATUS_RUN488.md), and [through Run487](history/PROJECT_STATUS_THROUGH_RUN487.md) history remain unchanged; all preceding commits and technical evidence remain reachable.

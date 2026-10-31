# ARK AI — Canonical Project Status

**LATEST — 2026-10-31 / Run496: five free-only independent packages; 13 new pytest functions, 30 expanded cases; exact-source CI pending.**

**Saved at:** **2026-10-31T14:45:13.320+09:00 Asia/Tokyo/JST** (clock sampled immediately before GitHub Contents write, not externally attested or trusted).

**Overall ARK/JARVIS: NOT_PASSED.** Local-first/disconnected foundations advance, but end-to-end JARVIS completion, real-world execution, independently authenticated SQLite custody, trustworthy consent/time, real Candidate training, protected V2 evaluation, Candidate promotion, and human review have NOT been demonstrated.

## LATEST branches and work-basis provenance

- **JARVIS foundations:** [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), branch `research/jarvis-foundations`, OPEN / DRAFT / UNMERGED. **Invocation work-basis HEAD:** `e5cf929d9eb16ac6bcd3ac97e4414124000277e1` (Run495 checkpoint). **Final source/test HEAD:** `3730e1ce0bd896c85ab9c7af3d78309b565bb0f9`. **Checkpoint-write-basis HEAD:** `e56165ef1463d398d4808dfb6a215552711c4cf1` (Run496 technical report). **Checkpoint-result HEAD:** assigned by the GitHub Contents write; verify by a subsequent PR/ref read. It is intentionally not guessed inside this self-referential checkpoint.
- **V3 independent branch:** [Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5), `research/v3-learning-evaluation`, OPEN / DRAFT / UNMERGED. **Invocation work-basis HEAD:** `c42521c16b7d52cd39c4c2aff413ab001c321b29`. **Final source/test HEAD:** `1a9abe3fe57c01ab2f03d8f6ad717543d30fc94f`.
- **main:** `7a843f17eb96ed13d66f23b58b06406b3002e405`; unchanged by this invocation. No merge requested or attempted.
- [Run496 implementation, test and evidence report](JARVIS_POST_AUTHORITY_CUSTODY_V3_UTF8_RUN496.md), committed at `e56165ef1463d398d4808dfb6a215552711c4cf1`.

## NEW work this invocation — five reversible free-only packages

1. **Scheduler due-preview post-authority custody:** source `src/ark/disconnected_schedule_preview.py` blob `dec116957c538d223a003a45fb29eca2e1923c5d`. The prior-result non-authority getters can have side effects; now recheck input policy/cursor and immutable due/fingerprint fields after authority probes. 2 pytest functions / 5 cases.
2. **Personal Context request-bound receipt post-authority custody:** `src/ark/personal_context_request_binding.py` blob `e144e478156d68501299b3c8046df62bf1528275`. Detect a False-returning result getter's late mutation of preview or receipt; remain no-consent/no-disclosure. 2 pytest functions / 3 cases.
3. **Offline WAV inventory post-authority custody:** `src/ark/offline_pcm_wav.py` blob `6ce4acafd475576cf7932c1a112bb48039a98dab`. Validate metadata again after the denied microphone/speech/disclosure getters. Corrected the fixture's literal sample bytes without weakening expected checks. 2 pytest functions / 5 cases.
4. **Disconnected Memory delta exact result and authority:** `src/ark/offline_memory_delta.py` blob `d2e100057dadc997319f8d44268f325332a4dd4b`. Reject forged result type/fields, forged source-authentication/erasure/atomicity/dispatch authority, and late mutations. 4 pytest functions / 8 cases.
5. **V3 local artifact identity UTF-8:** `src/ark/learning/lineage.py` blob `8172f94141445f94350fabd6d3abc83c118f8793`. Enforce strict UTF-8 encoding, 4,096-byte string budgets, and DEL-control rejection in metadata identities. Corrected test DEL-literal syntax. No weight files, training or Candidate generation. 3 pytest functions / 9 cases.

**Total: 13 NEW pytest functions, 30 expanded cases.** New source/test coverage is NOT GREEN until exact HEAD CI completes.

## CI / tests / evidence — source-head precision

- **Previous PR #8 source:** `fb8843bd331fae3f122b878be0a97aaa02c1a575`; [CI #1793 / 41170158527](https://github.com/Iam-2squared/ark-ai/actions/runs/41170158527) **6/6 GREEN**, verified by jobs.
- **Previous PR #8 checkpoint:** `e5cf929d9eb16ac6bcd3ac97e4414124000277e1`; [#1795 / 41170295130](https://github.com/Iam-2squared/ark-ai/actions/runs/41170295130) **6/6 GREEN**.
- **Previous PR #5 source:** `c42521c16b7d52cd39c4c2aff413ab001c321b29`; [#1787 / 41169960149](https://github.com/Iam-2squared/ark-ai/actions/runs/41169960149) **6/6 GREEN**.
- **CURRENT PR #8 final source/test:** `3730e1ce0bd896c85ab9c7af3d78309b565bb0f9`; [#1807 / 41173686694](https://github.com/Iam-2squared/ark-ai/actions/runs/41173686694) **6 jobs QUEUED** at last read; no final result asserted.
- **CURRENT PR #5 final source/test:** `1a9abe3fe57c01ab2f03d8f6ad717543d30fc94f`; [#1805 / 41173650595](https://github.com/Iam-2squared/ark-ai/actions/runs/41173650595) **6 jobs QUEUED** at last read; no final result asserted.
- Independent local full pytest/Ruff **NOT VERIFIED**: direct container GitHub DNS resolution unavailable. No duplicate equivalent workflow runs were manually dispatched.

## Frozen contracts, blockers, and authorization boundaries

- Frozen Memory v1 `src/ark/memory/contracts.py` blob `b6e93821ecd69270a7634aceb20775dc36e9953c` — re-read unchanged.
- Frozen Agency v1 `src/ark/agency/contracts.py` blob `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9` — re-read unchanged.
- Frozen V3 contract `docs/v3/CONTRACT.md` blob `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23` and accompanying hash-file blob `176154514bd6be22685ca0555bc682c3bd8d45dc` — both re-read unchanged. V1/V2/Local UI/Launcher evidence untouched.
- **No paid/external compute, paid API, subscription, GPU training, weight/Candidate creation, protected V2 final suite opening, Candidate promotion, external Tool execution, sensor acquisition, account/secret connection, destructive action, or main merge.** Both PRs remain Draft/unmerged.
- Local hashes, dataclass epochs, and false authority flags do not authenticate an independent writer, user consent, trusted clock, multi-store atomicity, genuine deletion, or real-world outcomes. UNKNOWN/RUNNING WRITE remains quarantined: no autonomous retry.
- PR #5 still blocked on real model/tool-byte identities, independent human-approved dataset/contamination decisions, exact runtime identity, cost/billing approval, and later evaluation gates.

## Next plan / 今後の方針

1. **CI closure:** Verify all six jobs of PR #8 #1807 and PR #5 #1805 at the exact source/test HEAD; investigate failures and apply minimal semantics-preserving fixes through normal writes. Do not duplicate existing workflow dispatch.
2. **Memory foundation:** CAS concurrency, bounded expiry, row/event chain custody, coherent read snapshots, external retained evidence and restart integrity.
3. **Planner/Tool/Agency:** manual UNKNOWN WRITE recovery diagnostics, registry-bound identity and exact permissions, trusted-clock audit-before-action, occurrence/replay prevention. Integrate only after exact-head GREEN lower-level evidence.
4. **Personal Context / Scheduler / Observation:** consent revocation and retention veto, durable due/replay fencing, startup readiness and synthetic multimodal fixture checks. Keep live sensors, disclosure and Tool execution disabled.
5. **V3 free lane:** local approval/identity/provenance/reproducibility guard reviews only. Do not generate a real Candidate, open protected V2 evaluation or cross payment boundaries.

---

**Prior preserved checkpoint:** [Run495 at `e5cf929d9eb16ac6bcd3ac97e4414124000277e1`](https://github.com/Iam-2squared/ark-ai/blob/e5cf929d9eb16ac6bcd3ac97e4414124000277e1/docs/PROJECT_STATUS.md). Older PROJECT_STATUS revisions, historical reports and frozen evidence remain in git; none overwritten in their original commits.

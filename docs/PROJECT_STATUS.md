# ARK AI — Canonical Project Status

**LATEST — 2026-10-31 / Run492: five free-only disconnected source/test packages, 8 new pytest functions / 10 test cases. Four local SQLite witness/custody improvements and one V3 file descriptor identity guard.**

**Saved at:** **2026-10-31T10:52:14.537+09:00 Asia/Tokyo/JST**, local wall-clock observed immediately before the normal GitHub Contents update request; **not authenticated trusted time**.

**Overall ARK/JARVIS: NOT_PASSED.** Reversible local/mock work, not integrated autonomous JARVIS, verified real-world actions, independent storage authority, consent, protected V2 approval, V3 Candidate, or end-to-end launch PASS.

## LATEST branch and checkpoint basis

- **JARVIS foundations:** [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8) (`research/jarvis-foundations`): OPEN / DRAFT / UNMERGED. **Run492 initial work-basis HEAD** `7b723453cb84b57d7cb2a283d993706e93e5c3a0` (Run491 checkpoint). **Run492 final source/test HEAD** `ca92275b755d502a9e1ddfa69b04272d1667c7ae`. **Technical-evidence and checkpoint-write-basis HEAD** `bfb2ec03ddacf13d433bf027f07c6fbb134f4289`. The future **checkpoint-result HEAD** cannot be embedded in this self-referential pre-commit file; use the SHA returned by the normal Contents write and independently recheck it against the branch HEAD.
- **V3 separate branch:** [Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) (`research/v3-learning-evaluation`): OPEN / DRAFT / UNMERGED. Initial Run492 HEAD `7d3d1fe69e5d8e550ea444510c793395047d99f7`. **Final source/test HEAD** `d96ac89ac576483514bc6d715015a5f0736faaca`.
- **Main** `7a843f17eb96ed13d66f23b58b06406b3002e405` from the checked PR base. No main merge, Candidate promotion, force push, destructive op or raw Git object bypass.

## NEW work in this invocation — five packages

1. **Scheduler due-slot retained authority**: `disconnected_due_reservation.py` rechecks caller-retained exact witness and independent-custody denial at every reservation callback and after read-only restart. Two tests target spoofing solely the caller witness after SQLite observation; neither reserves a durable row when rejected.
2. **Planner disconnected WRITE ledger**: `disconnected_write_slot_ledger.py` validates retained and SQLite-observed witness exact types, hashes and denied authority before CAS INSERT and after uncommitted verification. Two new tests cover authority spoof before COMMIT and equality-masking string subtype. No auto replay.
3. **Personal Context request replay**: `personal_context_replay_ledger.py` validates the observed witness before synthetic reservation and after INSERT, rather than treating count/hash equality as validation. One parametrized test, two phases. No disclosure authorization.
4. **Memory detached epoch witness**: `memory/disconnected_witness_ledger.py` validates constructed/observed witness at startup, before append and after INSERT, rejecting equal-value nonexact SHA carriers before COMMIT. One parametrized test, two phases. Memory content is not stored.
5. **V3 local file identity**: `learning/identity.py` binds hash input to an opened regular single-link descriptor stat epoch and rechecks descriptor/path after reading; guards against redirected `Path.open` with equal-size alternate bytes. Two offline tests. No HF downloads, weights or training.

**Totals:** eight new test functions / ten cases, plus one source-adjacent test correction for due-only retained spoof timing. Tests and safety predicates were not removed or loosened.

**Technical evidence:** [Run492 report](JARVIS_SQLITE_WITNESS_V3_DESCRIPTOR_RUN492.md), saved at PR #8 evidence HEAD `bfb2ec03ddacf13d433bf027f07c6fbb134f4289`.

## CI and evidence — exact HEADs matter

- **Before Run492, PR #8**: source/test `d70d48a889d0481a6c98178a2c8c2d27f469c5c2`, [Actions #1749 / 41151918888](https://github.com/Iam-2squared/ark-ai/actions/runs/41151918888): **6/6 GREEN**. Not evidence for Run492 changed HEAD.
- **Before Run492, PR #5**: source/test `7d3d1fe69e5d8e550ea444510c793395047d99f7`, [#1740 / 41151476912](https://github.com/Iam-2squared/ark-ai/actions/runs/41151476912): **6/6 GREEN**, not current-head PASS.
- **Run492 PR #8 final source/test** `ca92275b755d502a9e1ddfa69b04272d1667c7ae`, [Actions #1762 / 41157215683](https://github.com/Iam-2squared/ark-ai/actions/runs/41157215683): **6 jobs QUEUED** at last inspection, NOT yet GREEN. Subsequent documentation-only heads must not be confused with final source/test exact SHA.
- **Run492 PR #5 final source/test** `d96ac89ac576483514bc6d715015a5f0736faaca`, [Actions #1761 / 41157173741](https://github.com/Iam-2squared/ark-ai/actions/runs/41157173741): **6 jobs QUEUED** at last inspection, NOT yet GREEN.
- **Independent local pytest/Ruff:** **NOT VERIFIED**; direct `git ls-remote` failed DNS resolution. GitHub connector reads and CI are separate evidence. No duplicate manual workflows dispatched. No test numbers or GREEN are inferred for uncompleted exact-head runs.

## Frozen contracts, limitations, and authorization boundaries

- Memory v1 contract `src/ark/memory/contracts.py` blob `b6e93821ecd69270a7634aceb20775dc36e9953c`, Agency `src/ark/agency/contracts.py` blob `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`, rechecked unchanged.
- V3 Contract `docs/v3/CONTRACT.md` blob `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23` and hash companion blob `176154514bd6be22685ca0555bc682c3bd8d45dc` rechecked unchanged. V1/V2/Local UI/Launcher freeze, V3 Experiment 001 and provenance, contamination, reproducibility, regression and protected V2 final suite boundaries were not modified by this work.
- No paid/external compute, GPU, paid API/service/subscription, new secret/account, real Candidate/adapters/weights, protected V2 final evaluation, automatic promotion, real Tool dispatch/notification, deletion, human-review claim, physical-PC action, or main merge.
- Local SQLite CAS and SHA hashes do not prove writer identity, consent, independent retained-tip custody, authenticated monotonic time, cross-database atomicity or exactly-once external effects. UNKNOWN/RUNNING WRITEs remain quarantined without automatic retry. V3 remains Draft and blocked on real provenance/human approvals, immutable model/tool/runtime byte identities, cost caps and separate explicit gates.

## Next plan / 今後の方針

1. Verify exact-source all-six CI for [PR #8 #1762](https://github.com/Iam-2squared/ark-ai/actions/runs/41157215683) and [PR #5 #1761](https://github.com/Iam-2squared/ark-ai/actions/runs/41157173741); on concrete FAIL, inspect logs, make minimal semantics-preserving correction through the normal path, then validate the new SHA without duplicate runs.
2. Strengthen Memory schema/row/event CAS and externally retained coherent snapshots; Planner exact registry-bound identities, UNKNOWN WRITE human review and durable restart; trusted-clock audit-before-action and exactly-once local claim fencing in disconnected fixtures.
3. Extend Scheduler restart-safe occurrence/replay protection, privacy-safe Personal Context consent/revocation/expiry and mock Observation input integrity, integrating only on exact-head GREEN.
4. Advance **free-only** V3 model/tool/code identity, authorization scope and reproducibility checks. Do not authorize paid preflight, real training, Candidate promotion, protected V2 opening, frozen contract change or main merge.

---

**Previous immutable status:** [Run491 checkpoint `7b723453cb84b57d7cb2a283d993706e93e5c3a0`](https://github.com/Iam-2squared/ark-ai/blob/7b723453cb84b57d7cb2a283d993706e93e5c3a0/docs/PROJECT_STATUS.md). Earlier Run490/489/488 and through-Run487 status history remain reachable under `docs/history/` and original commit ancestry; no frozen evidence was rewritten.

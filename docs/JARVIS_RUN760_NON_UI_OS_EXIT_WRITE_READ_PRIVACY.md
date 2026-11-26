# ARK AI Run760 — OS process COMMIT-UNKNOWN and deny-only cold recovery

**Scope:** FREE-ONLY / NON-UI on Draft PR #8. Five independent, coherent
**test-only** packages covering actual spawned-process exit immediately after a
durable synthetic SQLite boundary and restart in a fresh interpreter. No backend
dispatch, external effect, paid execution, UI, Candidate, protected V2 final
evaluation, irreversible erasure or main merge. All carried identities are local
synthetic claims; neither a committed row nor a digest is consent or custody.

## Verified basis and code changes

- Initial work-basis HEAD: `d17bc741cf24f5f0e58a23a47c744d494b195486`
  (Run759 checkpoint on `research/jarvis-foundations`).
- Baseline [CI #42778723637](https://github.com/Iam-2squared/ark-ai/actions/runs/42778723637)
  on that exact basis: **COMPLETED SUCCESS, 6/6** for Windows/Ubuntu ×
  Python 3.11, 3.12 and 3.13 (job conclusions checked). This does **not**
  prove the new Run760 code.
- Package A, [`69c7639f`](https://github.com/Iam-2squared/ark-ai/commit/69c7639f829f28f780f27a865fab3ecc50b42c24):
  `tests/test_mock_cycle_real_process_exit_run760.py`, **5 parameterized cases**.
  A separate OS interpreter exits via `os._exit(0)` *after* committing a
  durable Planner RUNNING step, registry-bound synthetic occurrence, pre-action
  audit, audit/occurrence link, or terminal SUCCEEDED. A fresh caller reopens
  all **four separate SQLite files**, checks the exact 0/1 committed row counts
  and RUNNING/UNKNOWN or terminal states, and requires both a new token and a
  new occurrence to **fail to replay**. `_NeverExecute.execute` is a
  tripwire; the registered backend cannot run.
- Package B, [`b937cc91`](https://github.com/Iam-2squared/ark-ai/commit/b937cc917c820b458565cfed4cfa75fdba064b73):
  `tests/test_read_journal_os_commit_unknown_run760.py`, **2 cases**.
  A spawned process terminates with an uncommitted WAL receipt (which must
  disappear) or immediately after the detached READ journal COMMIT but before
  delivering the new witness. The caller explicitly reconstructs a retained
  digest-only witness to recover the committed row and verifies the original
  pre-COMMIT witness has become stale. All dispatch/replay/effect flags deny.
- Package C, [`6a7db1c3`](https://github.com/Iam-2squared/ark-ai/commit/6a7db1c399d961423278c0f8070aca32ab109af0):
  `tests/test_occurrence_real_process_lost_response_run760.py`,
  **2 cases**. Another interpreter commits a synthetic occurrence and exits
  before its receipt is delivered. New independent registry/ledger instances
  must reject (i) reuse of the same token with a new occurrence and (ii) reuse
  of the old occurrence with a new token. No raw token ID should be persisted
  in the main SQLite file. This is local replay-fencing, **not** a durable
  signed user approval or exactly-once external tool effect.
- Package D, [`83410c24`](https://github.com/Iam-2squared/ark-ai/commit/83410c241fcafa6987798f859a18cc22bafee412):
  `tests/test_private_veto_os_lost_response_run760.py`,
  **2 cases**. A synthetic scope revocation commits before a child OS exit.
  Cold readers must still deny the revoked scope; repeating its veto must
  fail rather than silently regrant, while unrelated owners/namespaces remain
  separately reviewable. Private owner text must not occur in raw main-file
  bytes. No lawful deletion or context disclosure is claimed.

- Package E, [`153fc80a`](https://github.com/Iam-2squared/ark-ai/commit/153fc80a61563845348656daeaf1f2f49ae34440):
  `tests/test_proactive_real_process_lost_response_run760.py`,
  **2 cases**. A separately spawned worker commits a synthetic proactive
  preparation then exits without returning its receipt. A cold reader sees
  one retained preparation and rejects same-policy attempts at rolled-back
  clock 99 or pre-interval time 104 (last committed time 100, interval 5).
  No notification, authenticated time or dispatch authority is inferred.

**Total: 13 new parameterized tests across five new test-only modules.**
No production source, UI or frozen contracts changed. The tests deliberately
exercise cross-process COMMIT/return boundaries absent from equivalent
same-interpreter exception-based fixtures; they do not simulate a power cut,
malicious filesystem rewrite or independent signed custody.

## Exact new-source CI (no pass carryover)

At the first in-flight sample after authoring:

- [#42785841172](https://github.com/Iam-2squared/ark-ai/actions/runs/42785841172)
  on `69c7639f829f28f780f27a865fab3ecc50b42c24`: IN PROGRESS.
- [#42785991734](https://github.com/Iam-2squared/ark-ai/actions/runs/42785991734)
  on `b937cc917c820b458565cfed4cfa75fdba064b73`: IN PROGRESS.
- [#42786130452](https://github.com/Iam-2squared/ark-ai/actions/runs/42786130452)
  on `6a7db1c399d961423278c0f8070aca32ab109af0`: IN PROGRESS.
- [#42786335715](https://github.com/Iam-2squared/ark-ai/actions/runs/42786335715)
  on `83410c241fcafa6987798f859a18cc22bafee412`: QUEUED.
- [#42786881464](https://github.com/Iam-2squared/ark-ai/actions/runs/42786881464)
  on `153fc80a61563845348656daeaf1f2f49ae34440`: QUEUED at addendum sampling.
- Report and checkpoint commits have distinct HEADs and separately triggered CI,
  so their final six-job conclusions must be checked before a current-head PASS.

No manual rerun or duplicate workflow launch was requested. On a FAIL, inspect
the failing job and make the narrowest allowed fix; do not weaken an existing
safety gate or mark an earlier HEAD green for a later one.

## Explicit isolation and approval blockers

1. **Cross-store atomicity is absent.** SyntheticPlanJournal, occurrence,
   ActionAudit, audit-link and Memory/Personal Context each hold separate
   SQLite transactions. A stage-specific success/failure can leave
   legitimately distinct durable prefixes. None may authorize replay.
2. **Receipt loss is not effect proof.** An external real WRITE might have
   succeeded, failed, or timed out across a crash. These synthetic fixtures
   never call a ToolBackend. Local committed markers cannot establish an
   exactly-once external side effect, authorized actor, authenticated clock,
   protected model identity or signature.
3. **No privacy authority is inferred.** Revocation persists a veto only:
   absence of a veto is not consent, and a hashed scope may still leak linkable
   metadata. No erasure, export, disclosure or user policy change is performed.
4. **Protected scope remains frozen:** main `7a843f17eb96ed13d66f23b58b06406b3002e405`,
   V3 Draft PR #5 `805b377697472268db02650a89c7a94b1c5337c8`,
   paused UI Draft PR #9 `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`.
   V1/V2/Local UI/Launcher evidence and explicit gates remain untouched.

## Next plan / 今後の方針

1. Verify latest **exact-head 6/6 CI**; repair any actual fail by log and
   normal Contents API only, without bypassing write safeguards or rerunning
   equivalent workflows.
2. Continue bounded Memory CAS/WAL and independently retained coherent
   COMMIT-UNKNOWN reviews; never auto-retry a potentially committed WRITE.
3. Progress Planner terminal/READ recovery, immutably bound ToolRegistry,
   exact PermissionGate and audit-before-action **mock-only** integration
   only after each lower invariant has exact-head GREEN evidence.
4. Advance privacy-safe Personal Context, Proactive/Observation back-end
   fixtures and FREE-ONLY V3 approval/identity guard review. Keep PR #5/#9
   Draft/unmerged and new frontend/UI work paused.

**ARK/JARVIS/V3 status: NOT_PASSED.**

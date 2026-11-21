# ARK AI Run685 — non-UI Planner restart, Memory generation, audit chronology, privacy veto

**2026-11-07 JST — FREE-ONLY, DRAFT / UNMERGED, SYNTHETIC AND NO DISPATCH.**

**Work basis:** Run684 checkpoint `9d92b79dfef8b0464a14bf2e6dfb3af4658f58ed`, [CI #42366245874](https://github.com/Iam-2squared/ark-ai/actions/runs/42366245874) independently checked **6/6 GREEN** at the start of this session (Windows/Ubuntu × Python 3.11–3.13). This report is written after four source/test-only commits, on [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8). This run never starts paid or external GPU compute, credentials, services, real actions, or UI work. No protected V2 evaluation, Candidate, main merge, frozen-contract or V3-gate change.

## Package A — Planner durable terminal fanout

- New `tests/test_planner_terminal_dag_restart_run685.py`, commit `9722aec7dcb63a5aa2a978eaaf32a39dfacd8632`, **4 cases**.
- A four-step diamond DAG is replayed from a local SQLite journal after A, B or C terminal FAILURE. Verify exact succeeded/pending/failed/derived BLOCKED revision states after reopening, without creating separate event records for the derived statuses. Verify RUNNING D remains ambiguous after restart and an attempted second RUNNING transition is rejected.
- Mock ToolCall identities only; a matching local journal does not prove execution or grant replay or dispatch.

## Package B — Memory stale generation across an independent SQLite writer

- New `tests/test_memory_independent_writer_generation_staleness_run685.py`, commit `c2093736d26360df30251dc11d62a966f7837e2f`, **4 cases**.
- Observe a generation-fenced CAS token, then let a separate SQLite connection refresh the target, delete/recreate it, expire/recreate it, or expire it without recreation. Attempting the old generation token must fail without adding a single event or changing the postintervention row. Re-created rows must have a new create event ID.
- A local generation digest is neither consent nor writer attribution; no automatic retry after uncertain COMMIT.

## Package C — Audit-before-link identity and chronology

- New `tests/test_synthetic_audit_link_identity_order_run685.py`, commit `bab5dade37a9bd7c4b69af4024df4c27274276b6`, **7 cases**.
- Reject mismatched audit outcome, changed ToolCall request, an audit earlier than the reservation, an audit later than link time, or link timestamp earlier than reservation. Admit only exact mock preaction identities with valid equality or normal timestamp ordering; all result authority properties remain False.
- Each reservation, audit and link SQLite transaction is independent. Their match is not an authenticated cross-store atomic transaction, trusted clock or exactly-once real-world action.

## Package D — Personal Context retention/veto isolation

- New `tests/test_private_retention_scope_expiry_veto_run685.py`, commit `a735a00154cfb0299a6328063905cacc0302586a`, **4 cases**.
- Verify a private-scope veto leaves unrelated owner/namespace inventories unaffected; unrelated Memory writes cannot change the private inventory. After private expiry purge and SQLite re-open, the independently persisted privacy veto remains present; the content-free inventory still cannot claim erasure, context-use permission or authorized deletion.
- The private payload is checked not to appear in diagnostic repr. Purging the synthetic test row does not attest deletion of backups or other copies.

**Total new regression cases: 19 (4 + 4 + 7 + 4).** These are test-only, mock/local changes. They do not modify the production contracts or frozen evidence, and do not claim a new runtime safety guarantee before CI passes. A separate full Windows/Ubuntu × Python 3.11–3.13 CI run automatically starts at each exact commit; CI evidence is meaningful only for its exact SHA.

## CI evidence at report preparation

- Incoming Run684 checkpoint: `9d92b79dfef8b0464a14bf2e6dfb3af4658f58ed`, [#42366245874](https://github.com/Iam-2squared/ark-ai/actions/runs/42366245874) **6/6 GREEN**.
- Planner commit `9722aec7dcb63a5aa2a978eaaf32a39dfacd8632`: [#42369355365](https://github.com/Iam-2squared/ark-ai/actions/runs/42369355365) sampled at **Ubuntu 3/3 GREEN; Windows 3 in progress**, no failures observed.
- Memory commit `c2093736d26360df30251dc11d62a966f7837e2f`: [#42369426531](https://github.com/Iam-2squared/ark-ai/actions/runs/42369426531) sampled at **Ubuntu 3/3 GREEN; Windows 3 in progress**, no failures observed.
- Audit commit `bab5dade37a9bd7c4b69af4024df4c27274276b6`: [#42369499714](https://github.com/Iam-2squared/ark-ai/actions/runs/42369499714) sampled at **Ubuntu 3/3 GREEN; Windows 3 in progress**, no failures observed.
- Privacy commit `a735a00154cfb0299a6328063905cacc0302586a`: [#42369656932](https://github.com/Iam-2squared/ark-ai/actions/runs/42369656932) sampled **in progress**, exact 6/6 GREEN not yet verified.
- This report commit and later canonical checkpoint will each generate their own HEAD and automatic CI. Never transfer ancestor GREEN to a later HEAD. No manual workflow reruns were launched.

## Boundary and next plan

1. Confirm each active CI result and especially the final checkpoint-result HEAD. If an actual semantics-preserving test correction is required, use normal GitHub Contents API only and reconcile the branch HEAD before every write.
2. Continue Memory CAS/ABA/expiry and COMMIT-UNKNOWN on coherent snapshots, Planner per-step recovery/terminal ambiguity, and registry-bound mock WRITE one-shot audit-before-action witnesses without allowing real dispatch.
3. Continue privacy-safe Personal Context, proactive scheduler, startup readiness and observation input contracts under zero-cost offline constraints.
4. Keep [V3 Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) blocked on real model/tokenizer/software identities, rights/provenance, separate human approvals and any spend; keep [UI Draft PR #9](https://github.com/Iam-2squared/ark-ai/pull/9) completely untouched and paused. PR #8 also remains Draft and unmerged.

**ARK / JARVIS / V3: NOT_PASSED.** No generated receipt is consent or external outcome proof.

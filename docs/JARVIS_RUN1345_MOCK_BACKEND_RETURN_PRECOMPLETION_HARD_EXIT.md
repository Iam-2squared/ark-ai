# ARK Run1345 — Mock backend return before completion-audit hard exit

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `9a286176aa5aa9e1c2c0b6f11a3f2b61bdd2142a`.
- New child branch: `research/run1345-mock-backend-return-precompletion-hard-exit-20261125`.
- Source under test: `src/ark/agency/disconnected_mock_executor.py`.
- Adjacent integrated boundaries: Run1288 occurrence-reservation hard exit, Run1296 pre-action-audit hard exit, and Run1337 completion-audit COMMIT hard exit.

## Gap covered

The existing process-exit tests covered:
1. exit after occurrence reservation, before pre-action audit/backend;
2. exit after pre-action audit commit, before backend; and
3. exit after completion-audit commit, after the backend and both audit events.

They did not isolate the intermediate boundary where the exact mock backend has returned successfully but the completion-audit append has not yet executed. This test uses a profile hook only in a spawned Python process: it records the backend method's return, then exits at entry to the second `SQLiteActionAudit.append` call, before that append body can write a completion event.

Cold recovery must retain the durable occurrence and pre-action audit, must not invent a completion event, and must reject reuse of the old one-shot before the new process-local gate or mock backend is called. A separately authorized new one-shot may create a distinct mock occurrence. Production source is unchanged.

## Validation

- PR #8 basis `9a286176aa5aa9e1c2c0b6f11a3f2b61bdd2142a` contains the Run1288, Run1296 and Run1337 adjacent test boundaries.
- Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required for this package. No PASS is claimed.

## Evidence boundary

Synthetic local SQLite and exact in-process MockToolBackend only. This does not establish external effects, trusted time, independent custody, cross-store atomicity, receipt reconstruction, fsync/power-loss durability or exactly-once external effects. No real backend, live data, external service, paid compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, UI work or main merge. PR #8 remains Draft/unmerged; PR #9 remains untouched; ARK/JARVIS remains NOT_PASSED.

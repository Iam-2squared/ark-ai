# Run1146 — Mock executor pre-action audit COMMIT ambiguity

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Parent basis HEAD: `243a65a121690bb0fc1f4a0596b9d1397da79c3c`.
- Child branch: `research/run1146-mock-preaction-commit-unknown`.
- Regression: `tests/test_disconnected_mock_executor_preaction_commit_unknown_run1140.py`.

## Finding

The disconnected mock executor already treats any pre-action audit append exception as a hard stop before the mock backend call. ActionAudit separately tests post-COMMIT acknowledgement loss, and the executor separately tests ordinary pre-action audit failure. The missing composition-level regression was the ambiguous boundary where the pre-action audit transaction may have committed even though the caller receives an exception.

## Change

A subprocess-only synthetic regression injects an acknowledgement-loss wrapper around the exact audit database connection after normal module initialization. Both possible outcomes are exercised:

- COMMIT durable, acknowledgement lost: the pre-action event is present after reopening the audit store.
- COMMIT rolled back, acknowledgement lost: no pre-action event is present after reopening.

In both cases the already-reserved occurrence remains present after reopening, the mock backend is never called, and a fresh process-local PermissionGate cannot replay the same token identity with a different occurrence ID. The wrapper is installed before ARK modules import in the subprocess, so import-original dependency guards remain active rather than being bypassed by runtime monkeypatching.

## Limits

This is synthetic local SQLite evidence only. It does not establish power-loss/fsync durability, cross-store atomicity, trusted time, authenticated consent, independent storage custody, real backend dispatch, or exactly-once external effects. The mock executor and audit/occurrence schemas are unchanged. No frozen contract, V1/V2/Local UI/Launcher evidence, UI/frontend work, PR #5, PR #9, paid service, external compute, credential, hardware action, Candidate generation/promotion, protected evaluation, or main merge is included. ARK/JARVIS remains NOT_PASSED.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS or CI GREEN is claimed.

# Run1392 — Disconnected Mock Executor Validator Vector Custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `9fa835e819cd9e212c2e0a2304d3c37b56293b07`.
- Child branch: `research/run1392-mock-executor-vector-epoch-custody-20261125`.

## Finding

The disconnected mock executor's component verifier used several mutable working/original field, method and hook tuples in strict-zip checks. Those tuples had no independently retained aggregate epoch. Jointly replacing all working/original aliases with matching empty tuples could make descriptor checks vacuous, including the denial-only fields on the mock receipt.

## Correction

An import-time aggregate tuple now retains the full validator inventory. `_require_original_components` captures that tuple in a keyword-only default and verifies the aggregate binding and every component vector by identity before inspecting foundation components or allowing execution to proceed.

## Regression coverage

The synthetic test jointly replaces every working/original vector and the aggregate epoch, then installs a hostile `MockExecutionReceipt.dispatch_authorized` descriptor. The executor must reject before the descriptor, mock backend, or audit store is invoked.

## Scope and evidence limits

This is local in-process identity hardening only. The mock-only execution ordering, registry/PermissionGate/Audit/Occurrence APIs, SQLite schemas, CAS, and authority-denial semantics are unchanged. The executor remains disconnected and never proves an external effect, trusted time, independent custody, human consent, durable authorization or cross-store atomicity.

No real ToolBackend, shell, network, device, model, live data, credential, hardware, paid/external compute, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, main merge or UI/frontend work occurred. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed.

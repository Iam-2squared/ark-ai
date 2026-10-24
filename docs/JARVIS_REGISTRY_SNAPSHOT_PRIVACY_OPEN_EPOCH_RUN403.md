# ARK JARVIS: bounded registry ingress and SQLite-open epoch guards (Run 403)

**Scope:** isolated, reversible, FREE-only synthetic/mock foundations on Draft PR #8.
This engineering note is evidence of intended source/test coverage, **not** a
production security certification, external identity attestation, human approval,
real WRITE authorization, model training result, or gate PASS.

## Threat and invariants matrix

| Boundary | Before: risk | Added fail-closed invariant | Regression fixtures |
| --- | --- | --- | --- |
| ToolRegistry registration generator | `tuple(registrations)` exhausts a hostile/unbounded iterator before registration count can be validated | Reject the **257th** yielded registration; maximum **256**; no backend call | `test_registry_ingress_budget_run403.py` |
| ToolRegistry construction identity | An earlier reflected-frozen `ToolRegistration` or backend `execute` static descriptor can change while a later iterator yield or StopIteration callback is running | Retain original field/backend/static-descriptor witnesses at FIRST observation, recheck after **each** yield, on exhaustion, during sorting/map building, and after revision serialization | Registration field, backend descriptor, StopIteration, and revision-serialization fixture cases |
| Memory snapshot read-only SQLite opening | `Path.resolve()`, `Path.as_uri()` or connection opening can run a substituted callback before the first SQLite read | Pin request and original Path object; reject drift after each boundary and immediately after handle acquisition, before first SELECT | `test_memory_snapshot_open_epoch_run403.py` |
| Synthetic Personal Context veto SQLite opening | Path resolution and URI conversion are callbacks; an opened connection under changed reflected source can precede veto validation | Recheck the original ledger source immediately after resolution, URI creation and SQLite opening; explicitly close any returned connection on drift | `test_privacy_veto_connect_epoch_run403.py` |

The unchanged core boundaries remain: immutable registry identity vectors,
Memory v1 frozen schema, isolated read-only Memory snapshots, append-only
synthetic revocation veto, no offline context disclosure authority, no live
backend dispatch, no human issuer, and UNKNOWN WRITE **never replayed**.

## Test and evidence interpretation

The three packages add **24 regression cases** to existing suites:
registry +10, Memory SQLite opening +7, privacy veto opening +7. These cases
use only disposable local fixtures and callbacks. The exact-number total
requires CI collection and successful execution on the **same HEAD**; this
document does **not** claim GREEN merely because code was saved.

This review tests Python object/path identity across callbacks. It does not
provide OS inode or open-file-descriptor custody, an authenticated trusted clock,
real external execution/consent, atomic cross-SQLite transaction, proof against
a fully hostile in-process interpreter, backend success receipts or exactly-once
external side effects. The Python caller's source-path check is **not** a
filesystem TOCTOU solution. No Memory content or raw Personal Context is
transmitted.

## Integration and authorization constraints

These isolated modules must not be wired to a live executor until an
independently reviewed authenticated issuer, durable one-shot reservation,
trusted execution-clock boundary, pre-action durable audit, backend-specific
reconciliation, and startup blocking gates are all independently GREEN on the
integrated exact HEAD. Synthetic `PermissionGate` decisions and offline
`StartupSnapshot.READY` remain local diagnostics only.

**Explicitly unchanged:** PR #8 stays Draft/unmerged; V3 PR #5 remains
Draft/unmerged/NOT_PASSED; V1/V2/Local UI/Launcher frozen evidence, V3 Contract 1,
protected V2 final evaluation, real Candidate and promotion gates remain closed.
No paid/external GPU, API, service or external PC/device interaction is
authorized or performed.

## Next plan / 今後の方針

Prioritize: (1) validate exact-head six-job CI for source/test packages and
repair genuine regressions via ordinary fresh-HEAD Contents writes; (2) extend
Planner/Occurrence/ActionAudit cross-store restart and UNKNOWN reconciliation
under disconnected mock-only fault injection; (3) review Registry and
PermissionGate identities at token admission versus durable issuer boundaries;
(4) strengthen Memory CAS/coherent snapshots and Personal Context revocation
against concurrent writes while preserving absence-of-consent denial;
(5) add reversible trusted-clock interface fixtures and Scheduler/Observation
reconciliation, with every real-action/evaluation/payment gate still shut.

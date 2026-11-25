# ARK Run1380 — retained guard custody across simultaneous alias replacement

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `11d72bef1b69df06ed0c0102d6154fc4d44a0214`.
- Child branch: `research/run1380-guard-alias-custody-20261125`.
- Production modules:
  - `src/ark/personal_context_revocation_continuity_review.py`
  - `src/ark/observation_fixture_adapters.py`
- Synthetic regressions:
  - `tests/test_context_revocation_continuity_dual_alias_custody_run1380.py`
  - `tests/test_observation_fixture_encoder_dual_alias_custody_run1380.py`

## Findings and corrections

### Personal Context revocation continuity

The previous self-custody check compared the mutable guard function name with a mutable module-level alias. Replacing both names with the same no-op made those two mutable values equal and bypassed the intended identity check.

The public reviewer now retains the original guard and implementation in closure cells while preserving the public function signature. Before private SQLite access and after callback boundaries, the implementation compares both mutable module bindings with the closure-held original and invokes that retained callable. Simultaneous helper-and-alias replacement is rejected before the ledger connection callback.

### Observation fixture text encoder

The previous fixture guard compared a module-level encoder, alias, vector and vector-epoch. Those module attributes could be replaced together with a matching forged vector, so equality between the mutable names was not an independent custody witness.

The public text-fixture adapter now retains the original encoder, vector and implementation in closure cells while preserving its public signature. It checks the module binding, alias, vector and epoch against those captured identities before metadata preflight, after reentrant metadata callbacks, and immediately before/after encoding. It invokes the captured encoder, never a replacement module binding.

## Regression coverage

- Replace the Personal Context continuity guard and its alias simultaneously; require denial before replacement execution or private SQLite access.
- Replace the Observation encoder, alias, vector and vector-epoch simultaneously before ingress and during metadata preflight; require denial before the replacement receives private text or the private hash helper runs.

## Scope and evidence limits

No MemoryScope, revocation schema, witness format, Observation Envelope v1, byte-budget algorithm, retention policy, or public API signature change is intended. These are local in-process integrity checks and synthetic fixtures only. They do not establish authenticated consent, trusted time, independent storage custody, physical erasure, cross-store atomicity, source authenticity, live capture, disclosure authority, dispatch authority, or exactly-once external effects.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No PASS is claimed before that run completes. No live personal data, camera, microphone, screen, device, network, paid/external compute, Candidate, protected V2 evaluation, credentials, hardware action, destructive operation, frozen-contract change, main merge, or UI/frontend work occurred. PR #5 and PR #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.

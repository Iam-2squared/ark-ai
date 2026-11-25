# JARVIS Run1350 — Exact one-shot token field admission

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `f5ca69fa46855a53315b5149d7cfecef4e941a23`.
- Child branch: `research/run1350-permission-gate-exact-token-field-admission-20261125`.
- Source modules:
  - `src/ark/agency/policy.py`
  - `src/ark/agency/durable_occurrence_review.py`
- Regression module: `tests/test_permission_gate_exact_token_fields_run1350.py`.

## Finding

`OneShotAuthorization.__post_init__` validates exact primitive fields at construction, but a frozen slotted dataclass can still be reflectively mutated with `object.__setattr__`. The gate previously captured the resulting field objects and could later reach string hashing/equality or expiry comparisons during grant callbacks and token-spend checks. The durable occurrence fixture likewise read and hashed `token_id` before independently rechecking exact field values.

## Correction

- PermissionGate now snapshots exact built-in `str`/`str`/`int` fields, validates the canonical `act_<64 lowercase hex>` request ID and SQLite-range expiry, and rejects malformed or subclassed values before registry binding/grant iteration/token spend.
- Registered and direct gate paths share an import-original admission helper and pin its identity. Post-callback registered token checks compare original field identity before any value comparison.
- The synthetic durable occurrence store independently pins the OneShotAuthorization class descriptors/hooks and repeats exact field admission before registry binding, digesting or SQLite reservation. Reentrant epoch checks reject changed field objects before invoking subclass methods.
- Existing OneShotAuthorization public contract, token format, registry identity, PermissionGate API, occurrence table schema/DDL, audit schema, retention and external-effect policy are unchanged.

## Regression coverage

The synthetic tests cover reflected token-ID subclasses and blanks, request-ID subclasses and malformed strings, bool/int-subclass/negative/overflow expiries, direct and registered PermissionGate denial before grant iteration, durable-store denial before registry binding, and replaced admission-helper refusal. All backends are inert and must remain uncalled.

## Validation

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS or CI PASS is claimed.

## Evidence boundary

This is local-only exact-value admission hardening. It does not authenticate an issuer, establish trusted time, prove independent custody, make the two SQLite ledgers atomic, authorize real dispatch, or prove exactly-once external effects. No live data, real backend, network/device I/O, paid/external compute, credential/account connection, hardware action, destructive operation, frozen-contract change, protected V2 evaluation, Candidate promotion, main merge, or UI work occurred. PR #5 remains Draft/unmerged; PR #8 remains Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.

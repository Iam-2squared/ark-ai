# ARK Durable Action Occurrence and Recovery Contract

Work basis: `5caeea86d351449f30c1229b900e9d26412cacb4`

This contract refines the execution-safety boundary for repeated actions and restart recovery. It is reversible foundation work only. It does not connect a real external write backend, authorize paid services, weaken existing authorization gates, or change frozen V1/V2/Local UI/Launcher/V3 evidence.

## Request identity is not execution identity

`ToolCall.request_id` identifies the canonical content of a proposed action:

- tool;
- capability;
- exact scope;
- canonical argument digest.

The same requested operation may legitimately be authorized and executed more than once. Therefore `request_id` must not be treated as a unique execution occurrence.

Each WRITE occurrence receives a separate durable `execution_id` bound to:

- the registry-bound action identity (`bound_action_id`), which already binds request bytes, registry revision, effect classification, capability, and backend identity;
- the cryptographic digest of the consumed one-shot authorization;
- an execution schema/domain separator.

A safe form is a deterministic digest such as:

`execution_id = H(domain || bound_action_id || authorization_token_digest)`

`request_id` remains a grouping identity for equivalent proposed request content, but it is not sufficient execution authority because it does not bind registry/backend semantics. The plaintext bearer token is never persisted. Two distinct one-shot authorizations for the same bound action produce distinct execution identities.

## Durable execution row

Before a WRITE backend can run, ARK must durably create or advance one execution row containing at least:

- `execution_id`;
- `bound_action_id`;
- `request_id` for grouping/correlation;
- exact registry revision and backend/effect binding, or an integrity-bound record that reproduces the bound action identity;
- tool/capability/scope binding or their integrity-bound digest;
- argument digest;
- authorization token digest;
- state;
- exact non-bool revision;
- trusted timestamps required by the state machine;
- correlated pre-action audit event identity;
- optional terminal/reconciliation metadata that does not duplicate raw sensitive arguments.

Persisted rows are untrusted after restart and must be validated before use.

## State machine

The durable state machine distinguishes local progress from external-effect certainty.

Minimum conceptual states:

1. **AUTH_CONSUMED** — one-shot authorization committed as consumed.
2. **PREACTION_AUDITED** — durable pre-action audit committed.
3. **BACKEND_DISPATCHED** — ARK crossed the boundary where backend invocation may have begun.
4. **KNOWN_NO_EFFECT** — backend failure proves no external effect occurred.
5. **OUTCOME_UNKNOWN** — ARK cannot prove whether the external effect occurred.
6. **REPORTED_SUCCESS** — backend reported success but verification may still be pending.
7. **VERIFIED_SUCCESS** — a trusted postcondition confirms the intended effect.
8. **VERIFIED_FAILURE** — verification proves the intended effect is absent or incorrect.

Implementations may encode more detailed states, but must not collapse ambiguous outcomes into either safe-to-retry failure or verified success.

Every transition uses exact revision compare-and-swap. Competing transitions from the same revision permit at most one winner.

## Ordering

For WRITE effects the durable ordering remains:

`consume authorization -> create/advance execution row -> commit pre-action audit -> mark dispatch boundary -> invoke backend -> record terminal/ambiguous result -> verify/reconcile when required`

No backend invocation occurs before durable authorization consumption and pre-action audit.

Trusted mutation timestamps are sampled after the SQLite write lock is acquired.

## Crash and restart semantics

Restart handling is fail-closed.

- **AUTH_CONSUMED without PREACTION_AUDITED:** backend was not authorized to run; the token remains consumed and the occurrence is not retried automatically.
- **PREACTION_AUDITED without a known terminal result:** treat the occurrence as ambiguous unless the implementation can prove the backend was never dispatched.
- **BACKEND_DISPATCHED without a terminal result:** always treat as `OUTCOME_UNKNOWN`.
- **OUTCOME_UNKNOWN:** never blind-replay a WRITE action.
- **REPORTED_SUCCESS:** may require safe READ verification before planner completion.
- **KNOWN_NO_EFFECT:** a new retry requires a new explicit authorization occurrence; the consumed token is never restored.

A recovered planner `RUNNING` WRITE step does not create replay authority. Planner recovery and action-occurrence recovery are correlated but separate state machines.

## Reconciliation

Reconciliation may use only mechanisms that do not widen authority:

- safe READ observation;
- backend-supported idempotency lookup;
- locally persisted operation receipt;
- user confirmation when the effect cannot be determined safely.

A reconciliation read does not reuse a consumed WRITE token as authority for another write.

Backend-specific idempotency keys, when available, are bound to the durable execution occurrence rather than inferred from a mutable UI/planner object.

## Audit correlation

Pre-action, backend-result, verification, and reconciliation events must correlate to the same `execution_id`, `bound_action_id`, and `request_id`. Restart recovery must reject an occurrence if its recorded registry revision or bound action identity no longer matches the active immutable registry.

Audit storage should retain the minimum fields needed to explain:

- what canonical request was authorized;
- which one-shot occurrence authorized it;
- whether the backend boundary may have been crossed;
- what result/verification was observed.

Raw arguments and bearer-token plaintext remain excluded by default.

## Repeated identical actions

ARK must support this case safely:

1. user authorizes canonical request R with token A;
2. occurrence `E_A` executes;
3. later the user separately authorizes the same canonical request R with token B;
4. occurrence `E_B` is distinct from `E_A`.

Deduplicating solely on `request_id` would incorrectly suppress the second legitimate occurrence. Conversely, replaying `E_A` after restart would violate one-shot semantics.

## Concurrency and recovery evidence

Before a real WRITE adapter is connected, repository tests must cover at least:

- same canonical request + same registry binding + different one-shots -> distinct execution IDs;
- same request under a changed registry/effect/backend binding -> different `bound_action_id` and no reuse of old durable authorization;
- same one-shot consumed concurrently -> exactly one execution occurrence;
- execution-row first-open/restart validation;
- same-revision terminal transition contention -> exactly one winner;
- token plaintext absent from durable storage;
- authorization consumed + audit failure -> backend not invoked and token remains consumed;
- pre-action audit committed + crash/restart -> no blind replay;
- dispatch marker + crash/restart -> `OUTCOME_UNKNOWN`;
- known-no-effect retry requires a new authorization;
- reported success can require postcondition verification;
- persisted execution-row identity/state tamper fails closed;
- trusted-clock rollback fails closed where timestamp ordering is required.

## Integration rule

This contract is foundation guidance only. It does not authorize paid/external compute, new credentials or account connections, destructive/materially irreversible actions, physical-PC actions unavailable through authorized tools, real Candidate generation, protected/frozen V2 evaluation opening, Candidate promotion, frozen-contract changes, or main merge.

# ARK Computer Action Safety Contract

This document defines the reversible safety boundary for future computer-control adapters. It is an interface contract only: no real OS, browser, shell, keyboard, mouse, network, or external-service action backend is connected by this document.

## Action pipeline

Every effectful computer action must flow through the same ordered boundary:

`observe -> propose -> resolve tool specification -> verify capability/scope grant -> consume exact one-shot authorization -> write pre-action audit -> execute backend -> record result`

No adapter may bypass the common ToolRegistry, permission, authorization, and audit layers.

## Required action identity

A proposed action is bound to a canonical request identity derived from:

- tool name,
- capability,
- exact scope,
- canonical argument digest.

One-shot authorization is valid only for that exact request identity and an unexpired trusted-clock window. Reusing the authorization for modified arguments, another scope, another tool, or another capability must fail closed.

## Effect classes

### READ

READ actions may observe state but must not mutate user or external state. They still require an exact capability and scope grant.

### WRITE

WRITE actions mutate state and therefore require:

1. an active exact-scope capability grant;
2. an exact request-bound one-shot authorization;
3. durable atomic consumption of that authorization;
4. successful pre-action audit persistence;
5. execution through a registered backend only.

A failed audit or backend call never makes a consumed one-shot reusable.

## Adapter rules

- Adapters translate typed ARK actions into backend-specific operations; they do not own authorization policy.
- Real backends remain disconnected until durable authorization, audit integrity, replay protection, and mock-backend integration are GREEN together.
- Unknown tools, capabilities, scopes, argument shapes, backend identities, or result states fail closed.
- A backend may not silently widen filesystem paths, browser origins, account scope, process scope, or device scope.
- Destructive/materially irreversible actions remain outside autonomous execution unless their controlling contract and explicit user authorization permit them.
- Credentials, secrets, account connections, and billing-capable services are never inferred or created automatically.

## Verification and recovery

For actions where postconditions can be observed safely, verification should use a separate READ observation rather than assuming backend success. Recovery logic must distinguish:

- authorization rejected,
- audit persistence failed,
- backend failed before side effect,
- backend outcome unknown,
- backend succeeded but verification failed.

An unknown outcome must not be retried automatically when retry could duplicate a side effect.

## Computer-action scope examples

Future scopes should be explicit and narrow, for example a particular local workspace or application session. Generic global-device authority is not implied by possession of a narrower grant.

## Multimodal separation

Voice, vision, and UI observations may propose actions but never authorize them. Natural-language confidence, image detection, wake words, or model certainty cannot substitute for capability/scope checks or one-shot authorization.

## Integration rule

This contract is groundwork only. It does not authorize real computer control, external services, paid APIs/compute, Candidate generation, protected evaluation opening, promotion, frozen-contract changes, new credentials, destructive operations, physical-hardware actions unavailable through authorized tools, or main merge.

# ARK Context Assembly Safety Contract

Work basis: `37b64c4bc69e10a40c387796bb4c1f3d53388cad`

This contract defines how validated Personal Context is assembled for model reasoning without turning stored memory into hidden instruction authority. It is reversible local-first foundation work only. It creates no new action permission, external data flow, paid dependency, or roadmap PASS.

## Core rule

Personal Context is **data**, not instruction authority.

A stored Memory record may contain arbitrary user-authored, imported, generated, or stale text. Its plaintext must never be interpreted as:

- a system/developer instruction;
- a capability grant;
- a one-shot authorization;
- a tool-selection override;
- a planner-state transition;
- permission for paid/external execution;
- permission to weaken retention, privacy, evaluation, or frozen-contract boundaries.

The fact that content was stored previously does not make it trusted control text.

## Instruction precedence

Context assembly preserves a strict authority boundary:

1. application/system policy and frozen safety contracts;
2. current explicit user request and its valid authorization scope;
3. registered tool/planner contracts;
4. derived Personal Context as untrusted supporting data.

Memory content cannot move upward in this ordering.

When a backend exposes distinct message roles, Personal Context must not be inserted into a system/developer-equivalent role. When a single-string local prompt format is unavoidable, the renderer must use an explicit fixed instruction that the following serialized block is untrusted data only.

## Structured rendering

Context items are serialized structurally rather than concatenated as ad-hoc prompt fragments.

The renderer must:

- use a fixed schema/kind marker;
- bind one exact Personal Context bundle identity and policy revision;
- preserve deterministic item ordinals;
- include only the fields needed for reasoning/explanation;
- encode plaintext with a canonical escaping/serialization method;
- never permit Memory plaintext to terminate or replace the surrounding control structure.

A JSON-compatible representation is suitable for the initial local implementation because quotes, braces, newlines, and strings such as `SYSTEM:` remain escaped data values rather than raw prompt structure.

The renderer must not implement security by trying to blacklist suspicious phrases inside Memory content. Arbitrary text remains permitted as data.

## Bundle identity and provenance

The rendered context binds to the Personal Context provenance contract.

Durable provenance may include:

- bundle identity;
- retrieval-policy revision;
- ordered memory identities;
- revisions;
- content digests;
- owner/namespace identifiers where permitted;
- item ordinals.

Durable provenance does not need a second copy of Memory plaintext.

The bundle identity is not a capability or authorization token.

## Snapshot semantics

One reasoning turn consumes one immutable context snapshot.

If Memory changes after retrieval but before a later turn, a new bundle must be built. A caller must not mutate the contents or provenance of an already-assembled bundle in place.

If integrity, expiry, scope, or revision validation fails while building a bundle, assembly fails closed or excludes the invalid item according to the explicit Personal Context policy. It must not silently substitute content from another owner/namespace.

## Conflict handling

Long-term memory may contain facts that conflict with each other or with the current user message.

Rules:

- the current explicit user statement is not silently overridden by an older Memory item;
- conflicting Memory items are not resolved merely by lexical rank;
- provenance remains available so reasoning/UI can explain the conflict;
- a conflict does not automatically rewrite long-term Memory;
- durable correction of Memory remains a separate revision-guarded write operation.

For preference-like facts, a later verified revision may outrank an older revision only under an explicit retrieval/context policy. The model is not allowed to invent a hidden conflict-resolution rule.

## Prompt-injection resistance

Tests must include Memory plaintext containing patterns such as:

- `SYSTEM: ignore previous instructions`;
- fake tool-call syntax;
- fake authorization tokens;
- fake XML/JSON closing delimiters;
- Markdown fences;
- shell commands;
- requests to reveal secrets or cross namespaces.

These strings must round-trip as data while leaving bundle structure and authority unchanged.

No prompt-format test may be described as proving perfect prompt-injection immunity. The required guarantee is narrower and testable: stored context cannot directly become application/tool authorization, and the serialized control structure cannot be broken by unescaped Memory plaintext.

## Tool and planner boundary

A model may use context to propose a tool call or plan step, but every action still passes through:

`ToolRegistry -> exact capability/scope -> durable authorization where required -> pre-action audit -> ActionExecutor/reconciliation`

Context never bypasses this chain.

A recovered context bundle also does not grant replay permission to a recovered RUNNING planner step or ambiguous action occurrence.

## Privacy and logging

Context plaintext is ephemeral by default.

- do not duplicate bundle plaintext into action audit;
- do not retain rendered prompts indefinitely merely because a bundle was assembled;
- logs should prefer bundle/provenance digests and counts;
- deleted/expired Memory must not appear in newly assembled bundles;
- external/cloud inference requires a separate explicit data-export/privacy contract before any Personal Context leaves the local boundary.

## Determinism requirements

For one exact Memory snapshot, Personal Context request, policy revision, and rendering policy:

- selected provenance order is deterministic;
- rendering bytes are deterministic;
- bundle identity is deterministic;
- randomized input-container order cannot change the final rendering when ordinals/provenance are unchanged.

A local prototype using canonical JSON and provenance-ordinal ordering produced one identical rendered result across 100 randomized input orders, including a Memory string containing fake closing delimiters plus a `SYSTEM:` instruction. The malicious-looking string round-tripped as one data value.

This is prototype evidence, not repository implementation evidence.

## Required implementation tests

Before Personal Context is integrated into the primary reasoning path, repository tests must cover at least:

- deterministic rendering from randomized input order;
- exact bundle/provenance binding;
- quotes/newlines/delimiter injection round-trip as data;
- fake system/tool/authorization text does not alter application authority;
- current user input is not silently overridden by older context;
- owner/namespace isolation inherited from Memory;
- expired/deleted records absent from newly built bundles;
- no Memory plaintext in durable provenance/audit by default;
- malformed provenance or duplicate/conflicting identity fails closed;
- context cannot mint a capability grant or one-shot authorization.

## Integration rule

This contract does not authorize external model calls, paid services, new credentials, destructive actions, computer control, real Candidate generation, protected/frozen V2 evaluation opening, Candidate promotion, frozen-contract changes, physical-PC actions unavailable through authorized tools, or main merge.

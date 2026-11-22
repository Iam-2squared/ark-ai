# Run1117 — ToolRegistry slot-only bridge compatibility

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD at branch creation: `c524935080889792b07f35c2eaefd5316c8dadb2`.
- Child branch: `research/run1117-tool-registry-slot-bridge-compat`.
- Prior isolated attempt: Draft PR #278, head `a93e2922b6280f4bad5aaf2b72ca19e7b87fcc31`, exact CI run [45027296742](https://github.com/Iam-2squared/ark-ai/actions/runs/45027296742).

## Failure evidence

PR #278's exact-head CI reported 203 failures, 19,093 passes and 1 skip on the inspected matrix job. The repeated TypeError was `vars(registry)` against a no-`__dict__` slot-only ToolRegistry. The atomic registered-intent bridge and the older disconnected executor namespace check still assumed an ordinary instance dictionary. Separate tests also tried to monkeypatch methods directly on a sealed instance, which now correctly raises `AttributeError`.

## Repair

- Port the no-dict `__slots__` / sealed-assignment implementation and original instance-seal guard from PR #278 onto the current PR #8 head.
- Replace the atomic bridge's `vars(registry)` instance-shadow checks with exact-class, class-descriptor identity checks and the registry's original instance-epoch validator before and after callback boundaries.
- The current PR #8 disconnected executor already uses its `_instance_namespace` compatibility helper, which returns an empty namespace for slot-only exact objects; keep that behavior unchanged.
- Update tests to distinguish impossible instance-level method shadowing (assignment itself must fail) from class-level descriptor substitution (PermissionGate/bridge must reject before grant iteration, digest or backend callback).
- Preserve the original registration digest, ToolCall identity, BoundAction identity, exact registration lookup and non-dispatch semantics.

## Boundaries

ToolRegistry remains a local immutable registration map, not an authorization grant or remote backend attestation. No tool executes, no grant is created or consumed, and no action is dispatched. PermissionGate continues to require exact class-level implementation identity and exact-scope authorization. PR #8 remains Draft/unmerged; PR #5 remains gated Draft/unmerged; PR #9 remains untouched and UI stays paused. No paid service, external GPU, Candidate generation/promotion, protected V2 evaluation, credentials, hardware action or main merge. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed. ARK/JARVIS remains NOT_PASSED.

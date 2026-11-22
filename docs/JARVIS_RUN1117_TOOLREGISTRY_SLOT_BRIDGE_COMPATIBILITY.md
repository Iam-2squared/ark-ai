# Run1124 — ToolRegistry slot-only immutability and atomic bridge rebase

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `3940af27c8dc55ccfccadad8cb5c6b63f1e96577`.
- Child branch: `research/run1124-toolregistry-slot-only-rebase`.
- Rebased source: Draft PR #297, `research/run1117-tool-registry-slot-bridge-compat`, exact source HEAD `efc7edd7061ad7ab9a5cf380645fa90322be38f0`.
- Prior exact-head CI run [45053320999](https://github.com/Iam-2squared/ark-ai/actions/runs/45053320999): all 6 Windows/Linux × Python 3.11–3.13 matrix jobs failed. The inspected Python 3.11 jobs reported 81 failed, 19,119 passed and 151 skipped.

## Findings and repair

- Port the no-`__dict__` `__slots__` / sealed-assignment ToolRegistry implementation and original instance-seal guard.
- Replace the atomic registered-intent bridge's `vars(registry)` assumptions with exact-class method-descriptor checks and the original registry instance-epoch validator before and after callback boundaries.
- Preserve the existing disconnected executor namespace helper, which already handles slot-only exact instances without a mutable namespace.
- Migrate the 20 affected legacy ToolRegistry/PermissionGate/Planner/occurrence tests away from impossible per-instance method shadowing. Direct registry reentrancy tests now inject through class descriptors; authorization/bridge paths assert class-level substitution is refused before callbacks, grant iteration, digest reads or backend execution.
- Pin the sealed `__delattr__` descriptor as well as `__slots__` and `__setattr__`, so ordinary deletion cannot mutate a constructed registry and a substituted deletion guard is rejected before reads.
- Keep exact ToolCall carrier identity, registration digest, BoundAction identity, one-shot token semantics, occurrence replay protection and non-dispatch behavior unchanged.

## Evidence limits

The earlier PR #278 attempt reported 203 failures from `vars(registry)` consumers and direct instance monkeypatches. PR #297 repaired the bridge but its exact-head run still failed on legacy instance-shadow tests; this rebase updates those tests. No test or local identity guard is a Python security sandbox or remote backend attestation.

All backends remain synthetic and nonexecuting. No grant is created or consumed by the registry itself; no tool dispatch, real WRITE, trusted human consent, external action, paid service, GPU compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, UI work, frozen-contract change or main merge is enabled. PR #8 remains Draft/unmerged, PR #5 remains gated Draft/unmerged, and PR #9 remains untouched with UI/frontend development paused. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed. ARK/JARVIS remains NOT_PASSED.

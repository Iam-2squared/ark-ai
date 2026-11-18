# ARK AI Run967 — opt-in local source custody and synthetic observation identity hardening

Work basis: Run966 checkpoint `0f0f49f95d0ce303bceaa3d1a9e2f738385348ed`. Branch `research/jarvis-foundations`, Draft PR #8; no main changes, approvals or integration claims.

## Package 1 — disconnected local source pins

- Source `dc387e5f5b589e22219a6e54294c7d2746981df6`: pin original dataclass field/denial/hook vectors, descriptors, metadata codec and path budget before retained-pin-field access or filesystem scan. Recheck after local scans and before returning.
- Regression `12ff8984ec2aea8863b15de15b2462b1613ec62d`: 25 authored cases. Substituted vectors/reflection, class getters/constructors, reentrant stat modification, normal read-only operation. No real user file bytes read or modified.

## Package 2 — POSIX descriptor-anchored seal

- Source `9532dfda42c92f23ab27bd1f7afdbfa82b2631ce`: original class/slot/denial/hook and digest-budget identity checks before opening file descriptors, during capture, before retained-metadata reflection and after final pathname recheck.
- Regression `edea9dc65c542c394041333c540445e2e15a1637`: 28 authored cases for altered vectors, fields, methods/equality, reentrant named-path stat swap and normal non-authorizing operation. POSIX-only suite skips on unsupported Windows.

## Package 3 — synthetic Observation fixture labels

- Source `db6021b5fd430d3f2f808e1d330e3d04aa640d6a`: reject 18 additional invisible Unicode codepoints for opt-in fixture source/privacy labels before hashing private *synthetic* bytes. Frozen public `ObservationEnvelope v1` API, schema and direct constructor remain unchanged.
- Regression `900500ce969703c1e9f2b3cf2a862179fa128ac5`: 40 authored cases: 18 codepoints × 2 labels, three permitted human-readable Unicode labels, explicit frozen v1 compatibility.

**Total: 3 coherent non-UI source/test packages, 93 authored test cases, not 93 proven passes.** Prior exact Run966 checkpoint CI [#44290072462](https://github.com/Iam-2squared/ark-ai/actions/runs/44290072462) completed SUCCESS 6/6; it does not certify Run967. Latest Run967 test-head CI [#44298747365](https://github.com/Iam-2squared/ark-ai/actions/runs/44298747365) was QUEUED when checked. Intermediate CIs in progress/queued. No local full pytest/Ruff or physical-PC verification; no manual duplicate workflow dispatch.

## Safety scope / non-claims

All changes isolated, reversible and opt-in. Local inode/hash snapshots are not independent provenance, physical storage consistency, authenticated custody, durable consent, trusted clock or exactly-once proof. Fixture identities grant neither camera/microphone access nor tool execution. POSIX handles guard only an inspection interval, not persistent filesystem immutability.

Frozen V1/V2, Memory v1, Observation Envelope v1, Local UI/Launcher and V3 Contract 1 retained. PR #5 protected Draft/unmerged; PR #9 paused UI Draft/unmerged/untouched; PR #8 still Draft/unmerged. No paid/external compute/API, Candidate generation/promotion, protected final evaluation, credentials, live external effects, irreversible actions, or main merge.

## Next plan / 今後の方針

1. Obtain exact latest Run967 checkpoint-head CI on Windows/Ubuntu x Python 3.11–3.13. For FAIL, inspect exact logs and use normal Contents API for minimal semantics-preserving fixes; do not infer GREEN from previous heads.
2. Continue Memory generation CAS/ABA, event/WAL/SHM/expiry coherence, ambiguous-COMMIT review with frozen v1 unchanged.
3. Advance Planner terminal/cold recovery, registry-bound exact-type PermissionGate, durable once-only reservation, trusted-clock audit-before-action and mock-only integration after exact-head GREEN evidence.
4. Continue privacy-safe Personal Context revocation, proactive occurrence/replay, Observation/startup fixture contracts and free-only V3 guards. Keep UI paused and payment/credential/hardware/irreversibility gates intact.

**ARK/JARVIS overall: NOT_PASSED.**

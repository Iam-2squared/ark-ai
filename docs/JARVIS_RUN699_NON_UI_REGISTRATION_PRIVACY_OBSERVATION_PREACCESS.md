# ARK AI — Run699 / non-UI registration, erasure, observation custody

Work-basis branch `research/jarvis-foundations`, Draft [PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), initially inspected at `0878cc696a22e21f575c4dd0768318bb04e2736a`; last pre-report basis `6279de8f8528c42836222bb535222a157aed32d9`. Recorded administrative UTC `2026-11-08T01:08:30.833Z` (not a trusted clock or execution identity). This is independent of pending parallel Run698 contributions already on the branch; nothing in this report attests their uncompleted CI.

## Work package A — immutable ToolRegistration class-descriptor custody

- Production `src/ark/agency/registry.py` at commit `49c8d8203671e1ff037d7887b5180e2001d90ff2`: pin original registration class, all five slots, constructors, and lookup hooks at module import. Reject class-level substitution before reading registration fields at direct construction validation, registry construction/iterator boundaries, revision checks, resolve, or bind.
- New `tests/test_registry_registration_descriptor_preaccess_run699.py`, initial commit `d087f03ff2a8973cb3850446fc435b17bd0c6883`, narrow dataclass-constructor expectation correction `796856cbc479c1873bbab9f807b64bc0d4e7fbeb`: 45 operation/descriptor combinations, five construction-slot cases, a generator interleaving case, an exported-class replacement case and a normal deterministic inert-binding case (**53 parameterized cases**).
- The constructor may fail in CPython's frozen dataclass `object.__setattr__` before reaching `__post_init__` when a slot is replaced by a setter-less property. Tests accept that early `AttributeError` or a domain `ValueError`, but require **zero hostile getter calls** in either case. Backend execution remains forbidden. The pin is only a local anti-reflection check, **not** a cryptographic/backend identity attestation, durable authorization, or protection against total interpreter compromise.

## Work package B — deny-only privacy-erasure evidence carrier custody

- Production `src/ark/privacy_erasure_evidence_review.py`, commit `488fcab01dbec41adce11e6e24e090cdd55f67d9`: retain import-original input observation/result dataclass slots and hooks, not merely the existing four always-False authority properties. Reject substitutions **before** the first observation getter and after caller-reentrant digest callbacks, and before result instantiation/use.
- New `tests/test_privacy_erasure_carrier_preaccess_run699.py`, initial commit `60b61c6eb6b759e460d305c4445222f7ad957592`, stronger retained callback-time mutation in `6279de8f8528c42836222bb535222a157aed32d9`: 16 preinstalled input/result descriptor cases, four hash-time persistent substitution cases, one unchanged deny-only case (**21 cases**).
- No file deletion, WAL checkpoint, forensic attestation, cleanup authorization, user approval, or privacy use grant is attempted. Even the most optimistic observations still return `independent_storage_attestation_missing` and `forensic_scope_not_attested`.

## Work package C — actual CI failure diagnosis and minimal Observation test compatibility

- Incoming head `0878cc696a22e21f575c4dd0768318bb04e2736a` CI [#42431826660](https://github.com/Iam-2squared/ark-ai/actions/runs/42431826660) reported Ubuntu failure. The inspected Ubuntu Python 3.11 job `128582211121` had **6 FAIL, 10,719 PASS, 1 SKIP**, all mismatched legacy diagnostic expectations after earlier import-pinned observation JSON/hash rejection. A second inspected Ubuntu 3.11 job `128583842353` from [#42432366843](https://github.com/Iam-2squared/ark-ai/actions/runs/42432366843) had the same six FAIL; no new local runtime authority issue was demonstrated by these logs.
- `tests/test_observation_rollover_original_epoch_run409.py`, commit `344c0ec467efcd6304f1e922fb51ac588d5d719d`: two tests now require **early digest implementation rejection**, no tampering/restoration callback, and unchanged retained generation.
- `tests/test_observation_window_witness_digest_epoch_run405.py`, commit `72d4d0aae8c64dc9b72386f27af04b7e6747f19b`: four parameterized assertions now require the earlier digest-implementation refusal, no injected serializer/hash execution, and retained source identity.
- These two compatibility changes restore tests to the stronger existing fail-closed boundary; production Observation code was not altered in this invocation.

## Verification, review limits and next plan

- This run used only ordinary GitHub Contents API source/test writes. The branch was re-read before each write, each write used the exact current file blob SHA; no force push, raw-object bypass, main merge, or UI work.
- Distinct CI runs were automatically triggered for each commit; latest exact-head **6/6 GREEN is not yet established**. In-flight/pending CI is not proof of PASS. Confirm it separately; diagnose any failing job before touching dependent code. A small static inspection confirmed no newly authored lines over 100 characters, but this is **not pytest/Ruff CI evidence**.
- Remain FREE-ONLY and disconnected. Keep PR #5/#8/#9 Draft/unmerged, frozen V1/V2/Local UI/Launcher intact, V2 protected evaluation closed, V3 unpromoted. No paid GPU/API, Candidate, real WRITE/notification, credential connection, automatic COMMIT-UNKNOWN replay, or irreversible cleanup.
- Next: (1) obtain exact-head Ubuntu/Windows Python 3.11–3.13 CI and minimal semantics-preserving repairs if needed; (2) Memory coherent CAS/COMMIT-UNKNOWN/retained veto; (3) Planner durable READ/UNKNOWN and registry-bound audit-before-action disconnected integration; (4) privacy erasure/revocation continuity and free V3 evidence/path guards.

**Overall ARK/JARVIS/V3 status: NOT_PASSED.**

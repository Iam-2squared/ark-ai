# Run1015 — Observation fixture metadata before private hashing

**Work basis:** Draft PR #50 exact head `56e3163ce0404eeabbc8bcf68771cc1fffedfccc`, whose exact-head CI run #44662927894 completed GREEN. This is an isolated test-only child of PR #50.

## Regression coverage

The new parameterized tests exercise both text and binary fixture adapters and require malformed metadata to fail before the private SHA-256 callback can receive content:

- exact-type and subclass rejection for source identifiers;
- blank and over-budget source identifiers;
- NUL and ASCII control delimiters;
- Unicode bidi/formatting controls;
- invalid UTF-8 surrogate input;
- boolean timestamps (which must not pass as integers); and
- uppercase parent digests.

Separate sentinels verify that a rebound global `hashlib.sha256` or local private-hash helper is rejected before either callback receives fixture bytes.

All values are synthetic and all content remains in-memory. The tests do not open files, cameras, microphones, screens, networks, notifications or ToolBackends.

## Interpretation and limits

This validates local fixture-adapter prehash admission only. It does not authenticate observation sources, prove capture provenance, consent, trusted time, physical erasure, independent custody, or permission to dispatch a tool. The frozen Observation Envelope v1 contract and production adapter source are unchanged.

No live capture, personal data, paid service, external compute, credentials, Candidate artifact, protected V2 evaluation, UI/frontend work, PR #5, PR #9, or main branch is touched. PR #50 and PR #8 remain Draft/unmerged.

**Validation:** test and report saved. Exact-head CI is pending after the Draft child PR is opened. No PASS is claimed. Overall ARK/JARVIS remains NOT_PASSED.

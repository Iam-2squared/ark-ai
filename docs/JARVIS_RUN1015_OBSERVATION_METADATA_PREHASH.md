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


## Run1030 rebase onto the current foundation head

- New exact work basis: Draft PR #8 branch `research/jarvis-foundations`, HEAD `b585c61a6e3ca1a9f456175b2a96053a908a500c`.
- This re-applies the isolated Observation fixture tests and evidence notes onto the current PR #8 foundation head; no Observation Envelope v1 contract or production adapter source changes.
- Previous PR #50 head `0e457eabd526d055757de7b77bd10bacacd3ce11` passed exact-head CI run #44796589485 (6/6); that result is not transferred to this new head.
- Fresh exact-head six-job CI is required. No local pytest/Ruff PASS is claimed.

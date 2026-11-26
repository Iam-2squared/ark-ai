# Run1010 — Observation fixture payload byte-budget boundary

**Work basis:** Draft PR #8 exact head `ce4b567605896fe1bda4fa8458fe448701b9dced`. This is a test-only child; the frozen Observation Envelope v1 contract and fixture adapter source are unchanged.

## Regression

The opt-in in-memory fixture adapters have a 4 MiB private-payload budget. This regression verifies:

- text, transcript, image and screen payloads one byte (or one four-byte UTF-8 scalar) over the limit are rejected before the private hash helper is invoked;
- a multibyte text payload whose character count is below the limit but UTF-8 byte count exceeds it is still rejected; and
- exact 4 MiB text and binary fixtures remain accepted as digest-only envelopes without retaining raw payload fields.

All payloads are synthetic in-memory values. No camera, microphone, screen, filesystem, network, notification or ToolBackend is accessed.

## Limits and safety

This checks only local fixture ingress bounds and hash ordering. It does not authenticate a source, establish consent, enable live capture, prove provenance, or authorize dispatch. The public Observation Envelope v1 contract is unchanged. No paid service, external compute, Candidate, protected V2 evaluation, UI work or main merge is involved.

**Validation:** authored regression and report; exact-head CI is pending. No PASS is claimed. PR #8 remains Draft/unmerged. Overall ARK/JARVIS remains NOT_PASSED.


## Run1030 rebase onto the current foundation head

- New exact work basis: Draft PR #8 branch `research/jarvis-foundations`, HEAD `b585c61a6e3ca1a9f456175b2a96053a908a500c`.
- This re-applies the isolated Observation fixture tests and evidence notes onto the current PR #8 foundation head; no Observation Envelope v1 contract or production adapter source changes.
- Previous PR #50 head `0e457eabd526d055757de7b77bd10bacacd3ce11` passed exact-head CI run #44796589485 (6/6); that result is not transferred to this new head.
- Fresh exact-head six-job CI is required. No local pytest/Ruff PASS is claimed.

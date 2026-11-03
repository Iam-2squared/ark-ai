# Passive V3 packet delta: printable Unicode spaces (Run548)

This source-only hardening does **not** approve learning, model weights, paid compute, Candidate generation, protected V2 evaluation, main merge, or any real external action.

## Source and regression fixtures

- Draft PR [#5](https://github.com/Iam-2squared/ark-ai/pull/5), branch `research/v3-learning-evaluation`.
- `src/ark/learning/authorization_packet_delta_review.py`: source update at `86a25758965e7eb20808703763c7dd9a1f50eac6`; unused-import cleanup at `626ed60ba389298bec3ad95168a2674df6c1e607`.
- `tests/v3/test_packet_delta_unicode_spaces_run548.py`: authored at `0e0b1ad4e8563b974f60504cf258897ab734604a`.

## Change and reasoning

Before this change, packet-delta path components escaped Unicode controls (`Cc`), format controls (`Cf`), surrogates and line/paragraph separators, but did not escape non-printing Unicode space separators (`Zs`). For example, U+00A0 NO-BREAK SPACE could remain visually ambiguous in a reported key path. `str.isprintable()` now covers all non-printing Unicode characters; an ordinary U+0020 ASCII space remains readable. Escaped code points use the existing `~u{HEX}` syntax. A literal tilde in a JSON key is independently encoded as `~0`, so `a~u{A0}b`, `a b`, and `a\u00a0b` cannot alias one another in the change-set path map.

Authoring included eight `Zs` code-point cases plus ASCII-space preservation, literal-escape collision avoidance and nested path collision avoidance (11 new pytest parameter-expanded cases). This is an output-path ambiguity fix, **not** an authorization decision, canonical content migration, or cryptographic provenance upgrade. Printable Unicode confusables and broader human display ambiguities still need separate review.

## Evidence and authorization

Frozen contracts, protected evaluation and training boundaries remain untouched. Authored tests and GitHub commit SHAs are recorded above; no independent local pytest PASS or six-job exact-HEAD GREEN is claimed here. Inspect actual Actions run jobs before stating their outcome.

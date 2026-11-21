# Run547 — passive V3 review packet path collision and display hardening

Scope: **unapproved, read-only, zero-new-cost diagnostic** in Draft PR #5.
This note is neither human-review evidence nor authority to perform a model
download, paid compute, preflight, full training, Candidate export/promotion,
protected V2 evaluation, or main merge. Frozen `docs/v3/CONTRACT.md` remains
unchanged.

## Confirmed source changes

1. `src/ark/learning/authorization_packet_delta_review.py` source commit
   `0694bb1a13036c352169b763cd3d0ff72656cf5e`: reserve `~5`
   as an empty JSON mapping-key path component. Without this, the trees
   `{"": {"a": 1}}` and `{"a": 1}` both emitted `a`, allowing
   a semantic change to disappear from a value-free field-path delta.
   Literal `~5` is always escaped to `~05`.
2. Source commit `5b81bcbdbb712cd40d0b745c52e46f784763bd8c`:
   additionally encode backslashes as `~6` and Unicode categories
   Cc/Cf/Cs/Zl/Zp as printable `~u{HEX}`. This prevents control-line,
   bidi-format, surrogate and line-separator codepoints from being
   reproduced as raw field-path text. The reserved tilde escape makes
   these representations disjoint from literal keys.
3. Existing ordinary dotted, bracketed and index paths remain compatible:
   a nested `a.b` still differs from literal key `a.b`, and
   `arr[0].nested` remains the normal path.

## Regression evidence

- `tests/v3/test_packet_delta_empty_keys_run547.py` added at
  `d7b30655f100ff438fbcbe9592f274020c4d4572`.
  Synthetic fixtures include the empty-key alias, mixed normal/empty
  keys, repeated empty nesting, the literal escape marker, arrays,
  empty containers, and depth-budget rejection.
- `tests/v3/test_packet_delta_printable_paths_run547.py` added at
  `30befe85d42bcfeed782dfd87e9b35fa8c5ae40b`.
  Fixtures include newline/NUL, backslash, bidi override, ZWJ,
  Unicode separators, lone surrogate, reserved-marker collision,
  and unchanged ordinary array/dot paths.
- Exact source/test HEAD `30befe85d42bcfeed782dfd87e9b35fa8c5ae40b`:
  GitHub Actions run [41388233307](https://github.com/Iam-2squared/ark-ai/actions/runs/41388233307)
  **6/6 GREEN** on Ubuntu/Windows with Python 3.11–3.13 (all six jobs
  individually inspected). No standalone local pytest PASS is claimed.
  This documentation commit will have a distinct HEAD and must receive
  its own exact-head CI verification.

## Boundaries and follow-up

The input packet and retained file digest are still caller-supplied.
A SHA-256 field-path manifest cannot prove independently authenticated
filesystem custody, reviewer identity, explicit user consent, licensing
or provider billing protection. Keep approval and Candidate controls
fail-closed. Next, audit the full packet review path for type-exact
retained identities, path stability, and source-code pinning without
ever opening protected V2 evaluation or running a model.

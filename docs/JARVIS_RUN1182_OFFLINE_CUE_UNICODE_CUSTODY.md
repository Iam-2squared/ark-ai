# Run1182 — Offline transcript cue Unicode dependency custody

**Status:** implementation saved on an isolated Draft branch; exact-head CI pending. No PASS is claimed.

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `a27344061d5abc5304c44c03f7457005deb4c89d`.
- Child branch: `research/run1182-offline-cue-unicode-dependency-custody`.

## Finding and change

The disconnected wake-cue parser already rejected Unicode categories beginning with `C` and normalized text with NFKC, but it invoked the mutable `unicodedata` module directly. A replaced category or normalization callback could inspect or misclassify caller-supplied private transcript/cue text.

- Pin the import-time Unicode module, exact category function and exact NFKC normalizer.
- Check those identities before scanning transcript/cue text, and recheck between category scanning and normalization.
- Preserve the existing control/invisible-character rejection, NFKC case-folding, cue-boundary rules and byte budgets.
- Add synthetic tests for U+0600, U+FFF9 and U+E0001 in transcript and cue text, plus both dependency-substitution paths.

## Validation and limits

- No local pytest/Ruff run is claimed.
- Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.
- This is text-only fixture parsing, not acoustic wake-word detection, speaker authentication, consent, command authorization or Tool dispatch.
- Unicode dependency pinning is an in-process integrity check, not a Python sandbox or independent runtime attestation.
- No paid/external compute, paid service, Candidate, protected V2 evaluation, credentials, hardware, destructive operation, frozen-contract change, UI work or main merge is involved.

**ARK/JARVIS remains NOT_PASSED.**

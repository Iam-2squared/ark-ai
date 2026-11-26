# Run1181 — Transcript Unicode dependency custody

**Status:** implementation saved on an isolated Draft branch; exact-head CI pending. No PASS is claimed.

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `a27344061d5abc5304c44c03f7457005deb4c89d`.
- Child branch: `research/run1181-transcript-unicode-dependency-custody`.

## Finding and change

The detached transcript binder already rejected Unicode categories Cc, Cf and Cs and required NFC text, but it invoked the mutable `unicodedata` module directly. A replaced normalization or category callback could therefore inspect or misclassify caller-supplied private transcript text.

- Pin the import-time Unicode module, NFC normalizer and category classifier.
- Check exact dependency identities before any transcript text is passed to them and recheck between normalization, category scanning and UTF-8 encoding.
- Preserve the existing Cc/Cf/Cs rejection, NFC requirement, segment/total byte limits, frame bounds and denial-only output.
- Add synthetic tests for U+0600, U+FFF9 and U+E0001 and for both dependency-substitution paths.

## Validation and limits

- No local pytest/Ruff run is claimed.
- Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.
- Tests use synthetic transcript strings and metadata only. No audio is opened, no ASR is run, and no speaker identity, consent, external disclosure or Tool permission is inferred.
- Dependency pinning is an in-process integrity check, not a Python sandbox or independent runtime attestation.
- No paid/external compute, paid service, Candidate, protected V2 evaluation, credentials, hardware, destructive operation, frozen-contract change, UI work or main merge is involved.

**ARK/JARVIS remains NOT_PASSED.**

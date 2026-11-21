# Run1047 — V3 executable identity Unicode-control admission

## Finding

The non-executing V3 export planner already required an exact, bounded UTF-8
Python executable string and rejected blank, NUL, ASCII C0/DEL and malformed
UTF-8 input. It still accepted C1, bidi, zero-width, Unicode format and line
separator controls. Those characters can make the exact argv value visually
ambiguous in a later reviewed command display.

## Change

The optional V3 export-plan boundary now rejects those Unicode formatting
controls before snapshot validation, path inspection or converter/quantizer
identity reads. The original executable string remains verbatim in one argv
element; ordinary multilingual paths remain valid.

## Regression coverage

Synthetic cases cover C1, Arabic letter mark, zero-width, line separators,
bidi override/isolate, word joiner, soft hyphen and BOM. A valid Japanese
path remains unchanged. Poisoned snapshot, tool-identity and filesystem
callbacks prove the denial happens before those boundaries.

## Limits

This is validation-only. It does not invoke a subprocess, converter,
quantizer, model, GPU, training, Candidate, protected V2 evaluation, or
external service. It does not change frozen V3 Contract 1, provenance,
contamination, reproducibility, regression, approval, promotion or billing
gates. PR #5 remains Draft/unmerged; no main merge is requested.

# Run1057 — V3 preflight numeric and cross-binding regressions

- Target: gated Draft PR #5, `research/v3-learning-evaluation`.
- Exact parent HEAD: `c0ec757c9cdd240886d0008e3faec06beef8638b`.
- **Numeric-subclass tests:** source PR #166, original child HEAD `7cb189502b96c4e1da3bf3770f323cd2d9acf447`, exact-head CI run `44877364723` / run 6879, 6/6 GREEN (Windows Python 3.13 retry succeeded).
- **Evidence cross-binding tests:** source PR #169, original child HEAD `cf2d551d21b7b225d857687aa1342126eaa5314a`, exact-head CI run `44877732603` / run 6882, 6/6 GREEN.
- Scope is validation-only: numeric subclasses are rejected before conversion callbacks; synthetic mismatch and invalid-boundary matrix covers device, VRAM, tokenizer probe, allocated/reserved/capacity ordering and wall-time budget.
- No source or frozen Contract 1 change. No backend, GPU, model/tokenizer load, converter, quantizer, Candidate, training, protected V2 evaluation, promotion, payment or external compute.
- The original CI runs validate their original exact heads only. Fresh exact-head CI is required for this combined rebase; no GREEN result is transferred.

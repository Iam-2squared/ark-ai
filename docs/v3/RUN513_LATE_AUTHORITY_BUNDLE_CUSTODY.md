# Run513 — V3 offline identity bundle late-authority closure

**Status:** free-only, isolated source/test hardening on Draft PR #5; **NOT_PASSED** for V3 training/Candidate/protected evaluation. No paid GPU, model download, new credentials, training, Candidate, model-weight output or main merge.

## Exact code/test basis

- Initial PR #5 work-basis HEAD: a5292872750d25565abf0e5c76805060ba3eab61.
- Code update commit: edbae0716d4e20f4767e6bfc46cbdd8d9c47d8fb, source path src/ark/learning/identity_bundle_verify.py, blob 94c870e951e162a43d4eeec75171fdb5f13530ea.
- Test update commit / final source+test HEAD: b2b89d6423aa1d66a2188b22d0d5f8a9610ff723, test path tests/v3/test_identity_bundle_late_authority_run513.py, blob f8ed25ba31499116f4c8d39ab5063f531e631337.
- GitHub Actions CI on exact source+test HEAD: [run 41245097998](https://github.com/Iam-2squared/ark-ai/actions/runs/41245097998), observed **6/6 SUCCESS** across Ubuntu/Windows and Python 3.11/3.12/3.13. This is GitHub CI evidence, *not* locally executed pytest/Ruff.

## Security question

A retained bundle's four inert authority properties were checked **before** the second local bundle inspection. A reentrant final inspection could return a plausible pinned-hash report while changing a false-valued authority property on either the retained report or the newly checked report. The earlier check could not establish the *final* authority state.

The offline bundle verifier now checks all four authority properties on **both** the retained report and latest local report after that final bounded scan, then revalidates the retained report and pins after getters. An additional final-carrier check refuses a reflected equal-valued receipt-field replacement.

**Eight authored pytest cases:** four final-scan authority flags on retained report, two authority flags on latest report, one late equal-value carrier rewrite by a denial getter, and one ordinary no-effect success control.

## Explicit trust limits

- All test artifacts are small fixture JSON files already present locally.
- A SHA-256 match is a local byte consistency comparison, **not upstream Hub revision provenance**, immutable filesystem custody, independently authenticated model weights, or human review.
- The final file scan remains non-atomic against malicious OS/filesystem races. No grant, training authorization, Candidate generation, or protected V2 evaluation is implied.
- Frozen V3 Contract 1 at docs/v3/CONTRACT.md (blob b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23) is untouched.
- Physical upstream/tokenizer byte identity, reviewed train120/validation30, contamination decisions, exact runtime/device identities and explicit paid-compute permission remain blockers.

## Next plan

Continue independent local-only provenance/path/pin checks, offline fixture reproducibility and exact-head CI review. Do not alter frozen contracts or cross any training, paid-provider, Candidate, final-V2, promotion or main-merge gate.

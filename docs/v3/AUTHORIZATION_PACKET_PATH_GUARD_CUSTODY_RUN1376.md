# Run1376 — V3 authorization-packet path guard self-custody

## Exact basis

- Parent: Draft PR #5, `research/v3-learning-evaluation`.
- Parent work-basis HEAD: `49e03192b785419ba4d4a99c06f9a4c104a821e5`.
- Child branch: `research/run1376-v3-packet-path-guard-custody-20261125`.
- Corrected source commit: `bb2993a9b8668454a5fa2da65c676ab0479a0076`.
- Regression commit: `a849313bf096e5cc2dd44b50fb237e6f1aac15c2`.

## Change

The detached local authorization-packet reader now retains the original path-policy guard in function defaults. Its read path uses a local guard closure that checks both mutable module bindings against the retained callable before and after filesystem callbacks. The exact-type/reparse classifiers, ancestor checks and file-epoch reads receive that closure rather than resolving a mutable module global at each call.

The public packet review checks the retained guard before private work and again after file reads and the delegated verifier. This is local in-process mutation detection; it does not close filesystem ancestor TOCTOU races or establish independent custody.

## Regression

Synthetic local tests cover:
- simultaneous replacement of the path-policy helper and its module alias before packet access; and
- reentrant replacement from the packet path's `lstat` callback, which must be rejected before `os.open`.

## Evidence boundary

Only temporary local packet fixtures are used. No model/tokenizer load, torch runtime, GPU query, preflight, training, Candidate/weight generation, protected V2 evaluation, paid/external compute or service, credentials, hardware action, or main merge occurs. No V3 PASS is claimed; exact-head Windows/Linux × Python 3.11–3.13 CI is required. V3 Contract 1 and packet schema remain unchanged.

# Run1117 — Atomic pre-action slot identity and UNKNOWN-review compatibility

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD at branch creation: `c524935080889792b07f35c2eaefd5316c8dadb2`.
- Child branch: `research/run1117-atomic-preaction-slot-review-compat`.
- The original isolated path-seal implementation was PR #291, whose exact CI run `45046330989` failed at pytest on its then-current child head. This report does not treat that run as evidence for the new branch.

## Change

- Bring the slot-backed `DisconnectedAtomicPreactionLedger` path identity implementation onto the current foundation head.
- Update `review_atomic_unknown_outcome` to validate the ledger through the original `_require_ledger_path_epoch` function rather than expecting `_path` to live in `__dict__`.
- Require the retained instance dictionary to be empty at admission and after every callback boundary; recheck the original slot-backed path identity before continuing.
- Add a focused regression proving the UNKNOWN reviewer still returns a non-authorizing `UNCHANGED` classification for a healthy slot-backed ledger.
- Preserve the existing reflective retarget, dictionary-shadow, reentrant callback and exact-type denial tests.

## Failure analysis

PR #291's exact-head CI run `45046330989` reported 56 failures and 19,301 passes on its tested job. The repeated failure was `pre-action ledger instance changed`: the downstream UNKNOWN reviewer still required the pre-seal dictionary shape `{"_path"}`, although the new ledger stores `_path` and `_path_identity` in slots. The registered UNKNOWN bridge then surfaced its own fail-closed wrapper error. This is a consumer/representation mismatch, not evidence that the ledger should regain a mutable dictionary path.

## Preserved boundaries

No SQLite schema, event chain, sequence/CAS, commit ambiguity, replay or dispatch behavior changes. The reviewer remains read-only and manual-review-only. Reflective mutation is still checked by the lower-level path-epoch validator. Synthetic local fixtures only; no external effect, consent, trusted clock, independent custody or atomic cross-store claim.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. PR #8 remains Draft/unmerged, PR #5 remains gated Draft/unmerged, PR #9 remains untouched and UI stays paused. No paid compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware action or main merge. ARK/JARVIS remains NOT_PASSED.

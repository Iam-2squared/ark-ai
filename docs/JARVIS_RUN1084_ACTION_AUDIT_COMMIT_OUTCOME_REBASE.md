# ARK AI Run1084 — Action Audit COMMIT rollback and lost acknowledgement rebase

**Work basis:** Draft PR #8 branch `research/jarvis-foundations`, exact HEAD `916aae6c6578086fee5e83c77c23375712676c90`. Rebased from Draft PR #106 at `6771915bb4ba2618306242a0a6bb3036a8698f73d`, itself derived from test-only PR #101. PR #101's prior exact head `f905a0d35a225ffc443f3dcb543a0072cbd87f2a` passed CI run #44796254718 (6/6); that result does not transfer to this rebase.

## Regression

The synthetic SQLite test injects both rollback before native COMMIT and native-COMMIT success followed by a lost acknowledgement. Cold readback must show exactly the previous event prefix or exactly one new committed event. It checks event IDs, synthetic timestamp values, argument digests, SQLite `quick_check`, and absence of a private argument marker from durable bytes.

The audit remains diagnostic-only. It does not prove tool execution, authorize replay, or authenticate approval. Synthetic ToolCall identities and disposable local SQLite only; no ToolBackend, external effect, trusted clock, independent custody, authorization, automatic replay, Candidate, protected V2 evaluation, UI, paid service, or main merge.

The prior PR #101 exact-head CI run #44796254718 validated only its previous branch head. PR #106's old base was also stale. This rebased branch requires fresh exact-head CI; no local pytest/Ruff PASS is claimed.

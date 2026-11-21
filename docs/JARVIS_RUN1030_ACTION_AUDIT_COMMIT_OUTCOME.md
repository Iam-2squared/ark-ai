# ARK AI Run1030 — Action Audit COMMIT rollback and lost acknowledgement

**Work basis:** Draft PR #8 branch `research/jarvis-foundations`, exact HEAD `b585c61a6e3ca1a9f456175b2a96053a908a500c`. Rebased from test-only PR #101, whose previous exact head `f905a0d35a225ffc443f3dcb543a0072cbd87f2a` passed CI run #44796254718; that result does not transfer to this new head.

## Regression

The synthetic SQLite test injects both rollback before native COMMIT and native-COMMIT success followed by a lost acknowledgement. Cold readback must show exactly the previous event prefix or exactly one new committed event. It checks event IDs, synthetic timestamp values, argument digests, SQLite `quick_check`, and absence of a private argument marker from durable bytes.

The audit remains diagnostic-only. It does not prove tool execution, authorize replay, or authenticate approval. Synthetic ToolCall identities and disposable local SQLite only; no ToolBackend, external effect, trusted clock, independent custody, authorization, automatic replay, Candidate, protected V2 evaluation, UI, paid service, or main merge.

The prior PR #101 exact-head CI run #44796254718 validated only its previous branch head. This rebased branch requires fresh exact-head CI; no local pytest/Ruff PASS is claimed.

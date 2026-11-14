# Run754 — Non-UI exact CI repair, READ journal join source custody, startup source custody

This technical record is scoped to **free-only, disconnected/mock, read-only or fail-closed** ARK foundations. It does not authorize a tool, startup, notification, model training, Candidate export, V2 protected evaluation, or any billing.

## Exact work basis and what was saved

- Original PR #8 / `research/jarvis-foundations` HEAD: `2021bd58238ca3a1b9dcb316fbe6c04d3af6b88f`; Run753 checkpoint reported 28 tests without claiming fresh GREEN.
- **CI #42740157890** on that original HEAD: six jobs **FAIL**. Real Ubuntu 3.11 logs showed five Personal Context tests with an old regex diagnostic: the new `_require_original_search_protocol` now denies a replaced `hashlib.sha256` before the untrusted callback can install a forged class descriptor. The old tests expected the later descriptor rejection. That order is now intentionally fail-closed.
- Normal Contents API updates `447d509cf1fcef83efbef65c2ad9680a6821379b` and `b35fdd4fa26224bd559ce8eba1c12e21e4d0eec9` changed **only the affected test expectation** in the two existing context suites. No source privacy guard or codec rule was relaxed.
- **CI #42745755718** on intermediate HEAD `bf5b9e8853bfca3c78a2f5100d0c389555f2b88e`: six jobs **FAIL** at Ruff `E501` in the first repaired test, not proof of a pytest failure. Normal Contents API commit `d52d69fc946e06ae325db5645f21a819b8bb2fae` split that single `pytest.raises` line. No other test semantics changed.

## Package A — Detached READ journal join preaccess barrier

- Source commit `5df9f885ba1b5703c11bd89dbfe77d8922940c22`: `src/ark/agency/disconnected_read_recovery_journal_bridge.py` now binds the original carrier integrity validators from the read-journal module. It invokes those original validators **before** reading any snapshot witness/receipt property and at each reentrant `stable()` epoch. Forged frozen dataclass slot/lookup definitions are rejected rather than executed.
- Test commit `6f64445492e0e98b2f71ac8c3daed7611feca394`: `tests/test_read_recovery_journal_source_carrier_run754.py` adds **9** isolated cases: six source slot attacks, one validator substitution, one post-schedule getter injection, and one baseline valid inert join.
- Limitations: this is a synthetic digest-only READ receipt matching check, not independent stored witness custody, authenticated tool effects or automatic replay authorization. No executable WRITE path was enabled.

## Package B — Synthetic startup lease preaccess barrier

- Source commit `f3c40c9c4ce4d58a7d55461c4275aaf3b7e0fe25`: `src/ark/startup_readiness_lease_review.py` now pins its original signed-64-bit clock bound, 512-requirement budget and imported startup graph constructor/slot validator. It checks these before probe metadata access, and again across callback epochs.
- Test commit `bf5b9e8853bfca3c78a2f5100d0c389555f2b88e`: `tests/test_startup_lease_source_budget_run754.py` adds **8** isolated cases: two limit rewrites, four forged source slots, one validator replacement, one baseline denial-only READY review.
- Limitations: even a passing synthetic READY lease is **not** proof of a physical PC, trusted clock, authenticated permission, hardware availability or safe ToolBackend dispatch.

## Package C — Retained Memory epoch input and output integrity

- Source commit `4e4c57ab4c0c98161b655b93d2d48f13ea287a01`: `src/ark/memory/retained_epoch_review.py` now pins retained row/event grammar, numeric budgets, original JSON/SHA-256 implementations, the imported raw AtomicMemoryEpochReview slots and lookup machinery, plus the inert comparison-result slots. It rejects a forged parser, codec or executable field descriptor *before* reading private scope fingerprints and rechecks across digest epochs. No Memory v1 schema or write behavior changed.
- Test commit `f09a9baabb078c324a09a54ffaac122699e4061a`: `tests/test_memory_retained_epoch_input_protocol_run754.py` adds **12** synthetic scenarios: five grammar/budget mutations, two hostile codec substitutions, two forged private review slots, two forged output slots and one baseline unchanged-snapshot denial-only receipt.
- This is a detached local comparison, not authenticated append-prefix custody, a cross-store atomicity guarantee, a write lock, consent, retention authorization or disclosure approval.

## Verification and follow-up

- New cases authored in this invocation: **29 total** (9 + 8 + 12). The number denotes parametrized cases added, **not** confirmed passing runs.
- First CI-repair HEAD: `d52d69fc946e06ae325db5645f21a819b8bb2fae`; later Memory source/test HEAD: `f09a9baabb078c324a09a54ffaac122699e4061a`. Automatically triggered CI [#42745942405](https://github.com/Iam-2squared/ark-ai/actions/runs/42745942405) was **IN PROGRESS** at the last job check; do not transfer its result to this documentation commit or a later checkpoint SHA.
- No independent local full test suite run and no physical Windows/GGUF gate. If CI fails, inspect actual job logs, repair only via normal allowed Contents API, then switch to another non-UI lane.
- PR #8 stays Draft/unmerged. PR #5 V3 and PR #9 UI stay Draft/unmerged; PR #9 receives no source, test, build or integration changes. Frozen V1/V2/Local UI/Launcher contracts and evidence unchanged. No paid service/external GPU, Candidate/weight generation, real sensor/tool action, protected evaluation, or main merge.

## Prioritized next dependency gates

1. Confirm exact source+test and final checkpoint HEAD CI (six Windows/Ubuntu Python 3.11–3.13 jobs) and fix only evidenced failures.
2. Independently close memory CAS/ABA, coherent snapshot, global row/event high-water, expiry and ambiguous COMMIT-UNKNOWN invariants.
3. Reconcile Planner persistent READ recovery with immutable registry, exact PermissionGate, trusted-clock and audit-before-action **without** granting execution on diagnostic receipts; connect mock Executor only after lower-layer exact-HEAD GREEN.
4. Continue privacy-safe Personal Context lifecycle, proactive scheduler and observation fixture contracts. V3 remains zero-spend and protected evaluation/promotion strictly gated.

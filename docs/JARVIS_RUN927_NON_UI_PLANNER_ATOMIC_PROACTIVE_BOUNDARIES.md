# ARK AI Run927 — Planner SQLite admission, atomic unknown custody, proactive policy pregetter

**Report prepared (Asia/Tokyo): 2026-11-17T06:25:12+09:00.** Isolated, zero-cost, disconnected non-UI safety work. **Work-basis HEAD:** `c85c0333d50e5f985d32fc34c2a72431923d40f0` (Run926 source/test/report, no Run926 status checkpoint yet). **Complete source/test HEAD:** `2b78fa26382bdbec522aaf1a030223ed57be3290`. All changes on Draft PR #8 `research/jarvis-foundations`; PR #5 and paused UI PR #9 untouched; no main merge.

## 1. Planner retained SQLite state — 13 regression cases authored

- [Test commit `f38c9033`](https://github.com/Iam-2squared/ark-ai/commit/f38c90331ac5ef37860edde8287124f05f49e1e5): `tests/test_planner_journal_sql_hydration_run927.py`.
- Eight malformed event-field SQLite cases (overlong step/state/digests, wrong revision/clock TEXT) require the existing `_replay` SQL-side admission to reject the row **before** Python event iteration. Four malformed header cases reject before header value hydration. All verify rejection does not rewrite the stored row. One healthy cold restart retains RUNNING as ambiguous, no dispatch or automatic replay.
- **No frozen Planner graph/schema or event format changed**; these tests increase adversarial coverage of already-existing SQL-side read budget.

## 2. Atomic pre-action COMMIT-UNKNOWN — 15 regression cases authored

- [Test commit `7f8bde49`](https://github.com/Iam-2squared/ark-ai/commit/7f8bde499ec6726162155c5ce9d5c0ba0aee9da7): `tests/test_atomic_unknown_carrier_custody_run927.py`.
- Twelve synthetic `AtomicUnknownOutcomeReview` slot/authority/lookup-hook replacements and two ledger attribute-lookup replacements must be rejected **before** the injected method runs or any SQLite review grants authority. One healthy local-empty baseline remains strictly manual-only, with no dispatch, consent or proof of external effects.
- This is an internal-local witness and test of existing constructor-boundary checks, **not** a durable one-shot WRITE permission issuer, authenticated time source, or action executor.

## 3. Proactive policy — source pregetter guard and 21 regressions authored

- [Source commit `09086860`](https://github.com/Iam-2squared/ark-ai/commit/09086860f2e6b92c2daebb84707ab6f591d6613f) and [test commit `2b78fa26`](https://github.com/Iam-2squared/ark-ai/commit/2b78fa26382bdbec522aaf1a030223ed57be3290).
- `SyntheticTriggerPolicy.__post_init__` and `identity` now invoke their existing import-pinned policy contract check before the first instance field getter. This prevents a class-level reflected slot or lookup hook from being executed during these direct validation/review entry points. Twenty field/method × entry-point fixtures and one healthy policy identity case.
- No schedule cursor advanced, no notifications or real tools, no external clock trusted, no consent claimed. Generated policy identity and existing persistence schema unchanged for valid callers.

## Exact CI boundaries and reliability

- Run925 checkpoint `2d703564`: [CI #43945718308](https://github.com/Iam-2squared/ark-ai/actions/runs/43945718308) **FAIL 6/6** (eight Ubuntu pytest failures included changed expected errors and privacy pregetter race); no Run925 PASS claim.
- Run926 recovery [CI #43953657924](https://github.com/Iam-2squared/ark-ai/actions/runs/43953657924) **GREEN 6/6**, Run926 Memory [CI #43954423571](https://github.com/Iam-2squared/ark-ai/actions/runs/43954423571) **GREEN 6/6**, **these are earlier SHA boundaries, not a latest overall PASS.**
- Run926 source/report [CI #43956863463](https://github.com/Iam-2squared/ark-ai/actions/runs/43956863463) is still completing; Run927 Planner [#43958504813](https://github.com/Iam-2squared/ark-ai/actions/runs/43958504813), Atomic [#43958824248](https://github.com/Iam-2squared/ark-ai/actions/runs/43958824248), Proactive source [#43959294740](https://github.com/Iam-2squared/ark-ai/actions/runs/43959294740), complete source/tests [#43959425252](https://github.com/Iam-2squared/ark-ai/actions/runs/43959425252): **QUEUED/IN PROGRESS at initial review; 6/6 latest exact-head GREEN not yet proven.**
- **49 synthetic cases authored, not independently certified as PASS.** Local AST syntax checked on authored test source, but there is no complete local pytest run or physical-PC/GGUF evidence.

## Preservation, limitations and next plan

Frozen V1/V2/Local UI/Launcher and protected evaluation contract untouched. PR #5 and PR #9 remain Draft/unmerged, UI paused; no paid APIs/GPU/compute, subscriptions, Candidate adapters/weights, protected V2 evaluation, real WRITE, user data, credentials, physical-PC claims, automatic UNKNOWN retry, destructive operations, hidden Git bypass or main merge.

**Blockers:** latest complete matrix still pending; WAL/SHM multi-process path/alias race unresolved; independent trusted clock, authenticated human consent and restart-safe one-shot authorization unproven; Memory coherent CAS/expiry and Planner external effects not authenticated. JARVIS overall **NOT_PASSED**.

**Next plan / 今後の方針:** (1) Finish exact-head CI and correct any regression without relaxing safety. (2) Continue disposable WAL/SHM alias-handle research and Memory/Planner bounded retained snapshots. (3) Reconcile registry-bound permissions with durable occurrence and audit only after each lower-level head has GREEN CI; disconnected mock only, no real dispatch. (4) Continue privacy-safe Personal Context and Observation backend contracts/free V3 guards on independent lanes; UI stays paused.

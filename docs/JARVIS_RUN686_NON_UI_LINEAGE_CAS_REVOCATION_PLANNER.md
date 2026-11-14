# ARK AI — Run686 FREE-ONLY non-UI core hardening and recovery fixtures

Date: **2026-11-07 JST**. Branch **`research/jarvis-foundations`**, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), unmerged. Work-basis: `0d83c8968866ff144b457bf2c611f74fd044ab19` (Run685 checkpoint). Latest source/test HEAD before this report: `41d9bb89dfcf083c4e77db4f1101bb358485e4bb`. This is an evidence note, NOT a PASS declaration or an action authorization.

## New independent packages

1. **Observation lineage import-original digest custody** — `src/ark/observation_lineage_review.py`. Pin the original `hashlib`/`json` objects, `sha256`/`dumps` callables and byte-domain object, and refuse replacement before `ObservationWindowReview` can read private fixture fields. Recheck during per-envelope and final identity passes. New `tests/test_observation_lineage_digest_custody_run686.py` covers four replacement forms, an equal-value/new-identity domain, and deterministic two-step lineage (**6 new cases**). Source commit `c0e82b01a4cccc1d5532a58cda0a171e779a4148`; test commit `0c211671f0537610d1a0ebd410c1397572627d5b`. Import spacing corrected in `4a1f61022ab05daa792e3ff8ef7efdd9967e7e96`. Two older callback-injection fixtures were adjusted to assert earlier **non-execution**, not weaker acceptance: `a5e0435777818619a255b26f45fb0656ecdb61e4`, `41d9bb89dfcf083c4e77db4f1101bb358485e4bb`.
2. **Memory unrelated expiry/CAS isolation** — `tests/test_memory_unrelated_expiry_purge_cas_run686.py` (**6 new cases**), commit `524340b48d410d8a548a4a44150f7a61cbb2347d`. A different SQLite connection purges an expired row belonging to another owner, another namespace or another source in the same scope; half the cases recreate the expired foreign generation. A still-live target's retained generation CAS remains valid, returning revision 2 with no inferred author identity or consent.
3. **Personal Context privacy revocation and row lifetime ABA** — `tests/test_private_revocation_recreated_row_run686.py` (**3 new cases**), commit `79755025839e4298187514055e67cbd882b948f4`. Manual delete/recreate, expiry purge/recreate and a second same-scope Memory source all retain the scope's denial after re-opening independent SQLite handles. Local retention inventory has no use/erasure authority. Backups or global deletion cannot be certified.
4. **Planner two-writer durable terminal CAS** — `tests/test_planner_independent_terminal_cas_race_run686.py` (**4 new cases**), commit `681c649cce14b4ec0438c710e88521fcce19cd14`. Independent journal handles cannot append two RUNNING/terminal transitions for one step revision. Both readers recover the same two-event terminal outcome and derived descendant BLOCKED/PENDING state, never permission for backend dispatch/replay. Ruff import formatting fixed in `ffdaf6280b3df7c8bf82aefb646d59ae25a713fb`.

**Total: 19 new parameterized cases across four new test files, one production module strengthened, two inherited test modules adapted.** All packages are synthetic/offline, no external I/O other than existing GitHub source and automatic public-repository CI.

## CI and evidence (sampled; exact-HEAD discipline)

- Incoming prior checkpoint `0d83c8968866ff144b457bf2c611f74fd044ab19`: [#42369977723](https://github.com/Iam-2squared/ark-ai/actions/runs/42369977723) **COMPLETED 6/6 GREEN** (Windows/Ubuntu × Python 3.11–3.13).
- Early source commit `c0e82b01a4cccc1d5532a58cda0a171e779a4148`: [#42373962754](https://github.com/Iam-2squared/ark-ai/actions/runs/42373962754) **FAIL**, due to Ruff import-block spacing before pytest. The test-inclusive ancestor commits inherited that formatting failure; no test-pass claim can be taken from those runs.
- Ancestor `4a1f61022ab05daa792e3ff8ef7efdd9967e7e96`: [#42374343737](https://github.com/Iam-2squared/ark-ai/actions/runs/42374343737) initially encountered a different Ruff import-group formatting failure in the Planner test; corrected in `ffdaf6280b3df7c8bf82aefb646d59ae25a713fb`.
- With import corrections, `ffdaf6280b3df7c8bf82aefb646d59ae25a713fb` [#42374416662](https://github.com/Iam-2squared/ark-ai/actions/runs/42374416662), **IN PROGRESS when sampled**. Two earlier observation serializer-hook tests were thereafter proactively updated to match the stronger pre-read guard, without changing production refusal.
- Corrected source/test HEAD `41d9bb89dfcf083c4e77db4f1101bb358485e4bb`: [#42374561830](https://github.com/Iam-2squared/ark-ai/actions/runs/42374561830), **3/6 Ubuntu GREEN, three Windows IN PROGRESS** when sampled at around 12:59 UTC. All-six GREEN for this HEAD is **not yet attested**. Automatic CI for the report-inclusive and checkpoint-result HEADs must be verified independently. No equivalent manual reruns triggered.
- The model-host UTC/JST clock and local SHA-256 fixtures are **not authenticated action audit clocks**, historical writer identity, consent, trusted provenance or independent reality attestations.

## Preserved gates and gaps

- Main remains `7a843f17eb96ed13d66f23b58b06406b3002e405`; V1/V2/Local UI/Launcher frozen contracts, evidence and protected V2 evaluation remain unopened and unchanged.
- [Draft V3 PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) remains unmerged at `805b377697472268db02650a89c7a94b1c5337c8`. Its `docs/v3/PRE_PAID_COMPUTE_GATE.md` still lacks immutable materialized model/tokenizer/software identities, 120/30 data rights/contamination human reviews, pinned proposed hardware/cost ceiling and **explicit separate approvals**. No preflight GPU, Candidate, actual training, promotion or evaluation opening.
- [Draft UI PR #9](https://github.com/Iam-2squared/ark-ai/pull/9) remains unmerged at `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`. **UI paused and untouched**.
- Independent SQLite occurrence, audit, authorization, Planner and Memory ledgers are **not cross-store atomic**. A successful local synthetic correlation is not global exactly-once real-world execution. COMMIT-UNKNOWN requires manual reconciliation, not automatic WRITE retry. No new account, paid service, GPU, credential, physical PC, destructive action, or main merge.

## Next plan / 今後の方針

1. Obtain exact-head six-job verdicts, inspect any failed log and repair only a proven regression via the ordinary GitHub Contents path. Do not transfer an ancestor verdict to a newer HEAD.
2. Extend independent mock authorization/occurrence/audit crash matrix and Planner per-step recovery proof without real WRITE dispatch; keep unknown outcomes non-replayable.
3. Continue Memory event/row coherent snapshots, CAS/ABA/expiry and privacy lifecycle, then startup/proactive readiness and observation backend contracts; no UI or V3 paid-gate crossing.

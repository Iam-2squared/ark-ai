# ARK AI Project Status

**LATEST**

Saved at: **2026-09-28 16:15:50 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / Draft PR #8

Work-basis HEAD: `4b0ae97e85c2d7987b396c527b455d56b7360f4a`

Checkpoint-result HEAD: this file cannot contain the SHA of the commit that writes itself; use the commit produced by this checkpoint update.

## Current state

V1/V2/Local UI/Launcher remain frozen and passed. V3 remains Draft/unmerged under its frozen Contract. JARVIS foundation work remains isolated/reversible and is not a roadmap PASS. At the work-basis HEAD, PR #8 is open, Draft, mergeable, 41 commits ahead and 0 behind `main`.

## New work this session

- `4b0ae97e85c2d7987b396c527b455d56b7360f4a`: extended isolated foundation prototype evidence with planner input reproducibility and action-observability occurrence identity checks.
- Planner dependency nondeterminism was reproduced across interpreter hash seeds: the same four names produced 9 distinct tuple orders across 12 fixed `PYTHONHASHSEED` values when sourced from a set.
- The source-ready planner hardening prototype revalidated immutable topology/status views, exact typed `StepState` transitions, exact non-bool non-negative revisions, ordered dependency input, and transitive blocking.
- A local typed observability-event prototype now binds action telemetry to both canonical request identity and execution-occurrence identity. It was deterministic across 100 randomized provenance orders, rejected 5/5 malformed boundary cases, and kept repeated identical requests with distinct execution IDs separate.
- Free-only PR #5 review identified an additional evidence-semantics gap: preflight/full-run persisted `wall_seconds` currently measures only the optimizer/training phase, while the controlling `WallTimeBudget` covers a larger setup/load/save interval. The timeout guard remains controlling, but persisted duration must not be interpreted as total guarded runtime until cross-bound.
- The existing PR #5 Candidate output path gap was re-reproduced without GPU work: the current local path predicate allows a new output directory inside the frozen base directory because canonical source/output separation is not yet enforced.
- Normal executable-source planner hardening and several follow-up documentation updates were re-attempted only after exact-head/blob reads and were rejected by the tool safety path. No bypass, force push, raw tree/ref write, or alternate unsafe path was used.

## Tests / CI / evidence

- CI #186 / run `36385907622` on prior exact HEAD `4a7e695ed0aa7a44bfa473983eefcffeb6f913a9`: SUCCESS, 6/6 jobs GREEN.
- CI #187 / run `36390441704` on work-basis HEAD `4b0ae97e85c2d7987b396c527b455d56b7360f4a`: SUCCESS. The latest job read showed Ubuntu/Windows × Python 3.11/3.12/3.13 all 6/6 jobs completed successfully.
- Planner source-ready isolated prototype: immutable views 2/2 PASS; invalid raw states 3/3 rejected; invalid revisions 3/3 rejected; unordered dependency input rejected; transitive blocking PASS.
- Observability envelope isolated prototype: 100/100 provenance-order permutations deterministic; 5/5 malformed boundary cases rejected; distinct execution-occurrence identity separation PASS.
- PR #5 remains Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`.
- Prototype-only checks remain explicitly separate from repository implementation evidence.

## Frozen boundaries unchanged

Frozen V1/V2/Local UI/Launcher evidence is unchanged. V3 Contract semantics are unchanged. Protected V2 final evaluation remains unopened. No Candidate weights, promotion, paid/external compute, destructive action, or main merge occurred.

## Blockers / authorization boundaries

Normal writes to executable source/tests remain blocked by the tool safety path. Some documentation updates were also rejected while the prototype-evidence update succeeded. Existing authorization gates remain in force for paid/external compute, real Candidate generation, protected evaluation, promotion, frozen-contract changes, destructive/irreversible work, new credentials/account connections, unavailable physical-PC actions, and main merge. No new user-action blocker was introduced.

## Next plan / 今後の方針

1. Retry only the normal source path for planner invariant hardening after an exact-head re-read; add ordered-sequence dependency validation and matching repository tests when that path is accepted.
2. Land Memory durability, persisted-row integrity, snapshot-before-expiry-clock search semantics, CAS normalization, and revision-bound expiry cleanup.
3. Harden Action Audit initialization, supported-schema shape/integrity checks, lock-before-clock ordering, and persisted request/digest validation.
4. Implement the reusable local-state migration/startup-readiness source and process recovery tests.
5. Continue immutable ToolRegistry, durable one-shot authorization, execution-occurrence reconciliation, and mock ActionExecutor integration.
6. Add typed local observability source with request+execution occurrence correlation and content-free provenance.
7. Continue Personal Context, proactive scheduler, typed observation, and V3 free-only canonical path/resource/runtime-evidence guard work as dependencies permit.

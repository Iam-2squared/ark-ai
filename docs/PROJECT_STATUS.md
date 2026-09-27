# ARK AI Project Status

**LATEST**

Saved at: **2026-09-27 17:27 JST (+09:00)**

Branch/PR: research/jarvis-foundations / Draft PR #8

Work-basis HEAD: 50f9784c707299b6661bc3a33e33c958b35b000c

Overall state: V1/V2/Local UI/Launcher remain frozen and passed. V3 remains Draft/unmerged under its frozen Contract and authorization gates. JARVIS foundations remain isolated, reversible research groundwork and are not a roadmap PASS. PR #8 is 16 commits ahead / 0 behind main at the work basis and is mergeable/Draft.

New this session: re-audited PR #8, PR #5, the dependency graph, planner, memory, agency policy/audit, and exact-head CI. Prepared planner immutable-view/exact-type hardening against the exact current bytes, but executable-source/test writes were rejected by the normal GitHub safety path and are not counted as repository progress. Independently validated a restart-safe SQLite one-shot authorization design, immutable ToolRegistry, audit-before-action executor ordering, Personal Context isolation/fairness/provenance, persisted-memory integrity/CAS/schema/concurrency hardening, and V3 preflight/export guards in isolated local prototypes.

Prototype validation this session: 24 foundation tests PASS + compileall PASS; bounded concurrency stress covering durable one-shot consumption, concurrent authorization DB first-open, same-revision Memory CAS, and Memory DB first-open passed 5 repeated runs. A separate V3 guard prototype passed 17 tests covering device/VRAM/tokenizer/wall-time cross-binding and canonical export path/source-tree/symlink/current-model alias rejection. During schema-shape validation, SQLite's rowid-table PRIMARY KEY behavior was explicitly accounted for: primary-key NOT NULL must be declared if the validator expects PRAGMA table_info.notnull=1.

Pre-existing repository progress: planner syntax is repaired, agency Ruff blockers are cleared, and the JARVIS foundation/dependency documentation is present. No source change from the isolated prototypes above is represented as committed work.

Tests/CI/evidence: exact work-basis HEAD 50f9784c707299b6661bc3a33e33c958b35b000c; CI #162 / run 36303618600 = SUCCESS with all six Ubuntu/Windows × Python 3.11/3.12/3.13 jobs GREEN. PR #5 remains Draft/unmerged at d6d4c1954a85fc716b1c593ac55c85417912418f. No duplicate workflow rerun was launched.

Frozen contracts/evidence unchanged: V1/V2/Local UI/Launcher evidence is unchanged. V3 Contract semantics are unchanged. Protected/frozen V2 final evaluation remains unopened. No Candidate adapter/weights were generated or promoted. No paid/external compute was used.

Unresolved boundaries/blockers: normal GitHub writes to executable source/tests, and a new foundation specification file, were rejected by the safety path despite exact-head rechecks. This is treated as a path-specific tooling blocker, not authorization to bypass safeguards. Existing authorization boundaries remain unchanged: paid/external compute, real Candidate generation, protected evaluation opening, Candidate promotion, frozen-contract changes, destructive actions, credentials not already authorized, and main merge require their controlling authorization.

Next plan / 今後の方針: keep the exact-head CI baseline green; retry normal source writes without bypassing safeguards; persist planner immutable/exact-type hardening first, then Memory persisted-integrity/schema/concurrency/retention hardening, durable one-shot authorization, immutable ToolRegistry, trusted-clock audit-before-action execution, Personal Context retrieval, and V3 resource/export cross-binding guards. Continue independent local validation while any one write path is unavailable.

Checkpoint-result HEAD is not self-recorded inside this commit; record it from the subsequent repository state when needed.

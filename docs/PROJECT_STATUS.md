# ARK AI Project Status

**LATEST**

Saved at: **2026-09-27 16:43 JST (+09:00)**

Branch/PR: research/jarvis-foundations / Draft PR #8

Work-basis HEAD: 759527828f14f33618ea25a9744c9d121856299a

Overall state: V1/V2/Local UI/Launcher remain frozen and passed. V3 remains Draft/unmerged under its frozen Contract and authorization gates. JARVIS foundations are isolated, reversible research groundwork and are not a roadmap PASS.

New this session: refreshed the canonical checkpoint against the actual latest foundation head and re-audited PR #8, PR #5, the dependency graph, planner, memory store, agency contracts/policy/audit, focused tests, and exact-head CI. PR #8 is 15 commits ahead / 0 behind main at the work basis. The exact-head CI baseline is GREEN. Two source hardening writes were prepared from the current bytes (planner immutable/exact-type state guards and persisted-memory integrity validation) but the normal GitHub source-write path was blocked by safety checks, so those changes are explicitly NOT counted as repository source progress.

Pre-existing repository progress: the malformed planner source was repaired, agency contract Ruff findings were cleared, and docs/JARVIS_FOUNDATIONS.md plus docs/JARVIS_DEPENDENCY_GRAPH.md document the continuous-system architecture and hard boundaries. Those changes were already present before this checkpoint refresh.

Tests/CI/evidence: exact work-basis HEAD 759527828f14f33618ea25a9744c9d121856299a; CI #161 / run 36300580512 = SUCCESS with all six Ubuntu/Windows × Python 3.11/3.12/3.13 jobs GREEN. PR #5 HEAD d6d4c1954a85fc716b1c593ac55c85417912418f; its previously recorded CI #151 / run 36223644908 = SUCCESS. No duplicate workflow rerun was launched.

Frozen contracts/evidence unchanged: V1/V2/Local UI/Launcher evidence is unchanged. V3 Contract semantics are unchanged. Protected/frozen V2 final evaluation remains unopened. No Candidate adapter/weights were generated or promoted.

Unresolved boundaries/blockers: normal GitHub writes to executable source are currently being rejected by the safety path even when based on the exact latest HEAD. This is treated as a path-specific tooling blocker, not authorization to bypass safeguards. Existing authorization boundaries remain unchanged: paid/external compute, real Candidate generation, protected evaluation opening, Candidate promotion, frozen-contract changes, destructive actions, credentials not already authorized, and main merge require their controlling authorization.

Next plan / 今後の方針: keep the exact-head CI baseline green; retry normal source writes without bypassing safeguards; first persist planner immutable/exact-type hardening plus tests, then persisted-memory integrity/schema/concurrency/retention hardening, durable one-shot authorization and audit-before-action execution, personal-context retrieval, immutable tool registry, and V3 resource/export guards. While any one path is blocked, continue validating independent foundations and keep this checkpoint aligned to the actual repository state.

Checkpoint-result HEAD is not self-recorded inside this commit; record it from the subsequent repository state when needed.

# ARK AI Project Status

**LATEST**

Saved at: **2026-09-27 06:50 JST (+09:00)**

Branch/PR: research/jarvis-foundations / Draft PR #8

Work-basis HEAD: e74157a481b008f9cdc638cdcac24ab67e29d0ad

Overall state: V1/V2/Local UI/Launcher remain frozen and passed; V3 remains Draft/unmerged; continuous JARVIS foundations remain isolated research and are not a roadmap PASS.

New this session: inspected exact repository/PR/CI state; attempted the first PR #8 Ruff correction. The planner Mapping import was modernized, but the same commit accidentally encoded two line breaks as literal \\n text in planner.py. CI #154 therefore remains red and the branch must be repaired before any further integration. No frozen evidence, V3 contract, protected evaluation, Candidate state, or main branch was changed.

Local-only validation (NOT repository-persisted): prepared memory persisted-row integrity and race-safe expiry hardening; immutable/type-safe planning; durable SQLite one-shot authorization with restart replay protection; trusted-clock audited ActionExecutor; same-version SQLite schema checks. Isolated foundation tests: 52 PASS plus compileall PASS. Prepared V3 preflight/training cross-field VRAM+timeout checks and canonical export-path separation; isolated tests: 15 PASS plus compileall PASS.

Tests/CI: foundation CI #153 / run 36271813169 failed at six Ruff findings before pytest. After the planner edit, CI #154 / run 36273940101 failed; four original Ruff findings remain and planner.py additionally contains the malformed literal line-break text introduced above. V3 CI #151 / run 36223644908 remains SUCCESS.

Frozen contracts/evidence unchanged.

Unresolved / authorization boundaries: first priority is restoring valid planner.py and clearing the remaining semantics-preserving Ruff findings. GitHub source writes are intermittently being rejected by the write safety path; do not bypass it. Existing V3 hard stops remain unchanged: no paid/external GPU compute, Candidate generation/promotion, protected V2 opening, frozen-contract change, or main merge.

Next plan / 今後の方針: (1) repair planner.py at the latest exact HEAD; (2) clear the remaining Ruff-only findings and run exact-head CI through pytest; (3) persist the already validated planner/memory/durable-authorization hardening in coherent tested chunks; (4) continue V3 preflight/run-manifest/export reproducibility hardening in parallel without crossing the training/evaluation gates.

# ARK AI Project Status

**LATEST**

Saved at: **2026-09-27 17:39 JST (+09:00)**

Branch/PR: research/jarvis-foundations / Draft PR #8

Work-basis HEAD: c2c80e51929f647c87d8d9e299490f9259d3f940

Overall state: V1/V2/Local UI/Launcher remain frozen and passed. V3 remains Draft/unmerged under its frozen Contract and authorization gates. JARVIS foundations remain isolated, reversible research groundwork and are not a roadmap PASS. PR #8 remains cleanly ahead of main with no mainline merge performed.

New this session: refreshed the canonical checkpoint from the actual PR #8 head, re-audited PR #8/PR #5/dependency state/CI, and expanded isolated implementation validation across planner, Memory, durable authorization, action audit, ToolRegistry, ActionExecutor, Personal Context, and V3 resource/export guards. Executable-source/test writes were retried only through the normal GitHub contents path after exact-head rechecks; those writes were rejected by the safety path and therefore are NOT counted as repository source progress.

Prototype validation completed this session: 33 foundation tests PASS + compileall PASS. The validated foundation behaviors include immutable planner topology/status views; exact StepState and non-bool revision inputs; immutable ToolRegistry resolution; restart-safe SQLite one-shot authorization with token digest only; request/expiry binding; same-version schema-shape validation; exactly-once concurrent consumption; trusted-clock audit-before-action execution; token consumption surviving audit/backend failure; READ execution without one-shot; persisted Memory content/identity/metadata/time integrity; update/delete/purge validation; clock-rollback rejection; same-revision CAS exactly-one winner; concurrent first-open initialization; owner/namespace-isolated Personal Context; deterministic cross-namespace fairness; duplicate-identity rejection; plaintext-free provenance; action-audit schema/row integrity; and content-free audit storage.

Bounded concurrency stress: durable authorization concurrent consumption + concurrent first-open, Memory same-revision CAS + concurrent first-open, and action-audit concurrent first-open passed 5 repeated runs. During SQLite schema-shape work, rowid-table PRIMARY KEY nullability was explicitly handled: if a validator expects PRAGMA table_info.notnull=1 for a text primary key, the DDL must declare NOT NULL PRIMARY KEY explicitly.

Separate V3 guard prototype validation: 17 tests PASS + compileall PASS covering tokenizer/device/VRAM/wall-time cross-binding, allocated VRAM <= reserved VRAM <= measured capacity, bool/NaN/infinity rejection, canonical base/merged/output separation, source-tree output rejection, symlink-parent alias rejection, and Current deployed model -> Candidate-source alias rejection. No training, Candidate generation, protected evaluation opening, promotion, or external compute occurred.

Repository tests/CI/evidence: exact work-basis HEAD c2c80e51929f647c87d8d9e299490f9259d3f940; CI #163 / run 36306760632 = SUCCESS with all six Ubuntu/Windows × Python 3.11/3.12/3.13 jobs GREEN. The preceding exact-head CI #162 / run 36303618600 was also GREEN. PR #5 remains Draft/unmerged at d6d4c1954a85fc716b1c593ac55c85417912418f. No duplicate workflow rerun was launched.

Frozen contracts/evidence unchanged: V1/V2/Local UI/Launcher evidence is unchanged. V3 Contract semantics are unchanged. Protected/frozen V2 final evaluation remains unopened. No Candidate adapter/weights were generated or promoted. No paid/external compute was used.

Unresolved boundaries/blockers: normal GitHub writes to executable source/tests remain rejected by the safety path despite exact-head rechecks. This is treated as a path-specific tooling blocker, not authorization to bypass safeguards. Existing authorization boundaries remain unchanged: paid/external compute, real Candidate generation, protected evaluation opening, Candidate promotion, frozen-contract changes, destructive actions, credentials not already authorized, and main merge require their controlling authorization.

Next plan / 今後の方針: keep exact-head CI green; retry only normal source writes without bypassing safeguards; persist planner immutable/exact-type hardening first, then persisted-Memory integrity/schema/concurrency/retention hardening, durable one-shot authorization, action-audit integrity, immutable ToolRegistry, trusted-clock audit-before-action execution, Personal Context retrieval, and V3 resource/export cross-binding guards. While source writes remain blocked, continue independent local validation rather than idling.

Checkpoint-result HEAD is not self-recorded inside this commit; record it from the subsequent repository state when needed.

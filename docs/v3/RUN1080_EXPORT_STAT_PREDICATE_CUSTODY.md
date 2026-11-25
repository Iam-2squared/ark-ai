# Run1080 — V3 export stat-predicate custody

Work basis: Draft PR #5 branch `research/v3-learning-evaluation`, exact parent HEAD `2ddc32a69dd32541497373ac76be2c1db332f88f`.

## Finding

The non-executing export planner rejected lexical traversal, symlink/reparse metadata, non-regular files and model/output overlap, but its mode classifications called the live `stat.S_ISDIR`, `stat.S_ISREG` and `stat.S_ISLNK` functions. Rebinding the imported `stat` module or one predicate could therefore change the local path classification before an export plan was returned.

## Change

The isolated child pins the import-original `stat` module and all three mode predicates. Export path policy admission now rejects module/predicate substitution before filesystem inspection, reads mode and reparse attributes as one bounded metadata epoch, rechecks the policy after metadata access, and classifies with the captured original predicates. Canonical path resolution rechecks the same policy after resolving.

Five synthetic tests cover module rebinding, each predicate, and metadata callbacks that replace predicates. No converter, quantizer, model, GPU, training, Candidate or external service is invoked.

## Boundaries

This is local in-process dependency-identity hardening, not a sandbox, atomic directory-handle traversal, trusted filesystem custody, or authorization. V3 Contract bytes, preflight/compute gates, protected V2 evaluation, Candidate promotion, PR #5 Draft state, and all frozen V1/V2/UI/Launcher evidence remain unchanged. No paid or potentially billable action is performed.

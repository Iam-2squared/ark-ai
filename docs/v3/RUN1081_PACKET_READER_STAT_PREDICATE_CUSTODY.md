# Run1081 — V3 authorization-packet reader stat custody

Work basis: gated Draft PR #5 branch `research/v3-learning-evaluation`, exact parent HEAD `2ddc32a69dd32541497373ac76be2c1db332f88f`.

## Finding

The read-only authorization-packet file verifier classified regular files and symlink/reparse points through the live `stat.S_ISREG` and `stat.S_ISLNK` predicates. It also treated malformed `st_file_attributes` values as if no reparse attribute were present. A substituted predicate or malformed Windows metadata could therefore weaken path admission before the packet bytes were reviewed.

## Change

The isolated child pins the import-original `stat` module and both mode predicates, checks that policy before filesystem inspection and after metadata access, and uses only the captured predicates. Reparse metadata must be an exact integer; malformed values fail closed rather than being interpreted as zero.

Eight synthetic regressions cover module/predicate substitution, malformed metadata, the absent-platform default, and metadata callbacks that replace predicates. The verifier remains read-only and does not authorize execution or external compute.

## Boundaries

This is local in-process dependency-identity and metadata-shape hardening, not a sandbox, atomic directory-handle traversal, authenticated custody, approval, or action authority. No packet schema, frozen V3 Contract, compute gate, protected V2 evaluation, Candidate promotion, main merge, paid service, or UI work is changed.

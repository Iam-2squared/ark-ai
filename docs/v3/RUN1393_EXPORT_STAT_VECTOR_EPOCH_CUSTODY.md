# Run1393 — V3 export stat-policy vector epoch custody

## Exact basis

- Parent: Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent work-basis HEAD: `279232c359ec13355f684e1c8cfc081bda0a4a94`.
- Child branch: `research/run1393-v3-export-stat-vector-epoch-custody-20261125`.

## Finding

The non-executing export planner retained the imported `stat` module and its
three classifiers through mutable module aliases. The guard compared the live
module with `_ORIGINAL_STAT` and the live predicates with
`_ORIGINAL_STAT_S_ISDIR`, `_ORIGINAL_STAT_S_ISLNK` and
`_ORIGINAL_STAT_S_ISREG`. Replacing the working and purported-original
bindings together, including a forged aggregate, could make those comparisons
self-consistent.

## Correction

An import-time tuple now retains the complete stat module/predicate inventory.
The path-policy verifier captures that tuple in a keyword-only default and
checks the aggregate binding, the working module, every original alias and
each predicate before path inspection. Existing path semantics, metadata
checks, output separation and non-executing behavior are unchanged.

## Regression coverage

- Jointly replace the stat module, all three original predicate aliases and
  the aggregate epoch; denial must occur before `Path.lstat` or a replacement
  predicate.
- Repeat the replacement reentrantly from a synthetic `Path.lstat` callback;
  the post-callback policy check must deny before any replacement predicate.

Only synthetic temporary directories and monkeypatched metadata are used.

## Scope and limits

This is local in-process dependency-identity hardening. It is not a sandbox,
atomic dirfd traversal, protection against hostile concurrent filesystem
renames, authenticated filesystem identity or export authorization. No
converter, quantizer, model, GPU, training, Candidate/weight generation,
protected V2 evaluation, paid/external compute, credentials, hardware,
frozen-contract change, main merge or UI/frontend work occurred. PR #5 remains
Draft/unmerged; no V3 PASS is claimed.

# ARK AI Run741 — Detached diagnostic segment recovery and Windows SQLite lexical guard

Date: 2026-11-09 JST. Branch: `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8). This is reversible **FREE-ONLY NON-UI** groundwork, not ARK/JARVIS PASS, release, owner approval, trusted audit, live Windows verification, or OS access.

## Work basis and saved packages

The verified initial work-basis PR HEAD was `2a0aef2540a6eef78ded0ccb2cf165a7775531c6` (Run740 checkpoint, whose CI was initially queued). The two newly authored, independent, opt-in packages and their exact normal GitHub Contents API commits are:

1. **Public diagnostic segmented recovery review:** [source `3e80613`](https://github.com/Iam-2squared/ark-ai/commit/3e806138c6b78cbbd930812cb809bd9823df14e3), [tests `8db18e3`](https://github.com/Iam-2squared/ark-ai/commit/8db18e39e499901063270163fcbb060156852b2f), [test correction `e041078`](https://github.com/Iam-2squared/ark-ai/commit/e04107831bcb0f755d61ab57a44a6ebc346e4c16). An exact-type, bounded tuple of caller-retained segments is verified against global first sequence, total count, initial anchor and final tip. Every segment additionally receives the already existing independent public-only JSONL verifier. The coordinator prevalidates all segment metadata, checks no gaps, overlaps or dropped suffixes, limits to eight segments / 128 events / 50,000 characters in aggregate, and returns a deny-only receipt. Test cases include normal multi-part recovery, dropped/reordered/duplicated segments, tampered payload, type/count/anchor changes, malformed global witness, substituted callback, result authority and budget overrun. The constructed receipt is **not authenticated by a separate witness**.
2. **Portable Windows SQLite lexical-only review:** [source `3deee71`](https://github.com/Iam-2squared/ark-ai/commit/3deee7155c564861718e74141a2cb31d6d43a170), [tests `c931450`](https://github.com/Iam-2squared/ark-ai/commit/c931450796a6c840b7cf9957303981a1a13ce03b), [import correction `03d7fa1`](https://github.com/Iam-2squared/ark-ai/commit/03d7fa149929b86d3267bb2e9950ee58bc2a21b5). Deterministically hash **synthetic** ASCII canonical drive-absolute `.sqlite3` and `-wal`/`-shm`/`-journal` names; refuse UNC, `\\?\` device namespaces, rooted/drive-relative forms, mixed case, traversal, non-ASCII, path punctuation, NTFS alternate data stream separators, 8.3 tildes, Win32 DOS device names and oversized components. No `os.stat`, `Path` access, SQLite connection or real Windows SDK is used.

These are **separate disconnected workstreams**, not implicit integration into Memory V1, Planner, registry, authorization, or real executor. They do not modify frozen V1/V2/Local UI/Launcher contracts or PR #5/#9.

## Exact CI observations and repair

- Inherited [Run740 checkpoint CI #42636375532](https://github.com/Iam-2squared/ark-ai/actions/runs/42636375532): **6/6 Windows/Ubuntu Python 3.11–3.13 GREEN** as independently observed during Run741, on old HEAD `2a0aef2540a6eef78ded0ccb2cf165a7775531c6`; not proof of Run741 additions.
- New test-head [#42638723097](https://github.com/Iam-2squared/ark-ai/actions/runs/42638723097): all six jobs **FAIL at Ruff I001 import layout**. Newer test-head [#42639246142](https://github.com/Iam-2squared/ark-ai/actions/runs/42639246142): all six **FAIL at Ruff I001**, involving the two new test modules. This was observed from actual job logs; neither was a pytest failure or a passed feature gate.
- Import fixes applied through the normal Contents API. The diagnostic fixture's aggregate-budget test was independently checked: 49,000 characters plus the remaining canonical records were below the stated 50,000-character cap, so that test was corrected to 49,600. This changes only the synthetic fixture, not the safety budget.
- Latest source/test repair HEAD: `03d7fa149929b86d3267bb2e9950ee58bc2a21b5`. Its associated [CI #42639830793](https://github.com/Iam-2squared/ark-ai/actions/runs/42639830793) was **IN PROGRESS** when initially observed. **Do not claim six-platform GREEN** until exact-head run/jobs complete.

## Remaining correctness and threat boundaries

The segment envelope is supplied and retained by the caller; a party who can rewrite both the JSONL and every retained scalar can forge an internally consistent chain. It cannot establish sender identity, trusted date, anti-rollback or external audit custody. It is a local review artifact, not a grant to export private text or erase evidence. The aggregate limits do not bound attacker-side preprocessing before invocation; the inputs must be explicit exact primitives.

The Windows guard is exclusively **lexical**. Real Windows file safety requires an explicit reviewed design for volume/device/NTFS normalization, reparse points, hardlink count, root and per-component handle custody, ACLs and path replacement between preflight and `sqlite3.connect`, plus WAL/SHM transaction coherence. These issues cannot be resolved with a string hash; the review deliberately returns all authority/provenance/snapshot flags `False`. No real Windows path was touched or certified.

## Prioritized next work

1. Confirm exact **latest** source/test/checkpoint HEAD and its CI 6/6 on Windows/Ubuntu Python 3.11–3.13. If failures remain, inspect actual logs and make narrow semantics-preserving corrections; do not inherit a predecessor run's GREEN.
2. After CI proves the lower-level invariants, review segment coordination against reentrant mutation during callbacks, then add a final all-segment metadata epoch check before claiming a consistent detached result; keep no-authority semantics.
3. Advance Memory generation CAS/ABA, SQLite WAL/row/event coherent snapshots, expiry races and manual-only COMMIT-UNKNOWN reconciliation. Do not replay unknown writes automatically.
4. Advance Planner persisted exact READ input/recovery, terminal propagation and registry-bound exact-type PermissionGate; join occurrence/audit-before-action only against a disconnected/mock executor after independent CI gates.
5. Continue privacy-safe Personal Context and proactive/observation fixture contracts; perform a separate Windows held-handle design review without claiming that the lexical prefilter closes TOCTOU.

**Hard stops unchanged:** no paid/potentially billable services or compute, external GPU, Candidate training/adapter/weights or automatic promotion, new credentials/account connections, real actions/sensors, destructive operations, protected V2 evaluation, frozen-contract edits, main merge, or raw Git-object bypass. PR #5 remains Draft/unmerged; PR #9 remains Draft/unmerged and **all UI/frontend development remains paused**.

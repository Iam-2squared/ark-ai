# ARK AI Run840 — disconnected core ingress and SQLite last-close evidence

## Scope and boundaries

Zero-cost, local/disconnected, **no UI/frontend**, real ToolBackend execution, authorization, consent, Candidate compute, account/credential connections or protected evaluation. Only Draft PR #8 (`research/jarvis-foundations`) was changed. Frozen V1/V2/Local UI/Launcher and PR #5/#9 are untouched. All receipt hashes and synthetic fixture outcomes remain **non-authoritative**. Overall ARK/JARVIS remains **NOT_PASSED**.

### Package A — isolated mock Tool builtin integrity

- Source: [`03c265ce`](https://github.com/Iam-2squared/ark-ai/commit/03c265ce760565f171650a2d4057e5214337b9f4)
- Tests: [`e3c81704`](https://github.com/Iam-2squared/ark-ai/commit/e3c81704c305866747f3f37e43b6a5510903f9be) (3 authored cases)
- `_run` invokes unqualified `sum(values)`. Python checks module globals before builtins; guarding only `builtins.sum` was not sufficient to prevent an injected `disconnected_toolbox.sum` from receiving private synthetic values.
- The preflight now rejects a module-local `sum` override before JSON decoding or `_run`; exact unshadowed builtins remain available. Synthetic math/text/JSON semantics, no-external-dispatch denials unchanged.

### Package B — Planner input/epoch callback safety

- Source: [`8b74656d`](https://github.com/Iam-2squared/ark-ai/commit/8b74656d198f7ed3308251df3f13adfa6de7cb05)
- Tests: [`f5e21621`](https://github.com/Iam-2squared/ark-ai/commit/f5e216213001a781bbb5a71d10b76a4eb2509606) (8 authored cases, counting parameterized probes)
- A frozen `PlanStep` can be mutated by `object.__setattr__` after `PlanStep.__post_init__`. Graph admission previously used `step_id` as a dict key and `depends_on` as a set before confirming their exact primitive types, exposing `__hash__`/`__eq__` callbacks.
- Admission now checks exact step ID, dependency, ToolCall type and duplicate dependencies **before** hashing/sorting. Retained step/status epoch tuples are shape-checked before unpacking; status map keys and epoch IDs are type-checked before hash/equality access. CAS transition rules, terminal cascade, status digests and ordering remain unchanged.
- In-process protection only. This does not provide durable Planner journal recovery or external authority.

### Package C — offline PNG private digest preflight

- Source: [`60e24c6c`](https://github.com/Iam-2squared/ark-ai/commit/60e24c6c25cf2bd9aac849241b9da5bfe7291f44)
- Tests: [`0feb3e68`](https://github.com/Iam-2squared/ark-ai/commit/0feb3e684160db3e6b4fcf6e82bcbcc7e87b7685) (6 authored cases, including 4 parameterized invalid digests)
- `_sha` accepted any-length string for regex scanning and was a mutable module-global helper receiving owner/privacy/source digest labels. Before reading the caller-owned PNG request, the original helper identity is now checked; fixed-width length is checked before regex evaluation. No image capture, pixel decode or consent authority.

**Total: 17 authored regression cases.** Case creation is not evidence of 17 PASS. Rely on exact-head CI for that conclusion.

## Independent disposable SQLite WAL/SHM last-close experiment (read-only evidence)

Executed **only against ephemeral synthetic SQLite files in Linux container**, not the user's PC or actual Memory/ActionAudit database. Python 3.13.5, SQLite 3.46.1, Linux. No repository code execution and no claim that this reproduces the ARK failure.

1. Open one SQLite connection in WAL mode, create/insert one synthetic row, and retain a read-only file descriptor for the existing `database-shm` sidecar. While the connection is live, `fstat(fd).st_nlink == 1`.
2. Close the **last** SQLite connection: both `-wal` and `-shm` paths disappear. The retained descriptor remains valid but `fstat(fd).st_nlink == 0`.
3. Repeat with a separate **keeper connection**. Closing the original writer while the keeper stays open leaves `-shm` present and `st_nlink == 1`; only after closing the keeper does `-shm` disappear and the retained descriptor return `st_nlink == 0`.

**Two-process follow-up (same disposable Linux runtime):** a separate child process opened WAL, inserted one synthetic row, signaled the parent, and closed only after the parent retained an `-shm` descriptor. With **no parent keeper connection**, the child exited cleanly and the parent's descriptor changed `st_nlink: 1 → 0`. With a **parent keeper connection**, the child's clean exit left `st_nlink: 1 → 1`, and the subsequent keeper close changed it to `0`. Both child exit codes were `0`. This confirms the sidecar last-close mechanism across process boundaries on this Linux environment, but still does **not** establish the exact failing ARK production/Windows interleaving. No original user data or persistent file was touched.

This is a concrete mechanism by which a previously validated read-only sidecar handle can later have `nlink=0` **without an adversarial hard-link**. It is **not proof** that any particular ARK Windows or Linux CI failure had that cause. Existing production fail-closed no-follow/link-count/handle custody checks must **not** be loosened based on this diagnostic. Next investigate keeper ownership, close order, and read-epoch boundaries on disposable ARK-specific fixtures, with OS-specific CI evidence. No recovery replay or automatic retry.

## CI and evidence requirements

- Prior Run839 exact checkpoint `df8d35336437a9ce71ba4f0cb9c9fa5e0e23a1a4`: [CI #43382147635](https://github.com/Iam-2squared/ark-ai/actions/runs/43382147635) **GREEN 6/6** (checked at Run840 start).
- Run840 Tool source/test `e3c81704`: [CI #43388576663](https://github.com/Iam-2squared/ark-ai/actions/runs/43388576663) **IN PROGRESS** on last inspection.
- Run840 Planner tests `f5e21621`: [CI #43388726238](https://github.com/Iam-2squared/ark-ai/actions/runs/43388726238) **QUEUED** on last inspection.
- Run840 PNG tests `0feb3e68`: [CI #43388843468](https://github.com/Iam-2squared/ark-ai/actions/runs/43388843468) **QUEUED** on last inspection.
- None of the above intermediate run IDs attests future report/checkpoint HEAD. Confirm all six Windows/Ubuntu × Python 3.11–3.13 jobs on the exact final checkpoint commit, repair semantics-preserving failures via normal GitHub Contents API, and preserve test/report provenance.

## Next plan / 今後の方針

1. Confirm Run840 final HEAD's six CI jobs; resolve any actual failure without reducing admission, privacy or authorization denials.
2. On owned disposable DBs, compare `-shm` nlink and retained descriptor identity across SQLite last-close with/without keeper under Memory and ActionAudit readers/writers.
3. Advance Memory postcommit COMMIT-UNKNOWN manual triage, Planner durable UNKNOWN isolation and exact revisions, then immutable ToolRegistry → exact-type PermissionGate → audit-before-action → mock executor integration **only after** exact-head lower-layer GREEN.
4. Continue privacy lifecycle, restart-safe proactive occurrence and observation fixture paths; keep free-only V3 approval/identity gates, paused UI and protected evaluation boundaries unchanged.

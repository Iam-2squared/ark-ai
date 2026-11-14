# Run723 — CI Planner regression correction, Registry and Memory digest preaccess

**Scope:** FREE-ONLY, NON-UI, reversible JARVIS foundations on Draft PR #8
(`research/jarvis-foundations`). **Work basis:**
`4dad38ad9d278abba21fde3a85cd2ba3d0cbfe70` (Run722 checkpoint).
**No roadmap PASS or authorizing/live capability is claimed.**

## Package A — exact Run722 CI failure correction

[Run722 exact-head CI #42527701240](https://github.com/Iam-2squared/ark-ai/actions/runs/42527701240)
completed **FAIL in all six Ubuntu/Windows × 3.11–3.13 jobs**. Ubuntu 3.11:
**11,297 PASS / 2 FAIL / 1 SKIP**; Windows 3.11:
**11,236 PASS / 2 FAIL / 62 SKIP**. Both failures were the two parameters
of `test_named_file_metadata_change_after_read_is_rejected`. The injected
`Path.stat(..., follow_symlinks=False)` returned substituted metadata
**twice**, while the test demanded exactly one call. The production loader
correctly denied the changed named-file epoch. **No production check was
relaxed.** [Correction `9e3470f6`](https://github.com/Iam-2squared/ark-ai/commit/9e3470f68dc3e3c269cadafcaea772845a533c96)
retains the denial expectation and verifies at least one injected named-file
observation, without specifying the defensive probe count.

## Package B — registry identity digest protection

[Source `abee167c`](https://github.com/Iam-2squared/ark-ai/commit/abee167cbba4ee9685f2e77a074108c29e7712c5)
pins original `hashlib.sha256` and `json.dumps` in the optional
`ToolRegistry` identity path and rejects substitutions before constructor
input iteration, revision checks, direct resolution, canonical revision
encoding, or bound-action request reconstruction. The guards are repeated
at synthetic callback/reentry boundaries. **No backend invocation** is
added, and frozen contract code is unchanged.

[New regression tests `5ffdf49b`](https://github.com/Iam-2squared/ark-ai/commit/5ffdf49bda0ec1361caa2d7094d83675c6982e0f)
author **19 parameter-expanded cases**: twelve preinstalled dependency
substitutions across six registry entry points, two mid-generator mutations,
four mutations after registry lookup, and one unchanged deterministic bound
identity. The hostile callbacks record execution; tests require none.

## Package C — opt-in generation CAS digest protection

[Source `3671d909`](https://github.com/Iam-2squared/ark-ai/commit/3671d909d6b94b22611a7334b5f91707393a165d)
pins the original local SHA/JSON implementations plus both generation-CAS
domain-separation byte objects. The public read-only observation and opt-in
existing-row CAS update reject substituted dependencies before reading
private SQLite or computing content digests. Token, snapshot and digest
paths recheck authority at existing phase boundaries. Frozen Memory v1
schema and public put/delete APIs are not changed.

[New regression tests `71dc7142`](https://github.com/Iam-2squared/ark-ai/commit/71dc7142432b79c15274508378f93b1386433a2c)
author **17 parameter-expanded cases**: four dependency/domain mutations
across four generation-CAS ingress/review paths, plus one real **local
temporary SQLite** nonauthorizing observation fixture.

## Package D — disconnected startup digest guard

[Source `3860d956`](https://github.com/Iam-2squared/ark-ai/commit/3860d95655c7961ce1a67fc296affcbcf164d698)
pins original `hashlib.sha256`, `json.dumps` and the local readiness
digest domain before potentially private schema, plan or registry input
inspection. This check is repeated immediately before the two local
digest calculations. It does not query a user machine, execute a tool,
prove cross-store atomicity, or grant startup authority.

[New regression tests `324a6fa5`](https://github.com/Iam-2squared/ark-ai/commit/324a6fa5529652cd2b14fa1233fea112dc921609)
author **4 parameter-expanded cases**: three preinstalled dependency/domain
substitutions must reject before touching sentinel private inputs, and one
original-implementation smoke check. No external resource is used.

## Inherited cross-lane CI corrections after registry-source CI

[Registry-test CI #42531811016](https://github.com/Iam-2squared/ark-ai/actions/runs/42531811016)
reported **four FAIL on Ubuntu 3.11** (11,314 PASS, 1 SKIP)
and on the other observed Ubuntu versions. New 19 registry cases passed;
the failures were inherited late-phase callback expectations. The registry
now refuses a changed SHA before fixture startup or before a synthetic WRITE
is ever journaled. Updated expectations in four old test modules:

- [`3b1db8db`](https://github.com/Iam-2squared/ark-ai/commit/3b1db8dbdac83b3f2ce1c351549f79e3c20a0f56):
  startup must refuse before injected hash/constructor invocation, not
  demand a late report-authorization failure.
- [`62cf747e`](https://github.com/Iam-2squared/ark-ai/commit/62cf747ee8e904631b5fb1f689a7118a23d92a59):
  audit marker mutation is refused at registry before Planner RUNNING,
  occurrence reservation or pre-action audit; PENDING remains unchanged.
- [`2caa26a3`](https://github.com/Iam-2squared/ark-ai/commit/2caa26a312b936e1035e6c5e91e910987d77e2ad):
  synthetic mock receipt constructor mutation is likewise refused before
  any running state is recorded or backend accessed.
- [`f22a894f`](https://github.com/Iam-2squared/ark-ai/commit/f22a894f495d68aa85eef15c88b5110586d0e5d5):
  registry bound constructor test continues to demand constructor denial
  for preinstalled replacement; digest-reentrant parameter now requires
  earlier digest-dependency denial and zero hostile invocation.

These corrections **did not relax production protection**, did not execute
real tools, and are not evidence of a later six-job GREEN. The later Memory
source/test CI [#42532024733](https://github.com/Iam-2squared/ark-ai/actions/runs/42532024733)
showed the **same four inherited FAIL** on Ubuntu 3.11
(**11,331 PASS / 4 FAIL / 1 SKIP**), with no additional Memory test failure.
The corrections were saved only *after* those earlier per-commit runs.

## Evidence, limitations and concurrency

- **40 newly authored parameter-expanded synthetic cases**, three source modules
  changed, three new test files and one prior test corrected. The new cases
  were not executed in a local checked-out source tree; GitHub's per-commit
  automatic CI is the verifier, and the final checkpoint-result HEAD needs
  its *own* exact six-job GREEN evidence. No manually duplicated CI runs.
- Observed during this session: fix [#42531566117](https://github.com/Iam-2squared/ark-ai/actions/runs/42531566117)
  **IN PROGRESS**; registry test [#42531811016](https://github.com/Iam-2squared/ark-ai/actions/runs/42531811016)
  **IN PROGRESS**; Memory test [#42532024733](https://github.com/Iam-2squared/ark-ai/actions/runs/42532024733)
  **QUEUED** at observation. Startup [#42532406893](https://github.com/Iam-2squared/ark-ai/actions/runs/42532406893) was **QUEUED** at observation. These are separate per-commit CI runs and
  may change. No latest-head GREEN is inferred.
- `hashlib`/JSON callback identity checks are **process-local**, not a sandbox
  against an attacker with full Python process control. Neither local
  digests nor SQLite event high-water are independently authenticated
  provenance, consent, trusted time, proof of real READ or exactly-once
  external effects. No automatic retry is permitted for UNKNOWN commits.
- Main and frozen V1/V2/Local UI/Launcher artifacts are untouched. Protected
  PR #5 stays Draft/unmerged; paused UI PR #9 stays Draft/unmerged/untouched.
  No paid service, GPU/Candidate, protected evaluation opening, physical PC
  action, credentials, external tool dispatch, destructive operation or
  main merge.

## Next plan / 今後の方針

1. Confirm the exact final checkpoint-result HEAD Windows/Ubuntu six-job CI;
   inspect failure logs and correct only the actually failing semantics.
2. Memory: coherent retained row/event custody under WAL competition,
   CAS/ABA/expiry and manual COMMIT-UNKNOWN triage. Distinguish local markers
   from independent authenticated history.
3. Planner: durable independently retained READ input receipts, stepwise
   journal recovery, Windows publication limitations; no automatic replay
   or real backend READ inference.
4. Registry/permission/occurrence/audit: connect exact-type registry-bound
   authorization and audit-before-action to a **disconnected/mock-only**
   executor only after source and tests have exact-head GREEN.
5. Private context/scheduler/observation: revocation, restart and fixture-only
   provenance; free-only V3 guard checks without training/evaluation opening.

**Overall:** ARK/JARVIS/V3 **NOT_PASSED**.

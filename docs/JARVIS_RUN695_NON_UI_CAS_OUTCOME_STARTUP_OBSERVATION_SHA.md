# ARK AI — Run695: manual CAS outcome, startup lease identity and observation hash custody

**Scope:** Free-only, non-UI, isolated/reversible safety work on Draft PR #8
(`research/jarvis-foundations`). Initial work-basis HEAD:
`f446e53ee3b29a5797493888482d785aa4697741` (Run694 checkpoint).
Previous exact-head [CI #42413028007](https://github.com/Iam-2squared/ark-ai/actions/runs/42413028007)
was independently checked **6/6 GREEN** across Windows/Ubuntu × Python 3.11–3.13.
Do not extrapolate this result to Run695 HEADs.

## A. Memory generation CAS manual outcome ingress

The optional **read-only** `review_memory_generation_cas_outcome()` accepted
reflectively mutated proposals that its paired opt-in generation update would
refuse. It now rejects blank content, non-plain/oversize metadata carriers and
non-exact/out-of-SQLite-range expiry **before private SQLite observation**.
Valid finite expiry and normalized mapping-proxy metadata remain supported.
This does not change frozen Memory v1 schemas/put/delete, attribute a matching
post-COMMIT row to the attempting writer, or authorize automatic retry.

- Source: `src/ark/memory/generation_cas_outcome_review.py`, commit
  `d36975750c436fbf1a8caec6ec7c68052b363cdb`.
- Tests: `tests/test_memory_cas_outcome_reflected_expiry_run695.py`, commit
  `b32d983e87349a167ecda76240defb05ee5328cc`; **11 cases**
  including 10 invalid reflected proposals with a forbidden private-read hook,
  plus a valid manual-only finite-expiry review.

## B. Startup lease requirements use the same UTF-8 byte budget as probes

A synthetic requirement previously checked <=256 **code points**, while its
`StartupComponent` identity contract used <=256 UTF-8 **bytes**. The lease
now rejects non-UTF-8 and over-256-byte component/schema labels, including
reflectively substituted frozen inputs, before READY membership lookup.
Valid 256-byte ASCII/multilingual/emoji labels remain diagnostics only.

- Source: `src/ark/startup_readiness_lease_review.py`, commit
  `dd363a11933d4a5c00b652a44db9403e0436120d`.
- Tests: `tests/test_startup_lease_utf8_requirement_run695.py`, commit
  `4bc5149cdee0ab1474b7bdfd6e3e8359aa6b1e73`; **11 cases**
  across both requirement fields and byte/Unicode boundaries.
- READY, even with a matching digest, never permits startup, notifications
  or tool dispatch. The caller supplies synthetic clock/probe values.

## C. Observation adapter hashes private fixture bytes only with the original SHA-256

`fixture_text_observation()` and `fixture_binary_observation()` used the
mutable `hashlib.sha256` global on raw caller-supplied content. A replaced hash
callback could see the raw bytes **before** envelope construction guards ran.
The preflight now verifies the import-time module and SHA-256 function before
raw-content hashing; malformed metadata still receives its original specific
diagnostic before any content hash. No raw fixture bytes are persisted.

- Source: `src/ark/observation_fixture_adapters.py`, commit
  `2386fc5e6d80a17620ec90ec8636578f942ff8fe`.
- Tests: `tests/test_observation_fixture_hash_preaccess_run695.py`, commit
  `4bb76446e9e85567979f292294578bf5d0a7c2f2`; **4 cases** proving
  substituted function/module never receives private text or binary bytes.
- Legacy fault-injection diagnostics adjusted to require the new **earlier**
  rejection rather than late constructor rejection:
  `tests/test_observation_fixture_constructor_custody_run608.py`
  (`f7e94fd1a7093436f5f038ad702719894a2de8bc`),
  `tests/test_observation_fixture_initializer_custody_run620.py`
  (`ed9c7e1be89eb55bf4feb627d11a9b366bb2523f`).
  The original constructor substitution refusal is not weakened.

## Evidence and limitations

**26 newly authored parametrized cases**, three isolated production modules,
three new test modules, two pre-existing fault-injection test adjustments and
this technical report. The initial Run695 Memory source/test
[CI #42417657910](https://github.com/Iam-2squared/ark-ai/actions/runs/42417657910)
and Startup source/test
[CI #42417842016](https://github.com/Iam-2squared/ark-ai/actions/runs/42417842016)
were each **3/6 GREEN, Windows 3 IN PROGRESS, 0 FAIL** at last review.
Observation adjustment
[CI #42418127471](https://github.com/Iam-2squared/ark-ai/actions/runs/42418127471)
was **6 QUEUED**, not GREEN. Distinct source and report/checkpoint HEADs
also trigger their own CI; only exact-head observations count.

Everything remains **offline/synthetic**. No trusted clock, real source identity,
consent, protected evaluation, Candidate training, external side effect,
hardware use, charged compute or irrevocable authorization is established.
The V1/V2/Local UI/Launcher frozen contracts/evidence are unchanged.
PR #5 (V3) and PR #9 (UI paused) are untouched, Draft/unmerged.
PR #8 is still Draft/unmerged. **ARK/JARVIS/V3 NOT_PASSED**.

## Next plan / 今後の方針

1. Confirm exact-head six-job CI for the corrected Run695 source/tests; if
   any FAIL, inspect actual job logs, apply the narrowest semantics-preserving
   Contents-API correction, and develop another independent non-UI lane.
2. Memory: transaction-unknown outcomes, CAS/ABA/expiry/WAL coherent snapshots,
   privacy-use veto retention. A matching row must never be credited to a
   particular ambiguous writer or trigger an automatic WRITE retry.
3. Planner: durable independent per-step READ evidence, terminal/UNKNOWN crash
   recovery, registry identity and audit-before-action fixture joins; no live
   dispatcher until full consent and clock/authorization evidence exists.
4. Continue disconnected ToolRegistry/PermissionGate, occurrence replay guards,
   Personal Context, scheduler and observation back-end contracts, plus free V3
   identity/path/approval/reproducibility checks. Keep UI development paused.

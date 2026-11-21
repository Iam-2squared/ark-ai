# ARK AI — Run673: non-UI disconnected ingestion / CAS / Planner recovery

**Scope:** Free-only, no external compute or tools, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), unmerged. Initial exact work-basis HEAD `fde1f4821ea8cbc65871b0bd039e6ef61af88f65`. This evidence is a source-and-test audit record, **not a JARVIS, V3, physical-PC, human-consent or training PASS**.

## Package 1 — observation fixture metadata before private hashing

- Production source `src/ark/observation_fixture_adapters.py`, commit `a893544623e01b14e6036fc79a670754b446b3be`. Both fixture text and binary ingress now check the exact source/privacy label types, blankness, a 1024-UTF-8-byte budget (plus cheap character cap), strict Unicode validity, SQLite-range exact timestamp, and canonical optional parent SHA-256 **before hashing raw caller fixture content**. This is independently rechecked by the original `ObservationEnvelope` validator; existing type/kind/content checks and digest bytes are unchanged. No media is acquired or retained.
- Regression tests `tests/test_observation_fixture_metadata_preflight_run673.py`, commit `a3a3836115bdeb5c1f96e76bafb91a550c2eac45`: **22 authored parameterized cases** (20 bad-label/clock/parent combinations × text/binary, 2 valid UTF-8 1024-byte edge cases). Bad metadata tests install a forbidden digest hook and require failure without reaching it. Exact valid fixture content hashes and parent binding remain unchanged.
- Caveat: Input preflight does not authenticate the source, the person, media origin, consent, trusted time, any permission or a sandbox boundary. Hashing alone cannot authenticate a private observation.

## Package 2 — Memory manual CAS outcome ingress

- Production source `src/ark/memory/generation_cas_outcome_review.py`, commit `103c0c39c07b12625a59e1c5d699c0099631ebc3`. The **opt-in** read-only COMMIT-UNKNOWN reviewer now applies the same strict 512-byte UTF-8 generation source validation as generation-fenced CAS, and checks reflected exact content type, size and UTF-8 validity before computing a payload hash, materializing metadata or opening SQLite. A reflected invalid frozen `MemoryWrite` fails via `MemoryCASOutcomeRejected`, rather than escaping an unhandled encoding error.
- Regression tests `tests/test_memory_cas_outcome_preaccess_run673.py`, commit `1e25fb0384df7fd757a3b6147579006de35483a2`: **7 authored cases**, six invalid post-init source/content substitutions forbidden from reaching storage reads, plus one normal `UNCHANGED_OBSERVED` manual-only result with all authority denials false.
- Following a static test audit, commit `44e48ce4d047f5dde4f6ccc05e2e4989ed5d534d` scoped the forbidden SQLite hook inside a temporary monkeypatch context, so the subsequent read-only invariance assertions use the real store method. No source safety check was relaxed.
- Frozen Memory v1 schema, legacy put/delete/expiry contracts and existing valid CAS classifications are unchanged. A matching post-COMMIT row cannot attribute the writer or authorize retries, retention extension, real actions, or consent.

## Package 3 — Planner journal-to-fence bounded mock recovery

- Regressions `tests/test_planner_projection_budget_branch_run673.py`, commit `edfcd96fc75cc488b118935ad6a7528f0dc7dc24`: **7 authored cases** (1/24-step dependency chains × independent READ/WRITE root states, rejection of the 25th step, duplicate/untyped effect claims). Require deterministic dependency-first decisions, no journal changes on read-only projection and strict false dispatch, WRITE, replay and external-outcome authority.
- No Planner source or registry policies modified. SUCCEEDED without independently reviewed real per-step receipt remains **rejected**, not synthesized into a success hash.

## Package 4 — immutable ToolRegistry UTF-8 identity integrity

- Production source `src/ark/agency/registry.py`, commit `5233eba7bf5a08ae8c17fc367c758c22cde363a7`: name, capability and backend_id now require strict UTF-8 and **at most 256 actual UTF-8 bytes**, in addition to the prior cheap code-point cap. The pre-existing immutable registry, effect policies, bound-action revision schema and mock backend execution boundary are unchanged. This closes an ambiguous multibyte budget/Unicode-encoding path without modifying frozen V1/V2 APIs.
- Regression tests `tests/test_registry_utf8_identity_budget_run673.py`, commit `c56bd6d1aa41d894b69f456dd188d4a55b97778d`: **16 authored cases** (9 rejected multibyte/Unicode-surrogate registration identities, 6 exact-256-byte deterministic identity and bound-READ digest controls, and 1 invalid lookup test). No mock backend is executed; registration alone is not PermissionGate approval or permission to run.

## Evidence status and boundaries

- **Inherited work-basis CI:** [#42308612583](https://github.com/Iam-2squared/ark-ai/actions/runs/42308612583) **completed GREEN 6/6** (Ubuntu/Windows × Python 3.11–3.13), verified by individual job results before source changes.
- **New authored cases:** **52** across 4 test files. In-flight automatically triggered CI at report preparation: observation test HEAD [#42313749459](https://github.com/Iam-2squared/ark-ai/actions/runs/42313749459) sampled Ubuntu **3/3 GREEN**, Windows ongoing; Memory test HEAD [#42313912621](https://github.com/Iam-2squared/ark-ai/actions/runs/42313912621) ongoing; Planner test HEAD [#42314021891](https://github.com/Iam-2squared/ark-ai/actions/runs/42314021891) queued/in progress; repaired Memory test HEAD [#42314296591](https://github.com/Iam-2squared/ark-ai/actions/runs/42314296591) queued; Registry test HEAD [#42314492713](https://github.com/Iam-2squared/ark-ai/actions/runs/42314492713) queued. **These are not the eventual checkpoint HEAD and no new all-6 PASS is claimed.** Automatic workflow IDs on later report/checkpoint commits must be sampled after commit. No duplicate workflow dispatch.
- **Frozen/integration boundaries:** `main` at last verified `7a843f17eb96ed13d66f23b58b06406b3002e405` untouched; protected V2 evaluation, V3 Contract 1, Candidate/weights, HF identities, paid GPU, actual human approvals, real tools, account credentials, irreversible actions and main merge remain closed. Draft PR #5 unmerged; Draft PR #9 UI foundation at `3b49048dd70eebcb6268299b9ecef4e301bbc0fd` **untouched / UI development PAUSED**. Local UI/Launcher freezes preserved.

## Next plan / 今後の方針

1. Confirm exact-head all-six CI on both OSes. If red, inspect real logs and repair using only the normal GitHub Contents path, without weakening safety.
2. Continue independently retained Memory COMMIT-UNKNOWN event/row evidence, actor-attribution denial, SQLite WAL snapshot checks, CAS expiry/ABA.
3. Establish a read-only per-step Planner result receipt bridge with exact topology/ToolCall/registry bindings and durable custody. Hold SUCCEEDED/WRITE/UNKNOWN until separately proven; no real dispatch.
4. Then test immutable ToolRegistry, exact PermissionGate, durable occurrence, trusted-clock audit-before-action and disconnected mock executor after prerequisite exact-head GREEN. Keep protected UI, paid, final-eval and merge gates shut.

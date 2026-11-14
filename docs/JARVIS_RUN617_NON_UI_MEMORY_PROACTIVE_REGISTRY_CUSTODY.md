# ARK AI — Run617 non-UI Memory, Proactive, Registry and Privacy custody

Status: **research-only; Draft PR #8; no UI work; JARVIS NOT_PASSED.**

## Source and independent evidence

- Invocation work-basis HEAD: `51255c62d84264f2508067dfe66306fbf6afb2b5` (Run616 checkpoint).
- Run616 exact-head workflow [#41922454019](https://github.com/Iam-2squared/ark-ai/actions/runs/41922454019) independently observed **Ubuntu/Windows Python 3.11–3.13: 6/6 GREEN** before beginning new work.
- Repository read confirmed PR #5, #8, #9 open Draft; PR #9 UI branch, `main`, and all frozen V1/V2/Local UI/Launcher contracts and evidence are outside this run's write scope.
- Local container `git ls-remote` could not resolve github.com. The new tests are **authored, not claimed as locally executed PASS**. GitHub Actions is the independent execution source; GitHub Contents is the ordinary save path.

## Package A — Memory retained prefix witness and comparison constructor custody

Source commits `b3bcf174232cbf1ea5834d6b99fcbba46ac5efcc`, immediate indentation/style fix `c788b4ad2de60c596c3e1c473ca2ddb0253f5049`; test commit `fffb8d7eae3b58d17f376b4bf21305a62c3199d3`.

- Pin the exact import-original `MemoryEventPrefixWitness.__init__` and `MemoryEventPrefixComparison.__init__` alongside the existing False-only authority descriptors and class definitions.
- Recheck before witness instantiation after the SQLite prefix/event-hashing epoch; recheck comparison constructor after the domain-separated comparison digest callback before instantiation.
- Five new pytest cases cover preinstalled and callback-installed constructors for both output classes, assert injected constructors are never run, and preserve a normal advanced-prefix result without writer authentication, disclosure rights or action rights.
- Remains a read-only local SQLite observation. It does **not** verify independent witness custody, original writer, consent, erasure, safe retry or a live effect.

## Package B — Synthetic proactive input lookup custody

Source commit `d4accea1843cc8077450179489717766c9e25e49`; tests `049bca91c4d150c99a479403ef21716120b42ae4`.

- Pin import-original `__getattribute__` and `__getattr__` class-dictionary lookups for `AttentionBudgetPolicy` and `SyntheticSurfaceMarker`. Recheck in the existing `_assert_original_denials` at admission, input epochs and digest boundaries.
- Reject installed and reentrant input field-getter substitutions **before executing a malicious getter**, even if the substituted getter would return plausible policy values. Do not alter historical preview result instrumentation or authorization properties.
- Seven parameter-expanded tests: policy/marker × preinstalled/digest callback (4); both `__getattr__` fallbacks (2); valid window-budget non-authorizing control (1).
- No scheduler is started, notification is emitted, or clock/consent provenance is authenticated.

## Package C — Immutable ToolRegistry bound-result constructor custody

Source commit `deec7443798e9e13d022c9da9dad8d494a41861e`; tests `d57756b08c85543132e016705e0adb9a88d56a7e`.

- Bind the original `BoundAction` class and dataclass constructor, validate at `ToolRegistry.bind` entry, immediately before constructor dispatch after reentrant revision/request hashing, and before return.
- Four new tests require zero invocation of a malicious constructor (preinstalled, digest callback, replaced class), and preserve deterministic, registry-bound, non-dispatching normal binding.
- Existing post-constructor result/identity checks remain; no gate is granted, mock backend is called, or live WRITE is authorized.

## Package D — Durable local privacy veto receipt constructor safety

Source commit `6133480a3450be1492f0e2e1bc10bece2870d367`; test commit `090c3b8a4a326d003f87a9002f4767198b5091a5`.

- Pin the original `OfflinePrivacyVetoReceipt.__init__` alongside import-original class and denial descriptors. The pre-COMMIT authority check refuses an already-forged constructor before writing the denial marker.
- Recheck in the post-COMMIT receipt verifier: a reentrant commit callback that replaces the constructor now raises an explicit **post-COMMIT/manual-reconciliation** error without invoking injected constructor code or claiming rollback. The durable local veto remains in SQLite.
- Three new authored tests cover preinstalled refusal before write; simulated post-COMMIT constructor substitution with the veto surviving reopen; and a normal denial-only receipt. Two legacy preinstalled-constructor mutation cases were corrected in test-only commit `1671e4d1215879f339c22a02a027652c6afc1233`: they now require early denial with **zero constructor calls and zero persisted veto rows**. The new Run617 post-COMMIT callback test separately requires a durable denial marker and manual-only uncertain receipt outcome. Neither path allows automatic retry.
- A veto is one-way **denial** evidence, not consent/authentication/deletion proof. No live personal data or external action is handled.

**Scope compare:** `51255c62…1671e4d1` contains **12 commits, exactly 10 changed non-UI paths** (4 source modules, 4 new test files, 1 corrected existing test file, 1 technical report). **19 new parameter-expanded test cases authored (5 + 7 + 4 + 3), plus 2 existing test cases corrected; no local pytest PASS claim.**

## CI observed and acceptance limits

- Prior checkpoint: [#41922454019](https://github.com/Iam-2squared/ark-ai/actions/runs/41922454019): **6/6 GREEN**.
- Memory test HEAD [#41927486845](https://github.com/Iam-2squared/ark-ai/actions/runs/41927486845): Ubuntu 3/3 GREEN; Windows 3 IN PROGRESS at first read.
- Proactive test HEAD [#41927669911](https://github.com/Iam-2squared/ark-ai/actions/runs/41927669911): QUEUED at first read.
- Registry test HEAD [#41927986197](https://github.com/Iam-2squared/ark-ai/actions/runs/41927986197): QUEUED at first read.
- Privacy test HEAD [#41928707262](https://github.com/Iam-2squared/ark-ai/actions/runs/41928707262): QUEUED at first read, with two legacy preinstalled-constructor expectations predictably outdated. A subsequent ordinary Contents test-only correction `1671e4d1…` preserves original rejection-before-execution and requires the separate actual COMMIT callback test for ambiguous durability. Do not count the old head as passing.
- Later result HEADs and checkpoint HEAD **must not be called GREEN without direct six-job confirmation**. No duplicate equivalent workflow was manually dispatched.

## Independent V3 free-only blocker review

Read-only audit of Draft PR #5 `docs/v3/PRE_PAID_COMPUTE_GATE.md` and `docs/v3/HF_IDENTITY_REVIEW.md` at its previously recorded PR head `805b377697472268db02650a89c7a94b1c5337c8` confirms unresolved **immutable upstream revision/file byte hashes, materialized tokenizer identities, reviewed 120+30 data/provenance/contamination decisions, concrete local runtime/tool identities, proposed hardware and separate explicit preflight/full training authorizations**. These are genuine blockers; no execution identity was inferred or invented, no model, paid GPU or protected final evaluation was opened, and PR #5 was not modified.

## Frozen boundaries and next plan

PR #5 remains Draft/unmerged under V3 gates, PR #8 Draft/unmerged, PR #9 Draft/unmerged with UI **PAUSED**. No main merge, actual backend, paid compute, secrets, new account connections, physical PC, production notifications, Candidate generation/promotion, or protected V2 final evaluation. COMMIT-UNKNOWN and UNKNOWN WRITE remain manually triaged and not automatically retried. **ARK/JARVIS/V3 NOT_PASSED**.

**Next plan / 今後の方針:** (1) verify exact-head 6-job CI for each completed package, diagnose real failures and apply only smallest semantics-preserving Contents API fixes; (2) audit retained event/snapshot authority and coherent Memory CAS manual reconciliation, without retroactive author attribution; (3) continue Planner persistent restart recovery with PermissionGate/ToolRegistry identity and audit-before-*mock*-action only after lower-layer exact-head GREEN; (4) expand privacy-safe Personal Context and non-UI observation/proactive mock adapters, plus V3 passive-only identity guards; (5) preserve frozen evidence, zero-cost bounds and UI pause.

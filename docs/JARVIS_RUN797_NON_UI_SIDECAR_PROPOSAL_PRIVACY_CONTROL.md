# ARK Run797 — Local SQLite sidecar, synthetic proposal and private-context control integrity

**Scope:** free-only **NON-UI** work on Draft PR #8 (`research/jarvis-foundations`), initial work-basis HEAD `1d67981ae08c07fe52a3b08243e0ba2de59a0774`. Three independently scoped source+test packages, **29 parameterized cases submitted (13 + 8 + 8)**. Latest exact-head six-job CI is **NOT YET VERIFIED**. ARK/JARVIS **NOT_PASSED**.

## Package A — detached improvement proposal store SQLite sidecars

- `src/ark/agency/disconnected_proposal_store.py`: `b34b82ff130269dbd77e5c57db3d36a203f19b18`. `tests/test_disconnected_proposal_sidecars_run797.py`: `35ca0ac02301b3418af1c8abccc923e29eb1e699`; **13 cases**.
- Check `-wal`, `-shm`, and `-journal` using `lstat` *before* each SQLite access, and again through existing path inspection *after* the operation. Reject symlinks (including dangling), directories, nonregular files and sidecars with more than one hardlink; reject any preexisting sidecar when **creating** a store. Valid existing regular single-link sidecars remain permitted for SQLite WAL compatibility.
- This does **not** establish race-free OS pathname opening, sidecar ownership, encrypted storage, cleanup policy, external witness authentication or safe multi-process cooperation. No automatic retry after COMMIT-UNKNOWN; no destructive removal of sidecars.

## Package B — detached proposal identity carrier control

- `src/ark/agency/disconnected_improvement_proposal.py`: `e7bce11c4b145951ce56e2271546102c8c0a10bf`. `tests/test_disconnected_improvement_controlplane_run797.py`: `c10b27385e6dc6dbae5eeb84e0388d3b6665ad0d`; **8 cases**.
- Pin input/output/denial *field-name controls* and dataclass `__init__`/`__new__`/`__getattribute__`/`__getattr__` control descriptors in the pre-ingress protocol; detect unsafe substitutions before processing synthetic proposal references. Verify unchanged valid proposals remain content-free, deterministic and False-only for code/training/Candidate authority.
- No authenticated reviewer, genuine authorization, automatic self-edit, promotion or model training.

## Package C — personal-context offline preview privacy control

- `src/ark/personal_context_offline_preview.py`: `895baed08c4e70e811c0062581b5f55f477e6d5b`. `tests/test_personal_context_preview_names_run797.py`: `838e67accdb95b47698fceb31d862067577ec2d6`; **8 cases**.
- Pin the fixture, result, carrier-hook and False-only denial *name tuples* at module initialization. Reject substitutions before reading local private fixture content in both preview construction and retained-preview verification. After scoped tampering fixtures are restored, the valid local preview remains nonexportable/non-dispatchable and replay-verifiable.
- Explicit fixture owner/scope values are not authenticated; no live Memory connection, consent proof, external export or ToolBackend use was enabled.

## Verification and known limitations

- Pre-invocation baseline HEAD `1d67981ae08c07fe52a3b08243e0ba2de59a0774`, [CI 43063801165](https://github.com/Iam-2squared/ark-ai/actions/runs/43063801165): **all six jobs GREEN individually verified** (Ubuntu/Windows × 3.11/3.12/3.13). This certifies **Run796**, not the 29 new tests.
- Package A test HEAD `35ca0ac...`, [CI 43070479098](https://github.com/Iam-2squared/ark-ai/actions/runs/43070479098): **IN PROGRESS** at inspection.
- Package B test HEAD `c10b273...`, [CI 43070958584](https://github.com/Iam-2squared/ark-ai/actions/runs/43070958584): **IN PROGRESS** at inspection.
- Package C source HEAD `895baed...`, [CI 43071245667](https://github.com/Iam-2squared/ark-ai/actions/runs/43071245667): **QUEUED**; test HEAD `838e67a...`, [CI 43071346241](https://github.com/Iam-2squared/ark-ai/actions/runs/43071346241): **QUEUED** at inspection.
- **No local full integrated pytest/Ruff claim; latest exact-head all-six GREEN unverified.** No duplicate equivalent workflow run dispatched. The tests are submitted, not yet certified.

## Boundaries and next

Frozen V1/V2/Local UI/Launcher evidence, protected V2 evaluation, V3 Contract 1, contamination/reproducibility gates unchanged. PR #5 **Draft/unmerged**; PR #9 **Draft/unmerged and untouched**, UI PAUSED. No live model, paid/external GPU or service, new credential, real execution, Candidate generation, review attestation, training, promotion, uncertain WRITE retry, protected evaluation or main merge.

Next: verify exact-head six-job CI and repair real failures minimally; add independent cross-process sidecar/path race examination without claiming race freedom; continue Memory CAS/ABA/COMMIT-UNKNOWN and Planner durable UNKNOWN WRITE quarantine; only join PermissionGate/audit/mock execution once independently proven invariants hold. All new material is isolated and reversible.

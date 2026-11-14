# ARK Run455 — Detached PCM, binary, and wake-cue representation privacy

**Invocation work basis:** `ecb3c1dd5ccb6783066b0d268f659120483eed69` (Run454 checkpoint).
**Branch/PR:** `research/jarvis-foundations`, Draft PR #8 (not merged).
**Final source/test HEAD before this document:** `a50b53d525d717085b4efaf0aae52ddfac8ee523`.

## Confirmed, bounded defects and repairs

Implicit Python dataclass representation previously exposed content supplied to three
detached fixture carriers. This could leak bytes or private wake phrases when an
unrelated caller logs or formats a request object, including nested representations.

1. `src/ark/offline_pcm_activity.py`: `OfflinePcmActivityRequest.pcm_bytes`
   now uses `field(repr=False)`; GitHub blob
   `25c76bb1052c50229fe9b5284adfceac9b5d05c3`.
2. `src/ark/offline_binary_inventory.py`: `OfflineBinaryRequest.source_bytes`
   now uses `field(repr=False)`; GitHub blob
   `00929a7930592397baf739e0f8f0a09064297eec`.
3. `src/ark/offline_transcript_cues.py`: `OfflineWakeCue.phrase`
   now uses `field(repr=False)`; GitHub blob
   `fe0020baf0b7bddda46508bbe1a161e58f9ad0a3`.
   This also prevents the raw phrase from appearing through a nested
   `OfflineCueRequest.cues` implicit representation.

Only imports / dataclass representation flags changed. Exact-type validators,
algorithms, identity/digest semantics, positional dataclass constructors,
privacy scopes, limits, frozen contracts, and execution permissions remain unchanged.

## Tests and provenance

Added `tests/test_private_fixture_repr_run455.py` with **4 defined regression
tests**, GitHub blob `bc7633d952952e5ee7a961348b91883b810ca8eb`.
They cover PCM and binary object repr/str/nested containers, nested wake-phrase
redaction, preserved field access and working fixture calls, and explicit
`dataclasses.asdict` still containing sensitive values.

The newly created test source passed local Python 3.13.5 `py_compile` and AST
syntax/count inspection; it has 72 lines, max line width 94. Independent local
`git hash-object` matched the GitHub-saved test blob SHA exactly.
Three changed source paths were fetched, patched by single exact-line replacements,
and saved through the ordinary GitHub Contents API with distinct blob SHA results.
**The 4 test cases were NOT executed against the complete saved repository.**
Whole-repo pytest, Ruff, other Python versions, Windows/Linux, and exact-head
six-cell GitHub Actions GREEN are **NOT established**. Remote clone is blocked
by github.com DNS resolution from the local Python container; local Ruff missing.

Historical read-only CI inspection: at the start, **125 queued / 6 in progress**
GitHub Actions runs; latest Run454 checkpoint #1369,
`40342259814`, was QUEUED. Historical #1238 Ubuntu jobs had two failing
`test_privacy_cross_process_veto_projection_run434.py` success-count
assertions at their older HEAD. The assertion was revised in Run448, but
**the old failure does not confirm current-head recovery**. No manual re-run,
runner cancellation, paid runner, credential, or external compute was started.

## Safety / remaining blockers

`repr=False` is **only protection against incidental string formatting**:
it does NOT prevent explicit attribute access, `asdict`, serialization,
pickling, copying, third-party observability, crash dumps, or intentional logging.
No source authentication, trusted clock, actual consent, disclosure approval,
real ASR/microphone, real Tool dispatch, Candidate run, protected V2 evaluation,
or automatic replay authorization is implied. Sensitive bytes remain caller-owned.
Any real export/storage requires separate owner/scope/consent/revocation policy,
provenance and audit-before-action.

Frozen V1/V2/Local UI/Launcher evidence, Memory V1 Schema, ActionAudit V1,
V3 Contract 1, evaluation fixtures and integrity/reproducibility gates unchanged.
PR #5 stays Draft/unmerged; PR #8 remains Draft/unmerged. No main merge,
paid/external compute or irreversible operations.

## Next plan / 今後の方針

1. Observe exact latest source/test/document/checkpoint HEAD CI naturally; diagnose
   real failures, never infer all-six GREEN from source inspection alone.
2. Audit explicit serialization and diagnostic projection boundaries for PCM,
   binary and cue fixture carriers, separate from incidental representation.
3. Continue independent Memory CAS/event/expiry, Planner multi-WRITE recovery
   and issuer/trusted-clock/PermissionGate readiness; no effectful integration
   until lower-layer exact-head GREEN and explicit human gates are satisfied.

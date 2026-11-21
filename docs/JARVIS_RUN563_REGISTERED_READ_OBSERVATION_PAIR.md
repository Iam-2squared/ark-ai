# Run563 — Registry-bound READ report and disconnected media-pair review

## Scope and exact source

This pass changes only the unmerged, reversible JARVIS foundation branch. It does
not integrate into frozen V1/V2/Local UI/Launcher contracts, dispatch a backend,
open a camera or microphone, run ASR, infer consent, or authorize external effects.

### 1. Registered DAG READ receipt report custody

- Source commit [82f0189406](https://github.com/Iam-2squared/ark-ai/commit/82f0189406ce23ae045144d3cf0fd0742926dabb):
  `src/ark/agency/disconnected_registered_batch_receipt_review.py`.
- Test commit [5e69ea6d6](https://github.com/Iam-2squared/ark-ai/commit/5e69ea6d6ae1d348146296638a5ac12a6cefa295):
  six parameter-expanded cases in `tests/test_registered_batch_receipt_run523.py`.
- The five denied-authority property definitions are pinned at import time.
  Any replaced property is rejected *before* plan/registry/SQLite callbacks,
  even if the replacement happens to return `False`. Each subsequent
  callback epoch and denial getter rechecks original descriptors and exact
  output carriers. The test covers five initial replacements and one later
  replacement inside the first independently retained READ observation.
- The local SQLite journal and detached registry/call/receipt references
  remain independent, untrusted witnesses: this is **not** cross-store
  atomicity, evidence of execution, legitimate authorization, or permission
  to replay any operation.

### 2. Disconnected PNG + WAV metadata envelope

- Source commits [3d358b12](https://github.com/Iam-2squared/ark-ai/commit/3d358b1227d3b43e754fa3ed3275e7a7f068a064)
  and [072ffcab](https://github.com/Iam-2squared/ark-ai/commit/072ffcabdcf9e5e3f23160eed339c17b13afd47f):
  `src/ark/offline_observation_pair.py`.
- Test commit [8e68bb0c](https://github.com/Iam-2squared/ark-ai/commit/8e68bb0c8dd1eb23fcc74f142b4e04da15d478e2):
  16 parameter-expanded cases in
  `tests/test_offline_observation_pair_run563.py`.
- Caller-provided owner/privacy and source digests must match independently
  retained pins. Existing bounded PNG and WAV inspectors check the supplied
  in-memory fixture bytes. Two complete passive inspections must agree.
  The result is a canonical hash binding image dimensions/IDAT checksum and
  WAV frame/rate/PCM checksum without containing raw pixels or samples.
  Carrier mutation and non-original denied-authority getters are rejected.
- No file, device, network, real transcript, recognition model or audio/video
  stream is accessed. This is a **fixture metadata envelope**, not image
  understanding, acoustic interpretation, authenticated capture, matched
  real-world event timing, proof of user identity, or consent to retain/export.
  Caller-supplied retained hashes only detect historical substitution if they
  are truly retained independently by an authorized process.

## Verification boundary

Both changes were saved through the normal GitHub Contents API and are
covered by the existing six-job Ubuntu/Windows Python CI. Never transfer a
GREEN result from an earlier HEAD to a later commit; consult the exact
commit's completed workflow and job conclusions separately.

No new credentials, compute providers, potentially billable services,
hardware actions, Candidate weights, protected V2 evaluation, automatic
promotion, genuine ToolBackend calls or main merge are authorized by these
local contracts. All report authority properties remain denied.

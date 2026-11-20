# Run1003 — runtime-rendered tokenizer probe binding

**PR #5 child / Draft / UNAPPROVED / NOT_PASSED.** This is a free-only,
local-files-only identity guard. It does not authorize preflight, external
compute, Candidate generation, protected V2 evaluation, promotion or merge.

## Gap addressed

The prior identity path hashed a caller-supplied `chat-template-probe.txt`
and bound that digest into the execution snapshot. At runtime,
`_build_model_and_tokenizer` loaded an `AutoTokenizer` from the local
snapshot, but did not require that tokenizer's actual `apply_chat_template`
behavior reproduce the separately hashed probe bytes. A well-formed digest
could therefore describe a different rendered template than the tokenizer
used by training.

## Change

- Added `ark.learning.chat_template_probe`, a deterministic probe format
  containing the exact raw `tokenizer.chat_template` SHA-256 and two
  synthetic render cases: a user generation prompt and a completed
  user/assistant turn. Each rendered string has its own digest.
- Added
  `ark-v3-identity chat-template-probe --root <local-snapshot> --output <new-file>`.
  It imports `AutoTokenizer` only inside the command and uses
  `local_files_only=True` and `trust_remote_code=False`. It does not load
  model weights, import a GPU runtime, or contact a provider.
- The runtime now verifies the loaded tokenizer against the exact probe file
  before loading model weights. It repeats the check after the preflight
  example encoding and after full-run pretokenization, so a changed renderer
  cannot silently proceed to optimizer work.
- Probe reads are size-bounded and compare path/descriptor metadata before
  and after reading. This is best-effort local custody, not atomic
  dirfd-based protection against a hostile filesystem writer.

The existing snapshot field
`tokenizer.chat_template_probe_sha256` remains the SHA-256 of the probe
artifact. Frozen `docs/v3/CONTRACT.md` and the experiment template are not
changed. The new probe format adds runtime evidence to that existing field;
it does not invent an immutable Hub revision or authenticate any upstream
model/tokenizer bytes.

## Validation boundary

New tests use only a fake tokenizer, a tiny temporary probe file, and
monkeypatched local loader classes. They verify exact render reproduction,
template/render drift rejection, digest rejection before tokenizer callbacks,
create-only probe generation, and refusal before model-weight loading when
the runtime probe differs. No real tokenizer, model weights, CUDA device,
GPU kernel, external service, dataset, Candidate artifact or V2 suite is
used by these tests.

**CI status:** pending until the Draft child PR is opened. No local pytest
result is claimed.

## Frozen boundaries unchanged

- Contract 1 and the Experiment 001 template are unchanged.
- No external GPU/compute, paid API/service, subscription, purchase,
  model download or new account connection.
- No real preflight, training, adapter/weight generation or Candidate
  promotion.
- No protected V2 final-evaluation opening.
- PR #5 remains Draft/unmerged; this child remains isolated from main.

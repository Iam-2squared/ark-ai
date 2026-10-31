# V3 Run512 — Local identity bundle post-report byte custody

## Exact branch and code/test basis

- Repository `Iam-2squared/ark-ai`, Draft PR #5, `research/v3-learning-evaluation`.
- Initial basis HEAD: `20781a6c752a00a406b2543d621fe29062d1a982`; source-only HEAD `6293e57f9fca3853ee8f2106882d5c767f8f2cde`; final source/test HEAD `83807f62f8d94d7debd4911f81afccd8126decba`.
- Modified `src/ark/learning/identity_bundle_verify.py` exact blob `87df43b3466ab52b9c5f0b46cf896dbe4dd5f41c`.
- New `tests/v3/test_identity_bundle_final_file_epoch_run512.py` exact blob `faf2d3b9d38f25a7646036f6c7e7f334990b6e14`.
- Frozen `docs/v3/CONTRACT.md` blob `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`, unchanged. Main `7a843f17eb96ed13d66f23b58b06406b3002e405` unchanged; PR #5 remains Draft/unmerged.

## Fault model and new free-only validation

The existing local JSON bundle verification already inspects each independently pinned local component twice, checks its SHA-256, applies strict canonical JSON/path/byte limits and returns a denial-only local bundle witness. A reentrant witness constructor or a denial-property callback could rewrite an *earlier* component after the final prior check while preserving file size and restoring mtime; the report was then returned with now-stale file bytes. This package adds a **third bounded per-component verified read** after all bundle result-constructor and initial authority-property callbacks. Each late witness is checked against the exact originally captured bundle metadata; the report's own inert flags are rechecked. The new fixture suite has **5 authored cases including parametrization**: all components rechecked after report construction; same-length mtime-restored rewrite in constructor and denial getter; file deletion in constructor; final offline report check remains denial-only.

This detects ordinary late file rewrites after a witness was built, **not** adversarial concurrent filesystem swaps or malicious kernel writer, and not an atomic multi-file snapshot. Even repeated hash reads do not authenticate upstream Hugging Face provenance, immutable model/tokenizer files, local hardware or external reviewer/cost consent. No model loaded, dataset validation opened, GPU started, Candidate generated, files downloaded, or user authorization implied.

## Exact-head CI, chronology and blockers

- Prior PR #5 [41236023580](https://github.com/Iam-2squared/ark-ai/actions/runs/41236023580) at old `20781a6c752a00a406b2543d621fe29062d1a982`: **6/6 GREEN** (predecessor only).
- Run512 source-only CI [41241323246](https://github.com/Iam-2squared/ark-ai/actions/runs/41241323246), head `6293e57f9fca3853ee8f2106882d5c767f8f2cde`: initially IN PROGRESS.
- Run512 source+test CI [41241367944](https://github.com/Iam-2squared/ark-ai/actions/runs/41241367944), exact head `83807f62f8d94d7debd4911f81afccd8126decba`: **3 Ubuntu jobs GREEN, Windows three IN PROGRESS at evidence preparation**; six-job GREEN not yet asserted.
- Local standalone pytest/Ruff not executed; new cases are definitions, not independently attested passes. GitHub Contents API normal write route only. No raw Git objects/ref tricks.
- V3 remains **NOT_PASSED**, with independently verified immutable model/tokenizer/source bytes, human-reviewed 120/30 provenance and contamination decisions, runtime/GPU identities, preflight/real-training scope approval and user-approved cost ceiling unresolved. No paid/external compute, Candidate/weight/adapters, protected V2 final-evaluation opening, automatic promotion or main merge.

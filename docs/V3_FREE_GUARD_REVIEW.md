# ARK V3 Free Guard Review

Work basis for this review: PR #5 `d6d4c1954a85fc716b1c593ac55c85417912418f`.

Saved on the isolated JARVIS foundations branch only. This review does not modify the frozen V3 Contract, authorize external compute, generate a Candidate, open protected V2 evaluation, or promote/merge anything.

## Scope reviewed

The following PR #5 source was re-read at the exact review head:

- `src/ark/learning/preflight.py`;
- `src/ark/learning/execution.py`;
- `src/ark/learning/export_plan.py`;
- `src/ark/learning/identity.py`;
- `src/ark/learning/runtime_guard.py`;
- the pre-paid-compute gate and execution supplement.

The existing branch remains fail-closed on authorization state, immutable runtime/package identity, and the frozen experiment recipe. The gaps below are narrower cross-binding/path-safety issues that can be closed before any paid/external action.

## Preflight evidence cross-binding gap

`PreflightEvidence.validate()` validates each field independently, and `build_preflight_report()` separately validates the measured runtime identity. The report builder currently does not prove that several evidence fields describe that same frozen runtime/snapshot.

Before preflight evidence can authorize later full training, the report should additionally require:

1. `evidence.device == runtime_identity.device == snapshot.hardware.device`;
2. `evidence.vram_gib` to match the measured/frozen VRAM identity within the same explicitly bounded measurement tolerance;
3. `evidence.tokenizer_probe_sha256 == snapshot.tokenizer.chat_template_probe_sha256`;
4. `peak_vram_mib <= peak_reserved_vram_mib <= measured_capacity_mib`;
5. all three VRAM values to be finite positive non-bool numerics;
6. `evidence.wall_seconds <= snapshot.budget.wall_clock_timeout_minutes * 60`;
7. wall-time and capacity arithmetic to reject NaN, infinity, booleans, and negative/zero values.

Without these checks, individually well-formed evidence can still be internally inconsistent with the frozen execution snapshot.

### Required negative tests

At minimum:

- device mismatch;
- tokenizer-probe mismatch;
- evidence total-VRAM mismatch;
- allocated VRAM greater than reserved VRAM;
- reserved VRAM greater than measured capacity;
- wall time greater than the approved budget;
- bool/NaN/infinity at each numeric cross-binding boundary.

No GPU is required to test these guards; deterministic fixture evidence is sufficient.

## Export path canonicalization gap

`build_export_plan()` currently performs important byte-identity checks for the converter/quantizer and requires a new output directory, but path separation is primarily lexical.

Before any real export, canonical path guards should prove that:

- `base_dir`, `merged_candidate_dir`, converter, quantizer, Current model, and export output are resolved through a deterministic no-symlink policy;
- the output directory is not inside the source tree or either model source directory;
- the Candidate source is not the Current deployed model or an alias of it;
- none of the generated paired/Candidate output paths aliases the Current deployed model;
- symlinked output parents are rejected;
- canonical paths are pairwise separated before commands are constructed.

Raw `Path` equality is insufficient for aliases such as `..` normalization or symlinked parents.

### Required negative tests

At minimum:

- output directory under repository source;
- output directory under the frozen base directory;
- output directory under the merged Candidate directory;
- symlinked output parent;
- Current model reached through a lexical alias;
- merged Candidate source aliasing Current;
- base/Candidate canonical alias;
- generated output canonical aliasing Current.

These checks build plans only; they do not run conversion, quantization, model loading, or training.

## Authorization boundaries unchanged

This review intentionally does not resolve external identities or user-gated evidence. It does not fabricate:

- immutable HF revision/file hashes;
- reviewed 120/30 dataset decisions;
- approved GPU/provider/cost ceiling;
- llama.cpp converter/quantizer identities;
- preflight results;
- Candidate artifacts;
- historical V2 results;
- human promotion decisions.

The correct free next step is source/test hardening of the cross-bindings and canonical path guards. External compute remains blocked until its existing explicit authorization gate is satisfied.

# Run536 — Passive V3 readiness transition review (no training authority)

**Scope:** detached, reversible, free-only read/validation of two caller-supplied *unapproved* execution-snapshot dictionaries. No model load, network access, GPU, data creation, credential access, Candidate export, training step, evaluation opening, or billing path is invoked.

## Evidence and exact work basis

- PR #5 `research/v3-learning-evaluation` remained **Draft/unmerged**. This package started from HEAD `57579d4ea25070bb743365daf3c1f55951e35c21`.
- Source: `src/ark/learning/offline_readiness_transition.py`, introduced by commit `a831df69394b22555ab0b5b852c26500cf03a601`.
- Tests: `tests/v3/test_passive_readiness_transition_run536.py`, introduced by `72074067d573bde4e902fc1b92d69e2ac84117ac`, **17 authored pytest cases**, not a claim about independent local pytest.
- Exact source/test HEAD [Actions run 41338397659](https://github.com/Iam-2squared/ark-ai/actions/runs/41338397659): **6/6 GREEN** (Ubuntu and Windows, Python 3.11–3.13), directly read from individual job conclusions.
- Frozen V3 `docs/v3/CONTRACT.md` remains unchanged. Neither the training contract nor the protected V2 evaluation/scorer was opened or edited.

## What this module establishes

The new `review_passive_readiness_transition(before, after)` first invokes the existing exact-type, fail-closed passive snapshot-shape reviewer independently for *both* inputs. Every one of the five prior authorization fields must still be exactly `False`, and the authorizing properties on both resulting review objects must remain `False`. Canonical input JSON epochs are rechecked across callbacks, including a second full review after output-denial inspection. The result contains only snapshot hashes and sorted **field paths**; it never prints credential values, private dataset text, local file contents or paths.

It distinguishes four mutually meaningful path sets:

1. `newly_plausible_paths`: previously unresolved fields now have syntactically plausible shapes and are not malformed.
2. `became_unresolved_paths`: a previously nonplaceholder field is now marked unresolved.
3. `newly_malformed_paths`: a field newly fails its shape requirements, even if it merely departed from a placeholder.
4. `syntax_repaired_paths`: previously malformed fields now have syntactically plausible, nonplaceholder types.

`SAME_AS_BASE` tokenizer-revision dependencies are evaluated by the underlying shape review, so a base placeholder that becomes a 40-hex-looking identifier is correctly reflected in the tokenizer alias path as well. Domain-separated SHA-256 ties the report to the exact before/after snapshot hashes and four path sets.

## What it emphatically does NOT establish

- **No byte authenticity**: SHA-shaped fields may describe nonexistent, changed or unauthorized binaries, weights, tokenizer files, datasets or export tooling.
- **No provenance or review decision**: neither old nor new caller-provided mappings proves a human decision, contamination clearance, license clearance or verified dataset membership.
- **No GPU or billing authority**: all report properties `external_compute_authorized`, `preflight_authorized`, `real_training_authorized`, `candidate_generation_authorized`, `protected_v2_authorized`, `promotion_authorized`, `artifact_identity_verified`, and `human_approval_verified` remain hard `False`.
- **No execution readiness guarantee**: even empty unresolved and malformed path lists are merely a syntax diagnostic.
- **No immutable attestation of supplied dictionaries**: independent cryptographic custody and witness signatures are not present; the result cannot be treated as a signed artifact or a promotion basis.

## Next technical gates

Only when genuinely materialized local file bytes, immutable Hub revision, independently confirmed dataset/provenance/contamination decisions, runtime pins and explicit human approvals exist should separate, already-frozen authorization code be evaluated. All potential paid compute, real Candidate generation, final V2 opening, contract mutation and main merge remain blocked independently. In their absence, continue isolated non-executing local capability development.

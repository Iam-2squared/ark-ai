# Run535 — V3 passive authority and export identity guards (free-only)

## Basis and implementation

Work basis: `8ae990c6f23c196cacd884e6650aff2906509896`, Draft PR #5 `research/v3-learning-evaluation`. Changes are deliberately confined to the passive, unapproved snapshot inventory/review; no frozen experiment, evaluation scorer, training code, protected V2 gate, preflight permission, provider billing control, or Candidate bytes were changed.

- `src/ark/learning/offline_readiness_inventory.py` now refuses an authorization mapping containing additional keys, even when an unknown key is `False` or `None`. The five frozen authorization field names must match exactly and each literal value must be `False`. The execution validator already required exact field names; passive inventory no longer gives a misleading diagnostic on a schema-expanded authorization object.
- `src/ark/learning/offline_snapshot_shape_review.py` classifies `export.converter_identity` and `export.quantizer_identity` under strict lowercase 64-hex syntax, matching the existing production execution validator's SHA-256 *shape* requirement. Literal placeholders remain unresolved, not invalid.
- `tests/v3/test_unapproved_authority_and_export_shapes_run535.py` adds 13 parametrized/direct pytest cases for unknown permission fields, malformed export identity syntax, structurally plausible fake hashes, and unresolved placeholders.

These are diagnostic strings only. A SHA-looking value does not prove files, executable identity, upstream source, reviewed training data, licensing, the runtime/device, user consent, human signoff, or a billing ceiling. No network, model loading, GPU, Candidate, protected V2, auto-promotion, or paid service is invoked.

## Evidence and authorization boundaries

Initial exact-head source+test GitHub CI on `7ef42490a700e05c9f62195191d4d8ba7ec0381c`: [run 41333222818](https://github.com/Iam-2squared/ark-ai/actions/runs/41333222818), **completed GREEN** (six-job matrix to be cited separately if examined). This is *not* independent local pytest execution. This note creates a newer branch HEAD which requires a separate CI result; earlier green cannot certify subsequent contents.

**Still blocked:** external or potentially billable compute without explicit authorization and a provider-side spending ceiling, any real Candidate/weights generation, opening frozen V2 final evaluation, candidate promotion, main merge, unknown asset identity, licensing/provenance or human review. PR #5 remains Draft/unmerged.

## Next

Continue read-only, independently pinned real-file *inspection* only where lawful, free and supplied; distinguish lexical syntactic checks from real byte/root provenance and signed review. Never infer authorization from a clean passive report.

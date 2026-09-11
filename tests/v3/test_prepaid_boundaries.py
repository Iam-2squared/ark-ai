import json
from pathlib import Path

import pytest

from ark.learning.execution import ExecutionBlocked
from ark.learning.lineage import ArtifactIdentity, CandidateLineage, hash_file
from ark.learning.preflight import DisabledRealPreflightBackend, run_authorized_preflight

TEMPLATE = Path("docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json")


def test_real_preflight_cannot_run_from_template():
    snapshot = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    with pytest.raises(ExecutionBlocked):
        run_authorized_preflight(snapshot, DisabledRealPreflightBackend())


def artifact(kind, tool="rev-a"):
    return ArtifactIdentity(kind, f"/{kind}", "a" * 64, 1, tool)


def test_artifact_identity_requires_exact_integer_byte_size():
    for invalid_size in (True, 1.5, 0, -1):
        with pytest.raises(ValueError, match="byte size"):
            ArtifactIdentity("kind", "/artifact", "a" * 64, invalid_size, "rev-a").validate()


def test_lineage_hash_rejects_non_file(tmp_path):
    with pytest.raises(ValueError, match="non-symlink file"):
        hash_file(tmp_path)
    with pytest.raises(ValueError, match="non-symlink file"):
        hash_file(tmp_path / "missing.bin")


def test_candidate_lineage_requires_paired_quantizer_revision():
    lineage = CandidateLineage(
        base=artifact("base"),
        adapter=artifact("adapter"),
        merged_hf=artifact("merged"),
        gguf_f32=artifact("f32"),
        gguf_q4km=artifact("candidate-q4", "quant-a"),
        paired_base_q4km=artifact("paired-q4", "quant-b"),
    )
    with pytest.raises(ValueError, match="quantizer revision mismatch"):
        lineage.validate()


def test_candidate_lineage_is_hashable_when_matched():
    lineage = CandidateLineage(
        base=artifact("base"),
        adapter=artifact("adapter"),
        merged_hf=artifact("merged"),
        gguf_f32=artifact("f32"),
        gguf_q4km=artifact("candidate-q4", "quant-a"),
        paired_base_q4km=artifact("paired-q4", "quant-a"),
    )
    assert len(lineage.sha256) == 64

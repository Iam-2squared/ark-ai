"""Backend contracts and a non-model mock receipt; real training is hard-stopped."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from .dataset import (
    ContaminationGuard,
    DatasetArtifact,
    LearningCandidate,
    build_dataset,
    canonical,
    digest,
    valid_sha,
)


class StopRequired(RuntimeError):
    pass


@dataclass(frozen=True)
class TrainingConfig:
    base_model: str
    base_sha256: str
    dataset_sha256: str
    code_sha: str
    dependencies: str
    hardware: str
    seed: int = 42
    method: str = "mock"
    epochs: int = 1
    learning_rate: float = 0.0001
    schema_version: int = 1

    def validate(self) -> None:
        import math
        import re

        if self.schema_version != 1 or not all(
            valid_sha(value) for value in (self.base_sha256, self.dataset_sha256)
        ):
            raise ValueError("invalid provenance hashes/version")
        if not re.fullmatch(r"[0-9a-f]{40}", self.code_sha):
            raise ValueError("code commit SHA required")
        if not all(
            isinstance(x, str) and x.strip()
            for x in (self.base_model, self.dependencies, self.hardware)
        ):
            raise ValueError("base/dependency/hardware provenance required")
        if type(self.seed) is not int or type(self.epochs) is not int or self.epochs <= 0:
            raise ValueError("invalid seed/epochs")
        if not math.isfinite(self.learning_rate) or self.learning_rate <= 0:
            raise ValueError("invalid learning rate")

    @property
    def sha256(self) -> str:
        self.validate()
        return digest(canonical(asdict(self)))


@dataclass(frozen=True)
class TrainingArtifact:
    path: str
    sha256: str
    size: int
    kind: str


@dataclass(frozen=True)
class TrainingRun:
    config_sha256: str
    dataset_sha256: str
    artifact: TrainingArtifact
    measurement_kind: str
    metrics: dict


class TrainingBackend(Protocol):
    def train(
        self, dataset: DatasetArtifact, config: TrainingConfig, output: Path
    ) -> TrainingRun: ...


class RealTrainingBackend:
    def train(self, dataset: DatasetArtifact, config: TrainingConfig, output: Path) -> TrainingRun:
        raise StopRequired(
            "STOP before real training/weights: reviewed execution precommit required"
        )


class MockTrainingBackend:
    def train(self, dataset: DatasetArtifact, config: TrainingConfig, output: Path) -> TrainingRun:
        config.validate()
        if config.method != "mock":
            raise StopRequired("mock backend cannot train a real method")
        if digest(dataset.payload) != dataset.sha256 or dataset.sha256 != config.dataset_sha256:
            raise ValueError("dataset hash mismatch")
        rows = json.loads(dataset.payload)["examples"]
        rebuilt = build_dataset(
            [LearningCandidate(**row) for row in rows], ContaminationGuard.frozen_v2()
        )
        if rebuilt.payload != dataset.payload:
            raise ValueError("dataset validation/contamination rejected examples")
        if not rows or {row["split"] for row in rows} != {"train", "validation"}:
            raise ValueError("both nonempty dataset splits required")
        # No model is loaded, no artifact is misrepresented as weights.
        receipt = canonical(
            {
                "kind": "MOCK_RECEIPT_NOT_MODEL",
                "config": asdict(config),
                "dataset_sha256": dataset.sha256,
                "model_metrics": None,
            }
        )
        output = Path(output)
        if output.exists() or output.is_symlink() or not output.parent.is_dir():
            raise ValueError("output must be a new explicit run directory under an existing parent")
        if any(parent.is_symlink() for parent in (output.parent, *output.parents)):
            raise ValueError("symlink output parents are not allowed")
        output.mkdir()  # exclusive directory creation; no overwrites
        path = output / "mock-receipt.json"
        with path.open("xb") as handle:
            handle.write(receipt)
        artifact = TrainingArtifact(str(path), digest(receipt), len(receipt), "mock_receipt")
        return TrainingRun(
            config.sha256,
            dataset.sha256,
            artifact,
            "mock",
            {
                key: None
                for key in (
                    "trainable_parameters",
                    "steps",
                    "wall_seconds",
                    "peak_ram_mib",
                    "peak_vram_mib",
                    "loss",
                    "start",
                    "end",
                )
            },
        )

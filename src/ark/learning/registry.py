"""Append-only candidate snapshots, never a current-model writer."""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path

from .dataset import canonical, digest
from .training import StopRequired, TrainingConfig, TrainingRun

TRANSITIONS = {
    "CREATED": {"TRAINING", "REJECTED", "ARCHIVED"},
    "TRAINING": {"TRAINED", "REJECTED"},
    "TRAINED": {"EVALUATING", "REJECTED", "ARCHIVED"},
    "EVALUATING": {"REJECTED", "ARCHIVED"},
    "REJECTED": {"ARCHIVED"},
    "ARCHIVED": set(),
}


class CandidateRegistry:
    def __init__(self, root: Path):
        self.root = Path(root)
        if not self.root.is_dir() or self.root.is_symlink():
            raise ValueError("registry root must be an explicit existing nonsymlink directory")
        if any(parent.is_symlink() for parent in self.root.parents):
            raise ValueError("symlink registry ancestor")

    def _directory(self, candidate_id: str) -> Path:
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}", candidate_id):
            raise ValueError("invalid candidate ID")
        path = self.root / candidate_id
        if path.is_symlink():
            raise ValueError("symlink candidate directory")
        return path

    def create(self, candidate_id: str, config: TrainingConfig) -> dict:
        config.validate()
        directory = self._directory(candidate_id)
        directory.mkdir()
        record = {
            "schema_version": 1,
            "sequence": 0,
            "candidate_model_id": candidate_id,
            "status": "CREATED",
            "training_config": asdict(config),
            "config_sha256": config.sha256,
            "previous_sha256": None,
            "automatic_promotion": False,
            "artifact": None,
        }
        self._write(directory, record)
        return record

    def _write(self, directory: Path, record: dict) -> None:
        with (directory / f"{record['sequence']:06d}.json").open("xb") as handle:
            handle.write(canonical(record))

    def latest(self, candidate_id: str) -> dict:
        paths = sorted(self._directory(candidate_id).glob("*.json"))
        previous = None
        for index, path in enumerate(paths):
            if path.is_symlink() or path.name != f"{index:06d}.json":
                raise ValueError("invalid registry sequence")
            data = path.read_bytes()
            record = json.loads(data)
            if (
                record["candidate_model_id"] != candidate_id
                or record["automatic_promotion"] is not False
                or record["status"] not in TRANSITIONS
                or record["config_sha256"] != TrainingConfig(**record["training_config"]).sha256
            ):
                raise ValueError("invalid candidate snapshot")
            if record["sequence"] != index or record["previous_sha256"] != previous:
                raise ValueError("registry chain integrity failure")
            previous = digest(data)
        if not paths:
            raise ValueError("candidate not found")
        return record

    def transition(
        self, candidate_id: str, status: str, *, run: TrainingRun | None = None, reason: str = ""
    ) -> dict:
        if status == "PROMOTION_ELIGIBLE":
            raise StopRequired("STOP before real promotion decision; human-reviewed gate required")
        prior = self.latest(candidate_id)
        if status not in TRANSITIONS.get(prior["status"], set()):
            raise ValueError("illegal candidate state transition")
        artifact = prior["artifact"]
        if status == "TRAINED":
            if run is None or run.config_sha256 != prior["config_sha256"]:
                raise ValueError("training run/config provenance mismatch")
            if run.measurement_kind != "mock" or run.artifact.kind != "mock_receipt":
                raise StopRequired("real training artifact acceptance requires reviewed execution")
            if run.dataset_sha256 != prior["training_config"]["dataset_sha256"]:
                raise ValueError("training dataset mismatch")
            path = Path(run.artifact.path)
            if path.is_symlink() or digest(path.read_bytes()) != run.artifact.sha256:
                raise ValueError("artifact hash mismatch")
            if path.stat().st_size != run.artifact.size:
                raise ValueError("artifact size mismatch")
            artifact = asdict(run.artifact)
        if status == "REJECTED" and not reason.strip():
            raise ValueError("rejection reason required")
        record = {
            **prior,
            "sequence": prior["sequence"] + 1,
            "status": status,
            "artifact": artifact,
            "reason": reason,
            "previous_sha256": digest(canonical(prior)),
        }
        if run is not None:
            record["training_run"] = asdict(run)
        self._write(self._directory(candidate_id), record)
        return record

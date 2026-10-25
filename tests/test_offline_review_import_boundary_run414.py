"""Guard direct paid/network/hardware dependencies in synthetic-only review code.

This AST gate is deliberately narrow: it catches direct imports, not dynamic
imports, transitive dependencies, provenance or authenticated authorization.
It is not a sandbox and cannot by itself certify zero-cost execution.
"""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "src" / "ark"
REVIEW_MODULES = (
    "agency/synthetic_approval_claim_review.py",
    "agency/synthetic_clock_sequence_review.py",
    "agency/synthetic_mock_action_cycle_review.py",
    "agency/synthetic_occurrence_audit_link_review.py",
    "agency/synthetic_recovery_triage.py",
    "agency/synthetic_write_plan_recovery_review.py",
    "memory/synthetic_multiscope_integrity_review.py",
    "personal_context_revocation_review.py",
    "proactive_synthetic_freshness_review.py",
    "startup_readiness_review.py",
)
# Review modules should be local-only and must not directly acquire external
# GPU/LLM/network/hardware entry points. Free-only local fixture work is fine.
BANNED_ROOTS = frozenset((
    "openai", "anthropic", "httpx", "requests", "urllib", "socket",
    "subprocess", "boto3", "torch", "transformers",
    "huggingface_hub", "peft", "accelerate", "cv2", "pyaudio",
    "sounddevice", "mss", "pyautogui",
))


def _direct_imports(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module is not None:
                yield node.module


@pytest.mark.parametrize("relative", REVIEW_MODULES)
def test_disconnected_review_modules_have_no_direct_external_compute_imports(relative):
    path = ROOT / relative
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    invalid = {
        name for name in _direct_imports(tree)
        if name.split(".", 1)[0] in BANNED_ROOTS
    }
    assert not invalid, f"{relative} imports prohibited external interfaces: {sorted(invalid)}"


def test_import_guard_targets_exist_and_are_not_entirely_empty():
    assert all((ROOT / name).is_file() for name in REVIEW_MODULES)
    assert len(REVIEW_MODULES) >= 8

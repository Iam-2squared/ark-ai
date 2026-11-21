"""Expiry-restart verification never calls substituted module attribute hooks.

These denial-only probes have no real Memory records or purge authority.
"""

from __future__ import annotations

import pytest

from ark.memory import expiry_restart_receipt_review as restart


class HostileModule:
    def __init__(self) -> None:
        object.__setattr__(self, "reads", 0)

    def __getattribute__(self, key: str) -> object:
        if key == "reads":
            return object.__getattribute__(self, key)
        object.__setattr__(self, "reads", self.reads + 1)
        raise AssertionError("substituted module getter must never execute")


@pytest.mark.parametrize("module_name", ("hashlib", "json", "cohort_module"))
def test_rebound_module_is_rejected_before_access(
    monkeypatch: pytest.MonkeyPatch, module_name: str,
) -> None:
    impostor = HostileModule()
    with monkeypatch.context() as patch:
        patch.setattr(restart, module_name, impostor)
        with pytest.raises(
            restart.MemoryExpiryRestartRejected, match="protocol changed",
        ):
            restart.review_memory_expiry_restart_receipt(
                independently_expected_scope_hashes=(),
                prior_pages=(),
                observed_pages=(),
                retained_prior=None,
                prior_asserted_now_ms=100,
                observed_asserted_now_ms=101,
            )
    assert impostor.reads == 0

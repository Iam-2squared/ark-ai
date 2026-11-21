"""Review callbacks must remain the original import-time functions.

A substituted binder/preflight is executable and could inspect private
registry/call/witness data before the SQLite snapshot is validated.
"""

from __future__ import annotations

import pytest

import ark.agency.disconnected_atomic_binding_snapshot_review as binding


@pytest.mark.parametrize(
    "callback",
    ("derive_registered_atomic_intent", "review_atomic_input_carriers"),
)
def test_substituted_atomic_interpretation_refused_before_private_input(
    callback: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoked: list[bool] = []

    def forbidden(*_args: object, **_kwargs: object) -> object:
        invoked.append(True)
        raise AssertionError("untrusted atomic callback executed")

    monkeypatch.setattr(binding, callback, forbidden)
    with pytest.raises(
        binding.AtomicBindingSnapshotRejected,
        match="reader definition changed",
    ):
        binding.review_registered_atomic_binding_snapshot(
            None, None, None, None, occurrence_id="synthetic-invalid",
        )
    assert not invoked

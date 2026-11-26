"""Reflected startup dependency carriers must not execute a foreign __len__.

These are disconnected readiness diagnostics, not backend dispatch authority.
"""

from __future__ import annotations

import pytest

from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    evaluate_startup_readiness,
)


class _LenTrap:
    def __len__(self) -> int:
        pytest.fail("untrusted dependency length callback was invoked")


class _TupleLenTrap(tuple):
    def __len__(self) -> int:
        pytest.fail("untrusted tuple subclass length callback was invoked")


@pytest.mark.parametrize(
    "replacement",
    ([], {}, _LenTrap(), _TupleLenTrap(("core",))),
)
def test_reflected_non_tuple_denied_before_len_hook(replacement: object) -> None:
    component = StartupComponent("consumer", ("core",))
    object.__setattr__(component, "dependencies", replacement)
    with pytest.raises(TypeError, match="dependencies must be an exact tuple"):
        evaluate_startup_readiness((component,))


def test_reflected_oversized_exact_tuple_denied_before_graph_allocation() -> None:
    component = StartupComponent("consumer", ("core",))
    object.__setattr__(component, "dependencies", ("core",) * 4097)
    with pytest.raises(ValueError, match="per-component dependency budget"):
        evaluate_startup_readiness((component,))


def test_valid_detached_dependency_graph_still_ready() -> None:
    snapshot = evaluate_startup_readiness((
        StartupComponent("consumer", ("core",)),
        StartupComponent("core"),
    ))
    assert snapshot.state("consumer") is ReadinessState.READY
    assert snapshot.root_blockers("consumer") == ()

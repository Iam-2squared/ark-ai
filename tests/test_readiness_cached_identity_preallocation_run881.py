"""Cached readiness identity bounds precede sorting and digest work."""
import pytest

from ark import startup_readiness_review as readiness


@pytest.mark.parametrize(
    "field", ["component_id", "dependencies", "failure_code", "schema_revision"],
)
def test_reflected_cached_identity_rejected_before_sort(
    monkeypatch: pytest.MonkeyPatch, field: str,
) -> None:
    snapshot = readiness.evaluate_startup_readiness(
        (readiness.StartupComponent("root"),)
    )
    item = snapshot.components[0]
    # A frozen cached value is not safe against object.__setattr__.
    if field == "dependencies":
        object.__setattr__(item, field, ("bad" * 90,))
    else:
        object.__setattr__(item, field, "bad" * 90)

    def prohibited_sort(*args: object, **kwargs: object) -> None:
        raise AssertionError("unbounded cached identity reached sorting")

    # Use only this module's lookup for the synthetic trap. A compliant
    # preflight rejects before attempting sorted(...) on reflected data.
    monkeypatch.setattr(readiness, "sorted", prohibited_sort, raising=False)
    with pytest.raises(ValueError, match="startup snapshot identifier changed"):
        snapshot._assert_integrity()


@pytest.mark.parametrize("label", ["component_id", "failure_code", "schema_revision"])
def test_readiness_constructor_rejects_oversized_whitespace_identity(
    label: str,
) -> None:
    args: dict[str, object] = {"component_id": "root"}
    args[label] = " " * 257
    with pytest.raises(ValueError, match="bounded exact text"):
        readiness.StartupComponent(**args)

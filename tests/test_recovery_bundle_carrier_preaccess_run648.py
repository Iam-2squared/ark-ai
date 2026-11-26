"""Detached recovery bundle checks must not execute patched result slots.

All fixtures are offline and inert. A digest cannot prove external action,
consent, trusted time, or authorization to replay a previously reserved WRITE.
"""

import pytest
from test_synthetic_plan_bundle_cross_process_run434 import _fixture, _review

import ark.agency.synthetic_plan_recovery_bundle_review as bundles


@pytest.mark.parametrize(
    "name",
    bundles._BUNDLE_FIELDS
    + bundles._BUNDLE_DENIALS
    + ("__getattribute__", "__getattr__", "__init__"),
)
def test_preinstalled_bundle_code_cannot_read_retained_bytes(
    monkeypatch, name,
):
    data = b"{}"
    report = bundles.SyntheticWritePlanBundle(data, bundles._digest(data))
    calls = []

    def forbidden(*_args, **_kwargs):
        calls.append(name)
        raise AssertionError("executable bundle carrier ran")

    with monkeypatch.context() as patch:
        patch.setattr(bundles.SyntheticWritePlanBundle, name, forbidden, raising=False)
        with pytest.raises(
            bundles.SyntheticWritePlanBundleRejected,
            match="synthetic bundle carrier or denial changed",
        ):
            bundles.restore_synthetic_write_plan_bundle(report)

    assert calls == []


def test_digest_callback_cannot_patch_bundle_slot_before_decode(
    monkeypatch,
):
    data = b"{}"
    report = bundles.SyntheticWritePlanBundle(data, bundles._digest(data))
    calls = []
    native = bundles._digest

    def forbidden(*_args, **_kwargs):
        calls.append("slot")
        raise AssertionError("patched slot executed")

    with monkeypatch.context() as patch:
        def poison(value):
            digest = native(value)
            patch.setattr(bundles.SyntheticWritePlanBundle, "digest", forbidden)
            return digest

        patch.setattr(bundles, "_digest", poison)
        # The codec is now rejected before invoking the substituted digest,
        # rather than after it could install a hostile result descriptor.
        with pytest.raises(
            bundles.SyntheticWritePlanBundleRejected,
            match="synthetic recovery bundle codec changed",
        ):
            bundles.restore_synthetic_write_plan_bundle(report)

    assert calls == []


def test_capture_digest_callback_cannot_patch_result_constructor(
    tmp_path, monkeypatch,
):
    review = _review(_fixture(tmp_path / "state"))
    attempted = []
    native = bundles._digest

    def forbidden(*_args, **_kwargs):
        attempted.append("constructor")
        raise AssertionError("forged bundle constructor executed")

    with monkeypatch.context() as patch:
        def poison(data):
            digest = native(data)
            patch.setattr(bundles.SyntheticWritePlanBundle, "__init__", forbidden)
            return digest

        patch.setattr(bundles, "_digest", poison)
        # The codec is now rejected before invoking the substituted digest,
        # rather than after it could install a hostile result descriptor.
        with pytest.raises(
            bundles.SyntheticWritePlanBundleRejected,
            match="synthetic recovery bundle codec changed",
        ):
            bundles.bundle_synthetic_write_plan(review)

    assert attempted == []


def test_unmodified_bundle_is_restart_inert_and_restorable(tmp_path):
    review = _review(_fixture(tmp_path / "state"))
    receipt = bundles.bundle_synthetic_write_plan(review)
    restored = bundles.restore_synthetic_write_plan_bundle(receipt)
    assert len(restored) == 2
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.external_outcome_known is False

"""Detached WRITE-recovery bundles reject changed decoders before use.

Synthetic fixture bytes only. These checks do not authenticate custody,
authorize dispatch, or prove an external tool outcome.
"""

import pytest

import ark.agency.synthetic_plan_recovery_bundle_review as bundle


@pytest.mark.parametrize(
    "target",
    (
        "sha256", "json_dumps", "json_loads", "b64encode",
        "b64decode", "digest", "canonical", "archive",
        "restore", "label", "budget_bool", "budget_expand",
    ),
)
@pytest.mark.parametrize("entrypoint", ("restore", "capture"))
def test_rebound_codec_is_rejected_before_any_decode_or_capture(
    monkeypatch, target, entrypoint,
):
    calls = []

    def hostile(*args, **kwargs):
        calls.append(target)
        raise AssertionError("modified bundle codec was invoked")

    supplied = bundle.SyntheticWritePlanBundle(b'{"version":1}', "not-a-digest")
    with monkeypatch.context() as patch:
        if target == "sha256":
            patch.setattr(bundle.hashlib, "sha256", hostile)
        elif target == "json_dumps":
            patch.setattr(bundle.json, "dumps", hostile)
        elif target == "json_loads":
            patch.setattr(bundle.json, "loads", hostile)
        elif target == "b64encode":
            patch.setattr(bundle.base64, "b64encode", hostile)
        elif target == "b64decode":
            patch.setattr(bundle.base64, "b64decode", hostile)
        elif target == "digest":
            patch.setattr(bundle, "_digest", hostile)
        elif target == "canonical":
            patch.setattr(bundle, "_canonical", hostile)
        elif target == "archive":
            patch.setattr(bundle, "archive_synthetic_recovery", hostile)
        elif target == "restore":
            patch.setattr(bundle, "_restore", hostile)
        elif target == "label":
            patch.setattr(bundle, "_LABEL", b"substituted")
        elif target == "budget_bool":
            patch.setattr(bundle, "_MAX_STEPS", True)
        else:
            patch.setattr(bundle, "_MAX_BYTES", 8_000_000)
        with pytest.raises(
            bundle.SyntheticWritePlanBundleRejected,
            match="synthetic recovery bundle codec changed",
        ):
            if entrypoint == "restore":
                bundle.restore_synthetic_write_plan_bundle(supplied)
            else:
                bundle.bundle_synthetic_write_plan(object())
    assert calls == []


def test_intact_codec_reaches_normal_noncanonical_bundle_rejection():
    payload = b'{"version":1}'
    supplied = bundle.SyntheticWritePlanBundle(
        payload, bundle._digest(payload),
    )
    with pytest.raises(
        bundle.SyntheticWritePlanBundleRejected,
        match="noncanonical bundle shape",
    ):
        bundle.restore_synthetic_write_plan_bundle(supplied)
    assert supplied.dispatch_authorized is False
    assert supplied.automatic_replay_authorized is False
    assert supplied.external_outcome_known is False

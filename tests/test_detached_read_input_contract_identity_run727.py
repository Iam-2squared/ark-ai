"""Fixture-only detached READ input identity fence; no backend dispatch.

An attacker-controlled in-process regex or digest domain must be rejected
before the recovery reviewer can see a caller-retained expected-input claim.
Import-time identities do not prove external provenance or grant replay.
"""

from __future__ import annotations

import re

import pytest

from ark.agency import disconnected_read_input_binding_review as binding

REQUEST = "req_" + "a" * 32
STEP = "step_" + "1" * 16
DIGEST = "b" * 64
INPUTS = ((STEP, DIGEST),)


@pytest.mark.parametrize(
    ("name", "replacement"),
    (
        ("_DOMAIN", b"unreviewed-read-input-join\\0"),
        ("_SHA", re.compile(r".*\\Z")),
        ("_STEP", re.compile(r".*\\Z")),
    ),
)
def test_rebound_input_contract_refuses_without_recovery(
    monkeypatch, name, replacement,
):
    # The poisoned assertion fires if the function ever reaches its private
    # steps/snapshot inputs. Contract validation must run first.
    monkeypatch.setattr(binding, name, replacement)
    with pytest.raises(
        binding.ReadInputBindingRejected,
        match="input-join report authority changed",
    ):
        binding.review_detached_read_input_binding(
            REQUEST, None, None, None, INPUTS,
        )


def test_equal_value_replacement_domain_is_a_distinct_unreviewed_epoch(
    monkeypatch,
):
    copied = bytes(bytearray(binding._DOMAIN))
    assert copied == binding._DOMAIN
    assert copied is not binding._DOMAIN
    monkeypatch.setattr(binding, "_DOMAIN", copied)
    with pytest.raises(
        binding.ReadInputBindingRejected,
        match="input-join report authority changed",
    ):
        binding.review_detached_read_input_binding(
            REQUEST, None, None, None, INPUTS,
        )


def test_original_input_contract_keeps_all_backend_capabilities_denied():
    from test_detached_read_input_dependency_custody_run715 import _case

    report = binding.review_detached_read_input_binding(*_case())
    assert report.successful_step_ids == (STEP,)
    assert report.backend_dispatched is False
    assert report.external_result_proven is False
    assert report.automatic_replay_authorized is False
    assert report.independent_custody_proven is False

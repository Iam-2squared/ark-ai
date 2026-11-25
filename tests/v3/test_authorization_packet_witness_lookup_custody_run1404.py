"""Run1404: V3 detached packet witnesses pin exact class lookup policy."""

from __future__ import annotations

import pytest

from ark.learning import authorization_packet_verify as mod


def _invalid_review_inputs() -> tuple[object, object, str]:
    # The class guard must run before ordinary input validation or any packet
    # construction, so a full execution snapshot is intentionally unnecessary.
    return object(), object(), "not-a-digest"


@pytest.mark.parametrize(
    "hook",
    ("__new__", "__getattribute__", "__getattr__", "__setattr__", "__delattr__"),
)
def test_explicit_none_is_not_confused_with_an_absent_witness_hook(
    monkeypatch: pytest.MonkeyPatch,
    hook: str,
) -> None:
    snapshot, packet, retained = _invalid_review_inputs()

    with monkeypatch.context() as patch:
        patch.setattr(mod.LocalPacketBindingWitness, hook, None, raising=False)
        with pytest.raises(
            mod.LocalPacketBindingRejected,
            match="class lookup contract changed",
        ):
            mod.verify_detached_authorization_packet(
                snapshot, packet, retained_packet_file_sha256=retained,
            )


@pytest.mark.parametrize("hook", ("__getattribute__", "__getattr__"))
def test_hostile_lookup_hook_is_rejected_before_it_executes(
    monkeypatch: pytest.MonkeyPatch,
    hook: str,
) -> None:
    invoked: list[str] = []

    def forbidden(*_args: object, **_kwargs: object) -> object:
        invoked.append(hook)
        raise AssertionError("substituted witness lookup hook executed")

    snapshot, packet, retained = _invalid_review_inputs()
    with monkeypatch.context() as patch:
        patch.setattr(
            mod.LocalPacketBindingWitness, hook, forbidden, raising=False,
        )
        with pytest.raises(
            mod.LocalPacketBindingRejected,
            match="class lookup contract changed",
        ):
            mod.verify_detached_authorization_packet(
                snapshot, packet, retained_packet_file_sha256=retained,
            )

    assert invoked == []


def test_exact_absence_sentinel_installed_as_hook_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot, packet, retained = _invalid_review_inputs()

    with monkeypatch.context() as patch:
        patch.setattr(
            mod.LocalPacketBindingWitness,
            "__getattr__",
            mod._WITNESS_CLASS_HOOK_ABSENT,
            raising=False,
        )
        with pytest.raises(
            mod.LocalPacketBindingRejected,
            match="class lookup contract changed",
        ):
            mod.verify_detached_authorization_packet(
                snapshot, packet, retained_packet_file_sha256=retained,
            )


def test_replaced_absence_sentinel_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as patch:
        patch.setattr(mod, "_WITNESS_CLASS_HOOK_ABSENT", object())
        with pytest.raises(
            mod.LocalPacketBindingRejected,
            match="class lookup contract changed",
        ):
            mod._require_original_witness_contract()


def test_equal_valued_hook_name_vector_replacement_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    replacement = tuple(list(mod._WITNESS_CLASS_HOOK_NAMES))
    assert replacement == mod._WITNESS_CLASS_HOOK_NAMES
    assert replacement is not mod._WITNESS_CLASS_HOOK_NAMES

    with monkeypatch.context() as patch:
        patch.setattr(mod, "_WITNESS_CLASS_HOOK_NAMES", replacement)
        with pytest.raises(
            mod.LocalPacketBindingRejected,
            match="class lookup contract changed",
        ):
            mod._require_original_witness_contract()


def test_denial_flag_inventory_cannot_be_replaced_with_an_empty_vector(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as patch:
        patch.setattr(mod, "_DENIAL_FLAGS", ())
        with pytest.raises(
            mod.LocalPacketBindingRejected,
            match="gained authority",
        ):
            mod._require_original_witness_contract()


def test_false_valued_denial_descriptor_replacement_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as patch:
        patch.setattr(
            mod.LocalPacketBindingWitness,
            "main_merge_authorized",
            property(lambda _self: False),
        )
        with pytest.raises(
            mod.LocalPacketBindingRejected,
            match="gained authority",
        ):
            mod._require_original_witness_contract()


def test_guard_binding_is_retained_across_input_epoch_callbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_pin = mod._pin_json_tree

    def pin_then_replace_guard(value: object) -> object:
        result = original_pin(value)
        monkeypatch.setattr(mod, "_require_original_witness_contract", lambda: None)
        return result

    monkeypatch.setattr(mod, "_pin_json_tree", pin_then_replace_guard)
    with pytest.raises(
        mod.LocalPacketBindingRejected,
        match="class lookup contract changed",
    ):
        mod.verify_detached_authorization_packet(
            {}, {}, retained_packet_file_sha256="0" * 64,
        )


def test_original_witness_class_contract_remains_available() -> None:
    mod._require_original_witness_contract()

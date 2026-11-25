"""Run1417: proactive policy, state and ledger carriers pin absent hooks."""

from __future__ import annotations

import subprocess
import sys


def test_proactive_carriers_reject_none_and_absent_hook_sentinel() -> None:
    script = r"""
import ark.proactive_state_ledger as proactive

guards = (
    proactive._require_original_policy_contract,
    proactive._require_original_state_type,
    proactive._require_original_ledger_class,
)
for guard in guards:
    guard()

def require_rejected(guard, label):
    try:
        guard()
    except proactive.SyntheticProactiveStateRejected:
        return
    raise AssertionError(f"{label} was accepted")

carriers = (
    (
        proactive.SyntheticProactivePolicy,
        proactive._require_original_policy_contract,
    ),
    (
        proactive.SyntheticProactiveState,
        proactive._require_original_state_type,
    ),
    (
        proactive.SyntheticProactiveStateLedger,
        proactive._require_original_ledger_class,
    ),
)
for carrier, guard in carriers:
    for hook in ("__new__", "__getattribute__", "__getattr__"):
        for replacement in (None, proactive._PROACTIVE_CLASS_HOOK_ABSENT):
            type.__setattr__(carrier, hook, replacement)
            require_rejected(guard, f"{carrier.__name__}.{hook}")
            type.__delattr__(carrier, hook)
            guard()
    original_init = vars(carrier)["__init__"]
    type.__setattr__(carrier, "__init__", None)
    require_rejected(guard, f"{carrier.__name__}.__init__")
    type.__setattr__(carrier, "__init__", original_init)
    guard()

def replace_and_restore(module, name, replacement, guard):
    original = getattr(module, name)
    setattr(module, name, replacement)
    require_rejected(guard, name)
    setattr(module, name, original)
    guard()

replace_and_restore(
    proactive, "_PROACTIVE_CLASS_HOOK_ABSENT", object(),
    proactive._require_original_policy_contract,
)
replace_and_restore(
    proactive, "_POLICY_METHODS", tuple(list(proactive._POLICY_METHODS)),
    proactive._require_original_policy_contract,
)
replace_and_restore(
    proactive, "_ORIGINAL_POLICY_METHODS",
    tuple(list(proactive._ORIGINAL_POLICY_METHODS)),
    proactive._require_original_policy_contract,
)
replace_and_restore(
    proactive, "_ORIGINAL_POLICY_VECTORS",
    tuple(list(proactive._ORIGINAL_POLICY_VECTORS)),
    proactive._require_original_policy_contract,
)
replace_and_restore(
    proactive, "_ORIGINAL_POLICY_EPOCH",
    tuple(list(proactive._ORIGINAL_POLICY_EPOCH)),
    proactive._require_original_policy_contract,
)
replace_and_restore(
    proactive, "_STATE_HOOKS", tuple(list(proactive._STATE_HOOKS)),
    proactive._require_original_state_type,
)
replace_and_restore(
    proactive, "_ORIGINAL_STATE_HOOKS",
    tuple(list(proactive._ORIGINAL_STATE_HOOKS)),
    proactive._require_original_state_type,
)
replace_and_restore(
    proactive, "_ORIGINAL_STATE_VECTORS",
    tuple(list(proactive._ORIGINAL_STATE_VECTORS)),
    proactive._require_original_state_type,
)
replace_and_restore(
    proactive, "_ORIGINAL_STATE_EPOCH",
    tuple(list(proactive._ORIGINAL_STATE_EPOCH)),
    proactive._require_original_state_type,
)
replace_and_restore(
    proactive, "_LEDGER_METHODS", tuple(list(proactive._LEDGER_METHODS)),
    proactive._require_original_ledger_class,
)
replace_and_restore(
    proactive, "_ORIGINAL_LEDGER_METHODS",
    tuple(list(proactive._ORIGINAL_LEDGER_METHODS)),
    proactive._require_original_ledger_class,
)
replace_and_restore(
    proactive, "_LEDGER_GUARD_VECTORS",
    tuple(list(proactive._LEDGER_GUARD_VECTORS)),
    proactive._require_original_ledger_class,
)
replace_and_restore(
    proactive, "_ORIGINAL_LEDGER_GUARD_VECTORS",
    tuple(list(proactive._ORIGINAL_LEDGER_GUARD_VECTORS)),
    proactive._require_original_ledger_class,
)
replace_and_restore(
    proactive, "_ORIGINAL_LEDGER_EPOCH",
    tuple(list(proactive._ORIGINAL_LEDGER_EPOCH)),
    proactive._require_original_ledger_class,
)

def replace_type_alias(type_name, alias_name, guard):
    old_type = getattr(proactive, type_name)
    old_alias = getattr(proactive, alias_name)
    replacement = type("ReplacementCarrier", (), {})
    setattr(proactive, type_name, replacement)
    setattr(proactive, alias_name, replacement)
    require_rejected(guard, f"joint {alias_name} replacement")
    setattr(proactive, type_name, old_type)
    setattr(proactive, alias_name, old_alias)
    guard()

replace_type_alias(
    "_POLICY_TYPE", "SyntheticProactivePolicy",
    proactive._require_original_policy_contract,
)
replace_type_alias(
    "_STATE_TYPE", "SyntheticProactiveState",
    proactive._require_original_state_type,
)
replace_type_alias(
    "_LEDGER_TYPE", "SyntheticProactiveStateLedger",
    proactive._require_original_ledger_class,
)
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

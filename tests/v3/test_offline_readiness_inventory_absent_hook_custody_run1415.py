"""Run1415: passive V3 readiness inventory pins absent class hooks."""

from __future__ import annotations

import subprocess
import sys


def test_absent_inventory_hooks_reject_none_and_sentinel_installation() -> None:
    script = r"""
import ark.learning.offline_readiness_inventory as inventory

inventory._assert_original_inventory_protocol()
carrier = inventory.OfflineReadinessInventory

def require_rejected(label):
    try:
        inventory._assert_original_inventory_protocol()
    except inventory.OfflineReadinessRejected:
        return
    raise AssertionError(f"{label} was accepted")

for hook in ("__new__", "__getattribute__", "__getattr__"):
    for replacement in (None, inventory._ABSENT_INVENTORY_HOOK):
        type.__setattr__(carrier, hook, replacement)
        require_rejected(f"{hook}={replacement!r}")
        type.__delattr__(carrier, hook)
        inventory._assert_original_inventory_protocol()

def replace_and_restore(name, replacement):
    original = getattr(inventory, name)
    setattr(inventory, name, replacement)
    require_rejected(name)
    setattr(inventory, name, original)
    inventory._assert_original_inventory_protocol()

replace_and_restore("_ABSENT_INVENTORY_HOOK", object())
replace_and_restore(
    "_INVENTORY_HOOKS",
    tuple(list(inventory._INVENTORY_HOOKS)),
)
replace_and_restore(
    "_INVENTORY_PINNED_NAMES",
    tuple(list(inventory._INVENTORY_PINNED_NAMES)),
)
replace_and_restore(
    "_ORIGINAL_INVENTORY_CARRIERS",
    tuple(list(inventory._ORIGINAL_INVENTORY_CARRIERS)),
)
replace_and_restore(
    "_ORIGINAL_INVENTORY_DENIALS",
    tuple(list(inventory._ORIGINAL_INVENTORY_DENIALS)),
)
replace_and_restore(
    "_ORIGINAL_INVENTORY_EPOCH",
    tuple(list(inventory._ORIGINAL_INVENTORY_EPOCH)),
)

original_type = inventory._ORIGINAL_INVENTORY_TYPE
original_alias = inventory.OfflineReadinessInventory
replacement_type = type("ReplacementInventory", (), {})
inventory._ORIGINAL_INVENTORY_TYPE = replacement_type
inventory.OfflineReadinessInventory = replacement_type
require_rejected("joint inventory type-alias replacement")
inventory._ORIGINAL_INVENTORY_TYPE = original_type
inventory.OfflineReadinessInventory = original_alias
inventory._assert_original_inventory_protocol()
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

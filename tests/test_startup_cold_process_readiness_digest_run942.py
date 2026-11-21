"""Cross-interpreter deterministic, disconnected startup dependency diagnostics.

No probe here proves actual hardware or backend readiness, human consent,
trusted time, write authority, or permission to resume a real action.
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    evaluate_startup_readiness,
)

_CHILD = """
import json
import sys
from ark.startup_readiness_review import (
    ReadinessState, StartupComponent, evaluate_startup_readiness,
)
specs = json.loads(sys.argv[1])
components = tuple(
    StartupComponent(
        item["id"], tuple(item["deps"]), ReadinessState(item["state"]),
        item.get("failure"), item.get("revision"),
    ) for item in specs
)
snapshot = evaluate_startup_readiness(components)
ids = sorted(item["id"] for item in specs)
print(json.dumps({
    "digest": snapshot.digest,
    "states": {name: snapshot.state(name).value for name in ids},
    "blockers": {name: snapshot.root_blockers(name) for name in ids},
}, sort_keys=True))
"""


def _specs(variant: int) -> list[dict[str, object]]:
    roots = [
        {"id": "memory", "deps": [], "state": "blocked", "failure": "wal-unknown"},
        {"id": "audit", "deps": [], "state": "blocked", "failure": "custody-unknown"},
        {"id": "read", "deps": [], "state": "ready"},
        {"id": "planner", "deps": ["memory"], "state": "ready"},
        {"id": "write", "deps": ["planner", "audit"], "state": "ready"},
        {"id": "safe", "deps": ["read"], "state": "ready"},
    ]
    if variant == 1:
        roots[0]["revision"] = "schema-v2"
        roots[2]["state"] = "degraded"
    elif variant == 2:
        roots[1]["state"] = "ready"
        roots[1]["failure"] = None
        roots[4]["deps"] = ["audit", "planner"]
    return roots


@pytest.mark.parametrize("variant", (0, 1, 2))
@pytest.mark.parametrize("reverse", (False, True))
def test_cold_process_agrees_on_readiness_digest_and_blocker_propagation(
    variant: int, reverse: bool,
) -> None:
    specs = _specs(variant)
    if reverse:
        specs.reverse()
    components = tuple(
        StartupComponent(
            item["id"], tuple(item["deps"]), ReadinessState(item["state"]),
            item.get("failure"), item.get("revision"),
        )
        for item in specs
    )
    snapshot = evaluate_startup_readiness(components)
    expected = {
        "digest": snapshot.digest,
        "states": {
            item["id"]: snapshot.state(item["id"]).value for item in specs
        },
        "blockers": {
            item["id"]: list(snapshot.root_blockers(item["id"])) for item in specs
        },
    }
    child = subprocess.run(
        [sys.executable, "-c", _CHILD, json.dumps(specs)],
        check=True, capture_output=True, text=True, timeout=20,
    )
    assert json.loads(child.stdout) == expected
    assert snapshot.state("write") is ReadinessState.DEPENDENCY_BLOCKED
    assert snapshot.state("safe") is ReadinessState.READY
    assert snapshot.root_blockers("write") == (
        ("memory",) if variant == 2 else ("audit", "memory")
    )


def test_schema_revision_changes_digest_but_not_dependency_permission() -> None:
    a = _specs(0)
    b = _specs(0)
    b[0]["revision"] = "changed-synthetic-schema"
    old = evaluate_startup_readiness(tuple(
        StartupComponent(
            x["id"], tuple(x["deps"]), ReadinessState(x["state"]),
            x.get("failure"), x.get("revision"),
        ) for x in a
    ))
    new = evaluate_startup_readiness(tuple(
        StartupComponent(
            x["id"], tuple(x["deps"]), ReadinessState(x["state"]),
            x.get("failure"), x.get("revision"),
        ) for x in b
    ))
    assert old.digest != new.digest
    assert old.state("write") is new.state("write") is ReadinessState.DEPENDENCY_BLOCKED
    assert old.root_blockers("write") == new.root_blockers("write")

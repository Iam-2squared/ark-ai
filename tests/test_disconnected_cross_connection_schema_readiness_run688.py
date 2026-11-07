"""Startup preflight sees cross-connection schema drift without reading rows.

A disconnected READY diagnostic is never an authenticated startup lease.
One SQLite writer changes only synthetic schema/data while an independent
query-only handle retains the prior schema seal; no tool can dispatch.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency.contracts import CapabilityGrant, Effect, PlanStep, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.disconnected_local_readiness import (
    DisconnectedLocalReadinessRejected,
    review_disconnected_local_readiness,
)
from ark.disconnected_sqlite_schema_probe import capture_disconnected_sqlite_schema


class _InertBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("disconnected startup attempted a tool execution")


@pytest.mark.parametrize(
    ("external_sql", "schema_changed"),
    (
        ("INSERT INTO fixture(value) VALUES('synthetic')", False),
        ("CREATE TABLE extra(id INTEGER PRIMARY KEY)", True),
        ("CREATE INDEX idx_fixture_value ON fixture(value)", True),
        ("CREATE VIEW fixture_view AS SELECT id FROM fixture", True),
        (
            "CREATE TRIGGER synthetic_trigger AFTER INSERT ON fixture "
            "BEGIN SELECT 1; END",
            True,
        ),
    ),
)
def test_external_schema_change_invalidates_query_only_startup_probe(
    tmp_path, external_sql, schema_changed,
):
    path = tmp_path / "readiness.sqlite"
    with sqlite3.connect(path) as writer:
        writer.execute("CREATE TABLE fixture(id INTEGER PRIMARY KEY, value TEXT)")
    reader = sqlite3.connect(path)
    try:
        reader.execute("PRAGMA query_only=ON")
        seal = capture_disconnected_sqlite_schema(reader)
        backend = _InertBackend()
        registry = ToolRegistry((
            ToolRegistration(
                "reader", "local.read", Effect.READ, "fixture-only", backend,
            ),
        ))
        plan = PlanGraph((
            PlanStep(
                "root", ToolCall(
                    "reader", "local.read", "private",
                    {"object": "fixture"},
                ),
            ),
        ))
        gate = PermissionGate()
        grants = (CapabilityGrant("local.read", "private", 500),)
        initial = review_disconnected_local_readiness(
            reader, seal, plan, registry, gate, grants, observed_at_ms=100,
        )
        assert initial.ready_step_ids == ("root",)
        assert initial.startup_authorized is False
        with sqlite3.connect(path) as external:
            external.execute(external_sql)

        if schema_changed:
            with pytest.raises(
                DisconnectedLocalReadinessRejected, match="schema",
            ):
                review_disconnected_local_readiness(
                    reader, seal, plan, registry, gate, grants,
                    observed_at_ms=100,
                )
        else:
            again = review_disconnected_local_readiness(
                reader, seal, plan, registry, gate, grants,
                observed_at_ms=100,
            )
            assert again == initial
            assert again.source_authenticated is False
            assert again.cross_store_atomicity_proven is False
            assert again.dispatch_authorized is False
        assert backend.calls == 0
    finally:
        reader.close()

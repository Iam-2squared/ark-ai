"""Write-path carrier/source epochs for disconnected preaction audit links.

Every fixture remains local/mock-only; successful links authorize no dispatch,
real-world outcome, user consent or automatic replay.
"""

import hashlib
from pathlib import Path

import pytest

import ark.agency.synthetic_occurrence_audit_link_review as links
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.registry import ToolRegistration, ToolRegistry


class NoExecution:
    def execute(self, call):
        raise AssertionError("audit-link review must not dispatch")


def _fixture(tmp_path):
    call = ToolCall("offline", "fixture", "local", {"a": 1})
    registry = ToolRegistry((
        ToolRegistration("offline", "fixture", Effect.WRITE, "none", NoExecution()),
    ))
    ledger = SyntheticOccurrenceStore(tmp_path / "occ.sqlite")
    receipt = ledger.reserve_synthetic(
        registry, call, OneShotAuthorization("local-token", call.request_id, 999),
        occurrence_id="occ_" + hashlib.sha256(b"occ").hexdigest(), now_ms=10,
    )
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    event = audit.append(call, outcome="synthetic_audit_before_mock")
    link = links.SyntheticOccurrenceAuditLinkStore(tmp_path / "link.sqlite")
    return registry, call, ledger, receipt, audit, event, link


def _link(state, *, retained=None):
    registry, call, ledger, receipt, audit, event, link = state
    return link.link_synthetic(
        registry, call, ledger, receipt, audit, event,
        at_ms=15, retained=retained,
    )


def _clone(value):
    result = ("!" + value)[1:]
    assert result == value and result is not value
    return result


@pytest.mark.parametrize("source", ("link", "ledger", "audit"))
def test_link_open_does_not_accept_equal_path_substitution(
    tmp_path, monkeypatch, source,
):
    state = _fixture(tmp_path)
    ledger, audit, link = state[2], state[4], state[6]
    original = link._connect

    def changed(*, create=False, readonly=False):
        conn = original(create=create, readonly=readonly)
        if source == "link":
            link._path = Path(str(link._path))
        elif source == "ledger":
            ledger._path = Path(str(ledger._path))
        else:
            audit.path = Path(str(audit.path))
        return conn

    monkeypatch.setattr(link, "_connect", changed)
    with pytest.raises(links.SyntheticAuditLinkRejected, match="original input or source"):
        _link(state)
    assert link.read_witness().event_count == 0


def test_link_begin_retarget_fails_before_replay(tmp_path, monkeypatch):
    state = _fixture(tmp_path)
    link = state[6]
    opened = link._connect
    replay = links._replay
    calls = []

    class Proxy:
        def __init__(self, conn):
            self.conn = conn

        def execute(self, statement, *args):
            result = self.conn.execute(statement, *args)
            if statement == "BEGIN IMMEDIATE":
                link._path = Path(str(link._path))
            return result

        def __getattr__(self, name):
            return getattr(self.conn, name)

    monkeypatch.setattr(
        link, "_connect", lambda **kw: Proxy(opened(**kw)),
    )

    def observed(conn):
        calls.append(True)
        return replay(conn)

    monkeypatch.setattr(links, "_replay", observed)
    with pytest.raises(links.SyntheticAuditLinkRejected, match="original input or source"):
        _link(state)
    assert calls == []


@pytest.mark.parametrize("phase", ("event_hash", "reservation_validation", "audit_read"))
def test_link_callbacks_cannot_rebind_original_fields(
    tmp_path, monkeypatch, phase,
):
    state = _fixture(tmp_path)
    receipt, event, audit = state[3], state[5], state[4]
    if phase == "event_hash":
        original = links._hash

        def changed(label, fields):
            result = original(label, fields)
            if label == "ARK-synthetic-preaction-audit-v1":
                object.__setattr__(
                    receipt, "bound_action_id", _clone(receipt.bound_action_id),
                )
            return result

        monkeypatch.setattr(links, "_hash", changed)
    elif phase == "reservation_validation":
        original = links._validate_reservations

        def changed(conn):
            result = original(conn)
            object.__setattr__(event, "tool", _clone(event.tool))
            return result

        monkeypatch.setattr(links, "_validate_reservations", changed)
    else:
        original = audit.events

        def changed(**kwargs):
            observed = original(**kwargs)
            object.__setattr__(receipt, "request_id", _clone(receipt.request_id))
            return observed

        monkeypatch.setattr(audit, "events", changed)
    with pytest.raises(links.SyntheticAuditLinkRejected, match="original input or source"):
        _link(state)
    assert state[6].read_witness().event_count == 0


def test_retained_digest_rebinding_during_replay_is_rejected(tmp_path, monkeypatch):
    state = _fixture(tmp_path)
    retained = state[6].read_witness()
    original = links._replay

    def changed(conn):
        result = original(conn)
        object.__setattr__(retained, "tail_hash", _clone(retained.tail_hash))
        return result

    monkeypatch.setattr(links, "_replay", changed)
    with pytest.raises(links.SyntheticAuditLinkRejected, match="original input or source"):
        _link(state, retained=retained)


def test_committed_link_stays_durable_if_commit_callback_changes_source(
    tmp_path, monkeypatch,
):
    state = _fixture(tmp_path)
    audit, link = state[4], state[6]
    opened = link._connect

    class Proxy:
        def __init__(self, conn):
            self.conn = conn

        def commit(self):
            self.conn.commit()
            audit.path = Path(str(audit.path))

        def __getattr__(self, name):
            return getattr(self.conn, name)

    monkeypatch.setattr(
        link, "_connect", lambda **kw: Proxy(opened(**kw)),
    )
    with pytest.raises(links.SyntheticAuditLinkRejected, match="original input or source"):
        _link(state)
    # After COMMIT the link must remain even if a callback denied its receipt.
    assert link.read_witness().event_count == 1


def test_healthy_link_remains_inert_and_replay_is_blocked(tmp_path):
    state = _fixture(tmp_path)
    prior = state[6].read_witness()
    receipt = _link(state, retained=prior)
    assert receipt.dispatch_authorized is False
    assert receipt.external_outcome_known is False
    assert receipt.automatic_replay_authorized is False
    assert state[6].read_witness(retained=prior).event_count == 1

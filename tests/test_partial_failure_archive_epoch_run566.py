"""A synthetic FAILED/BLOCKED archive must not change in a False denial.

All evidence is disconnected local-fixture evidence; neither real backend
dispatch nor authenticated execution, retry, or clock authority is inferred.
"""

from __future__ import annotations

import pytest
from test_partial_registered_failure_join_run558 import invoke, setup_case

from ark.agency import disconnected_partial_registered_failure_join as mod


@pytest.mark.parametrize(
    ("kind", "denial"),
    (
        ("archive", "external_dispatch_authorized"),
        ("fixture", "dispatch_authorized"),
    ),
)
def test_false_only_denial_cannot_rewrite_retained_failure_evidence(
    tmp_path, monkeypatch, kind, denial,
):
    case = setup_case(tmp_path)
    cls = (
        mod.ArchivedDisconnectedFailure
        if kind == "archive"
        else mod.DisconnectedFailureFixtureReceipt
    )
    original_getattribute = cls.__getattribute__

    def mutate_on_denial(self, name):
        result = original_getattribute(self, name)
        if name == denial:
            if kind == "archive":
                object.__setattr__(self, "file_sha256", "f" * 64)
            else:
                object.__setattr__(
                    self, "terminal_states",
                    ((case["plan"].steps[0].step_id, "SUCCEEDED"),),
                )
        return result

    # The nested archive validator rejects this __getattribute__ interception
    # before the outer cross-receipt mutation check. That is a valid earlier
    # fail-closed boundary; it must never progress to backend dispatch.
    monkeypatch.setattr(cls, "__getattribute__", mutate_on_denial)
    try:
        with pytest.raises(
            mod.PartialFailureJoinRejected,
            match="partial registered failure archive reconciliation denied",
        ):
            invoke(case)
        assert case["backend"].calls == 0
        assert not case["gate"]._consumed_tokens
    finally:
        case["journal"].close()


def test_original_readonly_failure_archive_remains_coherent(tmp_path):
    case = setup_case(tmp_path)
    try:
        result = invoke(case)
        assert result.failure_file_sha256 == case["witness"].file_sha256
        assert result.terminal_states[-1][1] == "BLOCKED"
        assert result.backend_dispatched is False
        assert result.automatic_replay_authorized is False
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()

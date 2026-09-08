import pytest

from ark.intelligence import Capabilities, Intelligence, Message, TaskMode
from ark.intelligence.context import ContextBudgetError, ContextManager, estimate_tokens
from ark.models import EchoBackend, GenerationConfig


def pair(user="hello", answer="ok"):
    return (Message("user", user), Message("assistant", answer))


def test_exact_budget_boundary_and_whole_turn_eviction():
    # Fake counter isolates budgeting arithmetic from heuristic changes.
    counter = lambda messages: len(messages) * 10  # noqa: E731
    manager = ContextManager(65, safety_margin=5, counter=counter, counting_method="test")
    history = pair("old", "old answer") + pair("recent", "recent answer")
    result = manager.prepare("system", history, "now", 20)
    assert result.messages == (Message("system", "system"), *history[2:], Message("user", "now"))
    assert result.dropped_turns == 1
    assert result.utilization_estimate == 1.0
    assert history[0].content == "old"
    with pytest.raises(ContextBudgetError):
        ContextManager(44, safety_margin=5, counter=counter).prepare("s", (), "u", 20)


@pytest.mark.parametrize(
    "history",
    [
        (Message("user", "orphan"),),
        (Message("assistant", "wrong"), Message("user", "order")),
        (Message("system", "injected"), Message("assistant", "wrong")),
    ],
)
def test_invalid_history_order_rejected(history):
    with pytest.raises(ValueError, match="ordered complete"):
        ContextManager(1000).prepare("system", history, "current", 10)


def test_utf8_budget_and_oversized_current_message():
    assert estimate_tokens((Message("user", "あ"),)) > estimate_tokens((Message("user", "a"),))
    engine = Intelligence(EchoBackend(), Capabilities(4096, True, "test"))
    engine.chat("small")
    original = engine.history
    with pytest.raises(ContextBudgetError):
        engine.chat("あ" * 4096)
    assert engine.history == original


@pytest.mark.parametrize("failure", [RuntimeError("backend broke"), "", None])
def test_failed_generation_keeps_history_and_reset_recovers(failure):
    class FailingBackend(EchoBackend):
        broken = False

        def generate(self, messages, config):
            if self.broken:
                if isinstance(failure, Exception):
                    raise failure
                return failure
            return super().generate(messages, config)

    backend = FailingBackend()
    engine = Intelligence(backend, Capabilities(4096, True, "test"))
    engine.chat("hello")
    original = engine.history
    backend.broken = True
    with pytest.raises(RuntimeError):
        engine.chat("second")
    assert engine.history == original
    engine.reset()
    backend.broken = False
    assert len(engine.chat("new").request.context.messages) == 2


def test_failed_generation_does_not_commit_eviction():
    class Backend(EchoBackend):
        broken = False

        def generate(self, messages, config):
            if self.broken:
                raise ValueError("overflow")
            return "x" * 150

    backend = Backend()
    engine = Intelligence(
        backend, Capabilities(650, True, "test"), generation=GenerationConfig(max_tokens=32)
    )
    engine.chat("x" * 50)
    original = engine.history
    backend.broken = True
    with pytest.raises(ValueError, match="overflow"):
        engine.chat("x" * 100)
    assert engine.history == original
    backend.broken = False
    response = engine.chat("x" * 100)
    assert response.request.context.dropped_turns == 1
    assert len(engine.history) == 2


def test_policy_switch_and_backend_interchangeability():
    captured = []

    class OtherBackend:
        name = "unrelated-model"
        last_metrics = None

        def generate(self, messages, config):
            captured.append(messages)
            return "answer"

    engine = Intelligence(OtherBackend(), Capabilities(4096, True, "runtime config"))
    a = engine.chat("Explain", TaskMode.EXPLANATION)
    b = engine.chat("JSON please", TaskMode.STRUCTURED)
    assert a.request.request_id != b.request.request_id
    assert "valid JSON" in captured[-1][0]["content"]
    assert [m["role"] for m in captured[-1]] == ["system", "user", "assistant", "user"]
    captured[-1][1]["content"] = "external mutation"
    assert engine.history[0].content == "Explain"


@pytest.mark.parametrize(
    "generation",
    [
        GenerationConfig(max_tokens=-1),
        GenerationConfig(top_p=2),
        GenerationConfig(temperature=float("nan")),
        GenerationConfig(seed="bad"),
    ],
)
def test_invalid_controls_rejected_before_generation(generation):
    with pytest.raises(ValueError):
        Intelligence(EchoBackend(), Capabilities(4096, True, "test"), generation=generation)


def test_missing_capabilities_rejected():
    with pytest.raises(ValueError, match="chat-compatible"):
        Intelligence(EchoBackend(), Capabilities(4096, False, "test"))
    with pytest.raises(ValueError, match="controls"):
        Intelligence(EchoBackend(), Capabilities(4096, True, "test", generation_controls=()))
    with pytest.raises(ValueError, match="provenance"):
        Capabilities(4096, True, "")

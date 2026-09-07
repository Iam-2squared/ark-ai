from ark.core import ArkCore
from ark.models import EchoBackend


def test_chat_keeps_conversation_history() -> None:
    core = ArkCore(EchoBackend())
    assert core.chat("hello") == "ECHO: hello"
    assert [item["role"] for item in core.history] == ["user", "assistant"]


def test_chat_rejects_blank_message() -> None:
    core = ArkCore(EchoBackend())
    try:
        core.chat("   ")
    except ValueError as exc:
        assert "empty" in str(exc)
    else:
        raise AssertionError("blank message was accepted")


def test_reset_clears_history() -> None:
    core = ArkCore(EchoBackend())
    core.chat("hello")
    core.reset()
    assert core.history == []

"""One model and one V2 conversation per local server process."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock, Thread

from ..config import load_config
from ..intelligence.contracts import Capabilities
from ..intelligence.engine import Intelligence
from ..intelligence.runtime import local_engine
from ..logging import SessionLogger
from ..models import EchoBackend

MAX_MESSAGE_CHARACTERS = 16000
MAX_DISPLAY_MESSAGES = 200


@dataclass
class Runtime:
    engine: Intelligence
    metadata: dict[str, object]
    logger: SessionLogger | None = None


def load_runtime(config_path: str | None, *, mock: bool = False) -> Runtime:
    if mock:
        if config_path:
            raise ValueError("--mock cannot be combined with --config")
        return Runtime(
            Intelligence(EchoBackend(), Capabilities(4096, True, "UI mock demonstration")),
            {"name": "Echo — deterministic mock", "local_model": False,
             "family": None, "quantization": None, "context_capacity": 4096},
        )
    config = load_config(config_path)
    engine = local_engine(config)
    logger = SessionLogger(config.log_directory)
    logger.write(role="event", content="Local UI V2 session started", model=engine.backend.name)
    return Runtime(engine, {
        "name": engine.backend.name,
        "family": config.model_family,
        "parameter_size": config.parameter_size,
        "quantization": config.quantization,
        "context_capacity": engine.capabilities.context_capacity,
        "local_model": True,
    }, logger)


class SessionError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


class LocalSession:
    """Serialize V2 calls. Display history is never passed back as model context."""

    def __init__(self, loader: Callable[[], Runtime]):
        self._loader = loader
        self._lock = Lock()
        self._started = False
        self._runtime: Runtime | None = None
        self._state = "loading"
        self._revision = 0
        self._messages: list[dict[str, str]] = []
        self._pending: str | None = None
        self._error: str | None = None
        self._warning: str | None = None
        self._dropped_turns = 0

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            self._started = True
        Thread(target=self._load, name="ark-ui-load", daemon=True).start()

    def _load(self) -> None:
        try:
            runtime = self._loader()
        except Exception as exc:
            with self._lock:
                self._state = "error"
                self._error = (
                    f"モデルを読み込めませんでした。設定を確認して再起動してください。 {exc}"
                )[:1500]
                self._revision += 1
            return
        with self._lock:
            self._runtime = runtime
            self._state = "ready"
            self._revision += 1

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return {
                "state": self._state,
                "revision": self._revision,
                "intelligence": "V2",
                "model": dict(self._runtime.metadata) if self._runtime else None,
                "messages": [dict(message) for message in self._messages],
                "pending_message": self._pending,
                "error": self._error,
                "warning": self._warning,
                "dropped_turns": self._dropped_turns,
                "logging": bool(self._runtime and self._runtime.logger),
            }

    def _require_ready(self, revision: object) -> Runtime:
        if self._state != "ready" or self._runtime is None:
            raise SessionError(409, "モデルの準備・生成が完了してから操作してください。")
        if type(revision) is not int or revision != self._revision:
            raise SessionError(
                409, "会話が更新されました。画面の最新状態を確認して再操作してください。"
            )
        return self._runtime

    def chat(self, text: object, revision: object) -> None:
        if not isinstance(text, str) or not text.strip():
            raise SessionError(400, "メッセージを入力してください。")
        if len(text) > MAX_MESSAGE_CHARACTERS:
            raise SessionError(413, "メッセージは16,000文字以内にしてください。")
        with self._lock:
            runtime = self._require_ready(revision)
            self._state = "generating"
            self._pending = text.strip()
            self._error = None
            self._revision += 1
        Thread(target=self._generate, args=(runtime, text.strip()),
               name="ark-ui-generate", daemon=True).start()

    @staticmethod
    def _log(runtime: Runtime, role: str, content: str) -> None:
        if runtime.logger:
            runtime.logger.write(role=role, content=content, model=runtime.engine.backend.name)

    def _generate(self, runtime: Runtime, text: str) -> None:
        try:
            # If the user's turn cannot be logged, do not advance model context.
            self._log(runtime, "user", text)
            response = runtime.engine.chat(text)
        except Exception as exc:
            warning = None
            try:
                self._log(runtime, "error", f"{type(exc).__name__}: {exc}")
            except OSError:
                warning = "ログを保存できません。保存先を確認してサーバーを再起動してください。"
            with self._lock:
                self._state = "error" if warning else "ready"
                self._pending = None
                self._error = f"回答を生成できませんでした。 {exc}"[:1500]
                self._warning = warning
                self._revision += 1
            return

        warning = None
        try:
            self._log(runtime, "assistant", response.text)
        except OSError:
            # V2 has already committed this turn: keep the answer visible, stop new writes.
            warning = "回答は生成済みですがログ保存に失敗しました。サーバーを再起動してください。"
        with self._lock:
            self._messages.extend([
                {"role": "user", "content": text},
                {"role": "assistant", "content": response.text},
            ])
            self._messages = self._messages[-MAX_DISPLAY_MESSAGES:]
            self._dropped_turns = response.request.context.dropped_turns
            self._pending = None
            self._warning = warning
            self._state = "error" if warning else "ready"
            self._revision += 1

    def reset(self, revision: object) -> None:
        with self._lock:
            runtime = self._require_ready(revision)
            runtime.engine.reset()
            self._messages.clear()
            self._pending = None
            self._dropped_turns = 0
            self._error = None
            self._warning = None
            self._revision += 1
            try:
                self._log(runtime, "event", "Conversation reset; history empty")
            except OSError:
                self._state = "error"
                self._warning = (
                    "会話はリセット済みですがログ保存に失敗しました。再起動してください。"
                )

"""Opt-in local runtime wiring, independent of any model family."""

from ..cli import build_backend
from ..config import ArkConfig
from .contracts import Capabilities
from .engine import Intelligence

V1_FREEZE_SHA = "7e46a4529879243b4a5bd52bb6575d11c1ec0183"


def local_engine(config: ArkConfig) -> Intelligence:
    if config.backend != "llama-cpp":
        raise ValueError("real evaluation requires model.backend = 'llama-cpp', not a mock")
    if not config.model_path:
        raise ValueError("a local GGUF model.path is required")
    capabilities = Capabilities(
        context_capacity=config.context_size,
        chat_template_supported=True,
        source="configured context; llama-cpp chat API; template compatibility needs target review",
    )
    return Intelligence(build_backend(config), capabilities, generation=config.generation)

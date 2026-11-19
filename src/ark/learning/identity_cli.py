"""Offline-only identity capture for V3 execution-snapshot closure."""

from __future__ import annotations

import argparse
from pathlib import Path

from .execution import canonical_json, sha256_bytes
from .chat_template_probe import build_chat_template_probe
from .identity import build_code_tree_identity, build_hf_snapshot_identity, build_tool_identity

_MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"


def _write_new_json(path: Path, payload: dict) -> str:
    path = Path(path)
    # Exclusive creation protects the final file, but does not establish
    # custody if any already-existing parent is a symlink or the requested
    # name traverses through "..". Reject those aliases before writing an
    # otherwise reproducible local identity artifact.
    if (
        ".." in path.parts
        or len(str(path)) > 4096
        or path.name in ("", ".", "..")
        or path.exists()
        or path.is_symlink()
        or not path.parent.is_dir()
        or any(parent.is_symlink() for parent in path.parents)
    ):
        raise ValueError("identity output must be a new file under an existing directory")
    data = canonical_json(payload)
    with path.open("xb") as handle:
        handle.write(data)
    return sha256_bytes(data)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ARK V3 offline identity capture")
    sub = parser.add_subparsers(dest="command", required=True)

    hf = sub.add_parser("hf-snapshot", help="hash an already-materialized HF snapshot")
    hf.add_argument("--root", type=Path, required=True)
    hf.add_argument("--revision", required=True)
    hf.add_argument("--chat-template-probe", type=Path, required=True)
    hf.add_argument("--output", type=Path, required=True)

    probe = sub.add_parser(
        "chat-template-probe",
        help="render a fixed probe from an already-materialized local tokenizer",
    )
    probe.add_argument("--root", type=Path, required=True)
    probe.add_argument("--output", type=Path, required=True)

    tool = sub.add_parser("tool", help="hash a pinned export tool file")
    tool.add_argument("--path", type=Path, required=True)
    tool.add_argument("--revision", required=True)
    tool.add_argument(
        "--role",
        choices=("hf_to_gguf_converter", "quantizer"),
        required=True,
    )
    tool.add_argument("--output", type=Path, required=True)

    code = sub.add_parser("code", help="hash the V3 runtime source tree")
    code.add_argument("--root", type=Path, required=True)
    code.add_argument("--output", type=Path, required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "chat-template-probe":
        try:
            from transformers import AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "local chat-template probe requires the installed transformers package"
            ) from exc
        tokenizer = AutoTokenizer.from_pretrained(
            str(args.root),
            local_files_only=True,
            trust_remote_code=False,
        )
        payload = build_chat_template_probe(tokenizer)
        artifact_sha = _write_new_json(args.output, payload)
        print(f"identity_artifact_sha256={artifact_sha}")
        print(f"chat_template_probe_sha256={artifact_sha}")
        return 0
    elif args.command == "hf-snapshot":
        payload = build_hf_snapshot_identity(
            args.root,
            model_id=_MODEL_ID,
            revision=args.revision,
            chat_template_probe=args.chat_template_probe,
        )
    elif args.command == "tool":
        payload = build_tool_identity(
            args.path,
            git_revision=args.revision,
            role=args.role,
        )
    else:
        payload = build_code_tree_identity(args.root)

    artifact_sha = _write_new_json(args.output, payload)
    print(f"identity_artifact_sha256={artifact_sha}")
    if args.command == "hf-snapshot":
        print(f"base_file_manifest_sha256={payload['base_file_manifest_sha256']}")
        print(f"tokenizer_file_manifest_sha256={payload['tokenizer_file_manifest_sha256']}")
        print(f"chat_template_probe_sha256={payload['chat_template_probe_sha256']}")
    elif args.command == "tool":
        print(f"tool_identity_sha256={payload['identity_sha256']}")
    else:
        print(f"code_manifest_sha256={payload['manifest_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

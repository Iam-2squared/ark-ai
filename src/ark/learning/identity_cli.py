"""Offline-only identity capture for V3 execution-snapshot closure."""

from __future__ import annotations

import argparse
from pathlib import Path

from .execution import canonical_json, sha256_bytes
from .identity import build_code_tree_identity, build_hf_snapshot_identity, build_tool_identity

_MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"


def _write_new_json(path: Path, payload: dict) -> str:
    path = Path(path)
    if path.exists() or path.is_symlink() or not path.parent.is_dir():
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
    if args.command == "hf-snapshot":
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

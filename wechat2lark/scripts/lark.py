"""Thin wrapper around lark-cli for our specific upload + archive flow."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


class LarkError(RuntimeError):
    pass


def _run(args: list[str], cwd: Path | None = None) -> dict:
    cli = shutil.which("lark-cli")
    if cli is None:
        raise LarkError("lark-cli not found in PATH. Install via larksuite/cli.")
    proc = subprocess.run(
        [cli, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(cwd) if cwd else None,
    )
    if proc.returncode != 0:
        raise LarkError(
            f"lark-cli failed: {' '.join(args)}\nstderr: {proc.stderr.strip()}"
        )
    out = proc.stdout.strip()
    if not out:
        return {}
    try:
        return json.loads(out)
    except json.JSONDecodeError as e:
        raise LarkError(f"lark-cli returned non-JSON output: {out[:500]}") from e


def import_docx(file_path: Path, name: str, identity: str = "user") -> str:
    """Import a local .docx into Drive as a Feishu docx. Returns the obj token."""
    file_path = file_path.resolve()
    result = _run(
        [
            "drive",
            "+import",
            "--file",
            file_path.name,
            "--type",
            "docx",
            "--name",
            name,
            "--as",
            identity,
        ],
        cwd=file_path.parent,
    )
    token = (
        result.get("data", {}).get("token")
        or result.get("token")
        or result.get("data", {}).get("ticket")
    )
    if not token:
        raise LarkError(f"import did not return a token: {result}")
    return token


def move_to_wiki(
    docx_token: str,
    space_id: str,
    parent_node_token: str | None,
    identity: str = "user",
) -> dict:
    """Move a Drive docx into a wiki space. Returns the response payload (contains node info)."""
    args = [
        "wiki",
        "+move",
        "--obj-type",
        "docx",
        "--obj-token",
        docx_token,
        "--target-space-id",
        space_id,
        "--as",
        identity,
    ]
    if parent_node_token:
        args.extend(["--target-parent-token", parent_node_token])
    return _run(args)


def wiki_node_url(space_id: str, node_token: str) -> str:
    return f"https://feishu.cn/wiki/{node_token}" if node_token else ""

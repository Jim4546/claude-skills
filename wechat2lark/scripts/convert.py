"""Main entry: WeChat MP article URL -> Feishu wiki docx archive."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from docx_builder import build_docx
from lark import LarkError, import_docx, move_to_wiki, wiki_node_url
from wechat import WeChatFetchError, fetch_article


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a WeChat MP article into a Feishu wiki docx.")
    parser.add_argument("--url", required=True, help="WeChat article URL (mp.weixin.qq.com/s/...)")
    parser.add_argument("--config", required=True, help="Path to config.json")
    parser.add_argument("--wiki-space", help="Override wiki_space_id from config")
    parser.add_argument("--parent-node", help="Override parent_node_token from config")
    parser.add_argument("--keep-temp", action="store_true", help="Keep intermediate docx and image files")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(
            json.dumps(
                {
                    "error": "config_missing",
                    "message": f"Config file not found: {config_path}. "
                    "See references/setup.md to create it.",
                },
                ensure_ascii=False,
            )
        )
        return 2
    config = json.loads(config_path.read_text(encoding="utf-8"))
    space_id = args.wiki_space or config.get("wiki_space_id")
    parent_node = args.parent_node or config.get("parent_node_token") or None
    identity = config.get("lark_identity", "user")
    if not space_id or space_id.startswith("请填入"):
        print(
            json.dumps(
                {"error": "config_incomplete", "message": "wiki_space_id is not set in config."},
                ensure_ascii=False,
            )
        )
        return 2

    workdir = Path(tempfile.mkdtemp(prefix="wechat2lark_"))
    try:
        try:
            article = fetch_article(args.url, workdir / "images")
        except WeChatFetchError as e:
            print(json.dumps({"error": "fetch_failed", "message": str(e)}, ensure_ascii=False))
            return 3

        date_str = (article.publish_date or datetime.now()).strftime("%Y%m%d")
        safe_title = _safe_filename(article.title)
        doc_name = f"{safe_title}_{date_str}"
        docx_path = workdir / f"{doc_name}.docx"
        build_docx(article, docx_path)

        try:
            docx_token = import_docx(docx_path, doc_name, identity=identity)
            move_result = move_to_wiki(docx_token, space_id, parent_node, identity=identity)
        except LarkError as e:
            print(json.dumps({"error": "lark_failed", "message": str(e)}, ensure_ascii=False))
            return 4

        node_token = _extract_node_token(move_result)
        result = {
            "title": article.title,
            "doc_name": doc_name,
            "docx_token": docx_token,
            "wiki_node_token": node_token,
            "wiki_url": wiki_node_url(space_id, node_token) if node_token else "",
            "image_count": len(article.images),
        }
        print(json.dumps(result, ensure_ascii=False))
        return 0
    finally:
        if not args.keep_temp:
            shutil.rmtree(workdir, ignore_errors=True)
        else:
            print(f"[debug] kept workdir: {workdir}", file=sys.stderr)


def _safe_filename(name: str) -> str:
    name = re.sub(r"[\\/:*?\"<>|]", "_", name).strip()
    name = re.sub(r"\s+", " ", name)
    return name[:80] if len(name) > 80 else name


def _extract_node_token(move_result: dict) -> str:
    data = move_result.get("data", move_result)
    for key in ("node", "wiki_node"):
        node = data.get(key) if isinstance(data, dict) else None
        if isinstance(node, dict):
            tok = node.get("node_token") or node.get("token")
            if tok:
                return tok
    return data.get("node_token", "") if isinstance(data, dict) else ""


if __name__ == "__main__":
    sys.exit(main())

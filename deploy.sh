#!/usr/bin/env bash
# 把本仓库里的每个 skill（含 SKILL.md 的顶层目录）部署到 ~/.claude/skills/
# 仓库是唯一真相源；skills 目录是生成产物，请勿手改。
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$HOME/.claude/skills"
mkdir -p "$DEST"
for d in "$REPO"/*/; do
  name="$(basename "$d")"
  [ -f "${d}SKILL.md" ] || continue   # 只部署真正的 skill 目录
  rm -rf "$DEST/$name"
  cp -r "$d" "$DEST/$name"
  echo "deployed $name -> $DEST/$name"
done

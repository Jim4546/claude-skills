#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_output.py —— article-origin-finder 发布前的固定格式机械关卡。

在 `lark-cli docs +create` 之前（或写本地 .md 之前）必须跑一遍：

    python scripts/check_output.py content.xml
    python scripts/check_output.py 名称_YYYYMMDD.md          # 降级本地同样适用
    python scripts/check_output.py content.xml --no-original  # "无英文原文"分支

校验固定三层结构：① 原文信息 → ② 英文原文全文(verbatim) → ③ 中英核对。
ok:false 时退出码非 0；按 problems 修正后重跑，直到 ok:true 才能发布。

它挡的是结构性偏离（第二层被换成摘要 / 被外移 / 三层不齐 / 拆成多篇），
不判断语义忠实度——忠实度由 trace-origin.md 的人工分级负责。
"""

import sys
import re
import json
import argparse

# —— 阈值集中在此，按需调整（短推文等极短原文可调小 MIN_*）——
MIN_LAYER2_CHARS = 200       # 第二层剥标签后正文最少字符数
MIN_LAYER2_BLOCKS = 3        # 第二层最少段落/列表块数
TITLE_DATE_RE = re.compile(r"_\d{8}\s*$")   # 标题须以 _YYYYMMDD 结尾

# 三层标题的识别子串（对 XML <h1>… 与 Markdown # … 都用子串匹配）
H1 = "一、原文信息"
H2 = "二、英文原文全文"
H3 = "三、与中文文章的核对"

# 第二层里出现这些 = 把全文外移了（硬失败）
OFFLOAD_PAT = re.compile(
    r"(全文见|完整(全文|逐字稿)?见|见另一篇|见上(方|篇)|详见本地|本地文件|参见(链接|上方|另一)|另存|拆分到|见配套文档)"
)
# 第二层主体疑似被换成结论（软警告）
CONCLUSION_PAT = re.compile(r"(核对结论|总评|逐条(判定|比对)|判定档|忠实度结论)")


def strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"\s+", " ", s).strip()


def count_blocks(segment: str, is_md: bool) -> int:
    """数第二层里的内容块：XML 数 <p>/<li>/<tr>；MD 数非空非标题行。"""
    if is_md:
        n = 0
        for ln in segment.splitlines():
            t = ln.strip()
            if not t or t.startswith("#") or t.startswith("---"):
                continue
            n += 1
        return n
    return len(re.findall(r"<(p|li|tr)[ >]", segment))


def find_heading_pos(text: str, needle: str):
    """返回第一处“标题行里含 needle”的位置，找不到返回 -1。"""
    for m in re.finditer(re.escape(needle), text):
        # 行首到该位置，判断是不是标题行（XML <h1.. 或 MD #..）
        line_start = text.rfind("\n", 0, m.start()) + 1
        prefix = text[line_start:m.start()]
        if re.search(r"<h[12][\s>]", prefix) or re.match(r"\s*#{1,2}\s", prefix):
            return m.start()
    # 退一步：只要出现该子串也认（容忍标题写法差异），但排在标题判断之后
    p = text.find(needle)
    return p


def check(text: str, no_original: bool):
    problems, warnings = [], []
    is_md = bool(re.search(r"^\s*#\s", text, re.M)) and "<title>" not in text

    # —— 规则 1：标题唯一 + _YYYYMMDD ——
    titles = re.findall(r"<title>(.*?)</title>", text, re.S)
    if not is_md and "<title>" in text:
        if len(titles) != 1:
            problems.append(f"必须恰好一个 <title>，实际 {len(titles)} 个。")
        title_text = titles[0].strip() if titles else ""
    else:
        m = re.search(r"^\s*#\s+(.+)$", text, re.M)
        title_text = m.group(1).strip() if m else ""
        if not title_text:
            problems.append("缺少文档标题（XML 用 <title>，MD 用开头唯一一级标题）。")
    if title_text and not TITLE_DATE_RE.search(title_text):
        problems.append(f"标题须用『名称_YYYYMMDD』格式，结尾应为 _8位日期：当前『{title_text}』。")

    # —— 无英文原文分支：只要 ① + 结论，且不得有第二层“全文” ——
    if no_original:
        if find_heading_pos(text, H1) < 0:
            problems.append(f"缺少标题『{H1}』。")
        if find_heading_pos(text, H2) >= 0:
            problems.append(f"『无英文原文』模式下不得出现『{H2}』标题（防编造正文）。")
        has_concl = re.search(r"(结论|无英文原文|为何判定)", text)
        if not has_concl:
            problems.append("『无英文原文』模式须给出结论小节，说明为何判定无原文。")
        ok = not problems
        return {"ok": ok, "mode": "no-original",
                "problems": problems, "warnings": warnings}

    # —— 规则 2：三层齐全且顺序正确 ——
    p1 = find_heading_pos(text, H1)
    p2 = find_heading_pos(text, H2)
    p3 = find_heading_pos(text, H3)
    for name, pos in ((H1, p1), (H2, p2), (H3, p3)):
        if pos < 0:
            problems.append(f"缺少层标题『{name}』。三层必须齐全。")
    if p1 >= 0 and p2 >= 0 and p3 >= 0:
        if not (p1 < p2 < p3):
            problems.append("三层顺序必须为 ①原文信息 → ②英文原文全文 → ③中英核对。")

    # —— 规则 3 & 4：第二层有实质 verbatim 全文，且未被外移 ——
    if p2 >= 0 and p3 > p2:
        layer2 = text[p2:p3]
        # 去掉第二层自己的标题行
        layer2_body = re.sub(r"^.*?(\n)", "", layer2, count=1)
        body_txt = strip_tags(layer2_body)
        n_blocks = count_blocks(layer2_body, is_md)
        if len(body_txt) < MIN_LAYER2_CHARS:
            problems.append(
                f"第二层正文过短（{len(body_txt)} 字符 < {MIN_LAYER2_CHARS}）：第二层必须是英文原文逐字全文，"
                f"不可用摘要/结论/锚点摘录替代。")
        if n_blocks < MIN_LAYER2_BLOCKS:
            problems.append(
                f"第二层内容块过少（{n_blocks} < {MIN_LAYER2_BLOCKS}）：逐字全文应分段呈现。")
        if OFFLOAD_PAT.search(body_txt):
            problems.append(
                "第二层出现『全文见/见另一篇/见本地文件』等外移措辞：原文全文必须就地嵌入本篇，不得外移或拆分。")
        if CONCLUSION_PAT.search(body_txt) and len(body_txt) < MIN_LAYER2_CHARS * 4:
            warnings.append(
                "第二层疑似以『核对/结论/判定/总评』为主体——确认这里放的是英文原文逐字全文，而非核对内容。")

    ok = not problems
    return {"ok": ok, "mode": "full", "problems": problems, "warnings": warnings}


def main():
    ap = argparse.ArgumentParser(description="article-origin-finder 固定三层格式校验")
    ap.add_argument("path", help="content.xml 或 名称_YYYYMMDD.md")
    ap.add_argument("--no-original", action="store_true",
                    help="判定『无英文原文』分支：只校验 ①信息表 + 结论，禁止第二层全文")
    args = ap.parse_args()

    try:
        with open(args.path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        print(json.dumps({"ok": False, "problems": [f"读不到文件：{e}"]},
                         ensure_ascii=False, indent=2))
        sys.exit(2)

    result = check(text, args.no_original)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()

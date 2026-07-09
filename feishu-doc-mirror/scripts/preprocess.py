# -*- coding: utf-8 -*-
"""Turn fetched Feishu markdown + an image manifest into ordered build segments.

Usage:
  python preprocess.py --md raw/doc_content.md --manifest clone_manifest.json
                       [--source raw/source.json] [--date YYYYMMDD]
                       [--out-md clone_preprocessed.md] [--seg-dir seg] [--plan plan.json]

Does, in order:
  - <title> gets a _YYYYMMDD suffix (creation day) per naming convention
  - restore mid-word bold (\\*\\* -> **)
  - <cite doc-id=... title=...> -> [title](<source-tenant>/wiki/<doc-id>)
  - flatten any <grid>...</grid> into linear blocks (h#/p/@@IMG@@)
  - ![](.../file/TOKEN) and <img src="TOKEN"> -> @@IMG:TOKEN@@
  - split at @@IMG@@ into ordered text/img segments; write seg files + plan.json
"""
import argparse, json, re, datetime
from pathlib import Path

CITE_BASE = "https://www.feishu.cn"  # overridden from source.json host if available


def inline_to_md(s, keep_bold=True):
    s = re.sub(r'<cite\s+([^>]*?)\s*/?>(?:</cite>)?', _cite, s)
    if keep_bold:
        s = re.sub(r'<b>(.*?)</b>', r'**\1**', s, flags=re.S)
    else:
        s = re.sub(r'<b>(.*?)</b>', r'\1', s, flags=re.S)
    s = re.sub(r'<a\s+href="([^"]+)">(.*?)</a>', r'[\2](\1)', s, flags=re.S)
    s = re.sub(r'<[^>]+>', '', s)
    return s.strip()


def _cite(m):
    attrs = m.group(1)
    did = re.search(r'doc-id="([^"]+)"', attrs)
    title = re.search(r'title="([^"]*)"', attrs)
    t = (title.group(1) if title else "链接").strip()
    return f"[{t}]({CITE_BASE}/wiki/{did.group(1)})" if did else t


def flatten_grid(grid_xml):
    out = []
    for m in re.finditer(
            r'<(h[1-6])>(.*?)</\1>'
            r'|<p>(.*?)</p>'
            r'|<img[^>]*\bsrc="([A-Za-z0-9]+)"[^>]*/?>', grid_xml, re.S):
        if m.group(1):
            lvl = int(m.group(1)[1])
            out.append("#" * lvl + " " + inline_to_md(m.group(2), keep_bold=False))
        elif m.group(3) is not None:
            txt = inline_to_md(m.group(3))
            if txt:
                out.append(txt)
        elif m.group(4):
            out.append(f"@@IMG:{m.group(4)}@@")
    return "\n\n".join(out)


def main():
    global CITE_BASE
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", default="raw/doc_content.md")
    ap.add_argument("--manifest", default="clone_manifest.json")
    ap.add_argument("--source", default="raw/source.json")
    ap.add_argument("--date", default=datetime.date.today().strftime("%Y%m%d"))
    ap.add_argument("--out-md", default="clone_preprocessed.md")
    ap.add_argument("--seg-dir", default="seg")
    ap.add_argument("--plan", default="plan.json")
    a = ap.parse_args()

    # cite base = source tenant host
    sp = Path(a.source)
    if sp.exists():
        src = json.loads(sp.read_text(encoding="utf-8"))
        url = src.get("docx_url") or ""
        hm = re.match(r'(https?://[^/]+)', url)
        if hm:
            CITE_BASE = hm.group(1)

    s = Path(a.md).read_text(encoding="utf-8")

    # title + _DATE
    def title_sub(m):
        return f"<title>{m.group(1).strip()}_{a.date}</title>"
    s = re.sub(r'<title>\s*(.*?)\s*</title>', title_sub, s, count=1, flags=re.S)

    # restore mid-word bold
    s = s.replace(r"\*\*", "**")

    # flatten grids (line-wise; grids are emitted on one line by the fetch)
    out_lines = []
    for ln in s.split("\n"):
        if ln.lstrip().startswith("<grid>"):
            out_lines.append(flatten_grid(ln))
        else:
            out_lines.append(ln)
    s = "\n".join(out_lines)

    # remaining standalone cites
    s = re.sub(r'<cite\s+([^>]*?)\s*/?>(?:</cite>)?', _cite, s)

    # images -> markers
    s = re.sub(r'!\[\]\(https://feishu\.cn/file/([A-Za-z0-9]+)\)', r'@@IMG:\1@@', s)
    s = re.sub(r'<img[^>]*\bsrc="([A-Za-z0-9]+)"[^>]*/?>', r'@@IMG:\1@@', s)

    Path(a.out_md).write_text(s, encoding="utf-8")

    # split into ordered segments
    parts = re.split(r'@@IMG:([A-Za-z0-9]+)@@', s)
    seg_dir = Path(a.seg_dir)
    seg_dir.mkdir(exist_ok=True)
    man = json.loads(Path(a.manifest).read_text(encoding="utf-8")) if Path(a.manifest).exists() else {}
    img_dir = Path(a.manifest).parent / "clone_imgs"
    # manifest filenames are relative to clone_imgs/
    segments, ti = [], 0
    for i, p in enumerate(parts):
        if i % 2 == 0:
            txt = p.strip("\n")
            if txt.strip():
                fn = seg_dir / f"seg_{ti:03d}.md"
                fn.write_text(txt + "\n", encoding="utf-8")
                segments.append({"type": "text", "file": str(fn).replace("\\", "/")})
                ti += 1
        else:
            token = p
            imgfile = f"clone_imgs/{man.get(token, token + '.png')}"
            segments.append({"type": "img", "token": token, "imgfile": imgfile})

    Path(a.plan).write_text(json.dumps(segments, ensure_ascii=False, indent=2),
                            encoding="utf-8")
    n_text = sum(1 for x in segments if x["type"] == "text")
    n_img = sum(1 for x in segments if x["type"] == "img")
    missing = [x["token"] for x in segments
               if x["type"] == "img" and not Path(x["imgfile"]).exists()]
    print(f"segments: {len(segments)}  text={n_text}  img={n_img}")
    if missing:
        print("WARNING: missing local image files for tokens:", missing)
        print("  (run capture_images.py first, or these images will be skipped)")


if __name__ == "__main__":
    main()

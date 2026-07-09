# -*- coding: utf-8 -*-
"""Resolve a Feishu/Lark share or community URL down to the real docx + metadata.

Usage:
  python resolve_source.py <url> [--out raw]

Handles:
  - community/prompts card page -> parse inline _ROUTER_DATA, read promptData.worksLink
  - /docx/<token> or /wiki/<token> share link -> use directly

Writes <out>/source.json:
  {input_url, kind, docx_url, docx_token, doc_type, title, worksLink, author}
"""
import argparse, json, re, sys, urllib.request
from pathlib import Path

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
DOC_RE = re.compile(r'https?://[^/]+/(docx|wiki)/([A-Za-z0-9]+)')


def fetch_html(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def balanced(s, start):
    depth = 0
    for i in range(start, len(s)):
        if s[i] == '{':
            depth += 1
        elif s[i] == '}':
            depth -= 1
            if depth == 0:
                return s[start:i + 1]
    return None


def deep_find(o, key):
    if isinstance(o, dict):
        if key in o:
            return o[key]
        for v in o.values():
            r = deep_find(v, key)
            if r is not None:
                return r
    elif isinstance(o, list):
        for v in o:
            r = deep_find(v, key)
            if r is not None:
                return r
    return None


def from_router_data(html):
    m = re.search(r'_ROUTER_DATA\s*=\s*\{', html)
    if not m:
        return None
    js = balanced(html, m.end() - 1)
    if not js:
        return None
    try:
        data = json.loads(js)
    except Exception:
        return None
    pd = deep_find(data, "promptData")
    return pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--out", default="raw")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    res = {"input_url": a.url, "kind": None, "docx_url": None, "docx_token": None,
           "doc_type": None, "title": None, "worksLink": None, "author": None}

    direct = DOC_RE.search(a.url)
    if "/community/" in a.url:
        res["kind"] = "community-card"
        html = fetch_html(a.url)
        pd = from_router_data(html)
        if not pd:
            print("ERROR: could not parse _ROUTER_DATA/promptData from card page",
                  file=sys.stderr)
            sys.exit(2)
        res["title"] = (pd.get("name") or "").strip()
        res["worksLink"] = pd.get("worksLink")
        au = pd.get("author") or {}
        res["author"] = au.get("name")
        link = res["worksLink"] or ""
        dm = DOC_RE.search(link)
        if not dm:
            print("ERROR: worksLink is not a /docx//wiki/ URL:", link, file=sys.stderr)
            sys.exit(3)
        res["docx_url"], res["doc_type"], res["docx_token"] = link, dm.group(1), dm.group(2)
    elif direct:
        res["kind"] = "direct-doc"
        res["docx_url"] = a.url
        res["doc_type"] = direct.group(1)
        res["docx_token"] = direct.group(2)
    else:
        print("ERROR: unrecognized URL (expect community/prompts or /docx//wiki/)",
              file=sys.stderr)
        sys.exit(4)

    (out / "source.json").write_text(json.dumps(res, ensure_ascii=False, indent=2),
                                     encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=2))
    print(f"\n-> docx_token={res['docx_token']} doc_type={res['doc_type']}")
    if res["doc_type"] == "wiki":
        print("NOTE: wiki token — docs +fetch accepts the /wiki/ URL directly; "
              "for native export use `lark-cli drive +inspect` to unwrap to a docx token.")


if __name__ == "__main__":
    main()

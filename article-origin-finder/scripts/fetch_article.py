# -*- coding: utf-8 -*-
"""Fetch an article's full text with a local headless browser, bypassing the
anti-scrape walls (WeChat "环境异常" CAPTCHA, datacenter-IP blocks, soft paywalls)
that defeat server-side fetchers.

Why this exists: server-side fetchers (WebFetch, reader proxies) hit WeChat / X /
many CN sites from datacenter IPs and get a verification page, HTTP 451, or a login
wall. A real local browser uses YOUR residential IP + a genuine Chrome fingerprint
and renders the page like a normal visit. This is the step that actually worked.

Output is ALWAYS written to a UTF-8 JSON file (never printed), because the Windows
console is GBK and chokes on Chinese / emoji (see feishu-doc-mirror/references/pitfalls.md).

Usage:
  python fetch_article.py <url> [--out article.json] [--wait 4000] [--keep-open]

Exit codes:
  0  ok (check the JSON's "blocked" flag — true means we still hit a wall)
  2  navigation failed entirely
"""
import argparse, io, json, re, sys
from playwright.sync_api import sync_playwright

# A real, current Windows Chrome UA. No webdriver tells. Works cross-platform too.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

# Signatures that mean "we got a wall, not the article".
BLOCK_MARKERS = [
    "环境异常", "完成验证", "去验证", "请输入验证",
    "Something went wrong", "Log in", "Sign in to continue",
    "Enable JavaScript", "captcha", "verify you are human",
]

# Content selectors: WeChat first, then generic long-form containers.
CONTENT_SELECTORS = ["#js_content", "#js_article", "article", "main",
                     ".rich_media_content", ".article-content", "#content", ".post"]

# Where authors stash the "original source" pointer.
SOURCE_HINT_RE = re.compile(
    r"(原文链接|原文地址|来源[:：]|编译自|译自|source[:：]?|original[:：]?)", re.I)
URL_RE = re.compile(r"https?://[^\s　\"'）)\]】>]+")


def first_text(page, selectors):
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el:
                t = el.inner_text().strip()
                if t and len(t) > 200:
                    return t, sel
        except Exception:
            pass
    return "", None


def grab_meta(page, selectors):
    out = {}
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el:
                t = el.inner_text().strip()
                if t:
                    out[sel] = t
        except Exception:
            pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--out", default="article.json")
    ap.add_argument("--wait", type=int, default=4000,
                    help="ms to wait after load for JS-rendered content")
    ap.add_argument("--headful", action="store_true",
                    help="show the browser window (helps if a wall needs a human)")
    a = ap.parse_args()

    result = {
        "url": a.url, "final_url": None, "title": None, "author": None,
        "body": "", "body_selector": None, "source_links": [],
        "source_context": [], "blocked": False, "block_reason": None,
    }

    with sync_playwright() as p:
        b = p.chromium.launch(headless=not a.headful)
        ctx = b.new_context(
            user_agent=UA, locale="zh-CN",
            viewport={"width": 1280, "height": 1800},
        )
        page = ctx.new_page()
        try:
            page.goto(a.url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            result["block_reason"] = "navigation failed: %s" % e
            _write(a.out, result)
            print("nav-failed -> %s" % a.out)
            sys.exit(2)

        page.wait_for_timeout(a.wait)
        # nudge lazy content
        for _ in range(6):
            page.mouse.wheel(0, 1600)
            page.wait_for_timeout(400)

        result["final_url"] = page.url
        result["title"] = page.title()

        body, sel = first_text(page, CONTENT_SELECTORS)
        if not body:
            body = page.inner_text("body")
            sel = "body"
        result["body"], result["body_selector"] = body, sel

        # author / byline best-effort (WeChat + common patterns)
        meta = grab_meta(page, ["#js_name", "#js_author_name", ".rich_media_meta_list",
                                ".author", "[rel=author]", ".byline"])
        if meta:
            result["author"] = next(iter(meta.values()))

        # detect a wall
        full = (result["title"] or "") + "\n" + body
        for m in BLOCK_MARKERS:
            if m.lower() in full.lower() and len(body) < 800:
                result["blocked"] = True
                result["block_reason"] = "matched marker: %s" % m
                break

        # self-reported source links: lines near a source hint, plus all x/twitter
        # /medium/substack/nytimes-style external links in the body.
        for line in body.splitlines():
            if SOURCE_HINT_RE.search(line):
                result["source_context"].append(line.strip())
        links = URL_RE.findall(body)
        # prioritise likely-original-source domains
        for u in links:
            u = u.rstrip(".,;")
            if u not in result["source_links"]:
                result["source_links"].append(u)

        b.close()

    _write(a.out, result)
    status = "BLOCKED" if result["blocked"] else "ok"
    print("%s | title=%r | body=%d chars | %d source links -> %s"
          % (status, (result["title"] or "")[:60], len(result["body"]),
             len(result["source_links"]), a.out))


def _write(path, obj):
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()

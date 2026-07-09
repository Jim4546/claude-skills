"""Scrape a SPA: render with Playwright, extract sections + inline links.

Usage:
  python scrape.py <URL>
      --section-selector .Collapsible
      --title-selector .Collapsible__trigger
      --content-selector .Collapsible__contentInner
      [--out raw]
      [--no-fetch-links]            # default: only scrape inline links into raw, don't visit them

If your SPA uses a different structure, swap the three selectors. Each section
must be findable as one DOM node, with a child node holding the title and
another child node holding the body HTML.
"""
import argparse
import asyncio
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

NAV_TIMEOUT_MS = 30000
SETTLE_MS = 1500


async def render_root(page, url):
    await page.goto(url, wait_until="networkidle", timeout=NAV_TIMEOUT_MS)
    await page.wait_for_timeout(SETTLE_MS)
    return await page.content()


def extract_sections(html: str, section_sel: str, title_sel: str, content_sel: str):
    soup = BeautifulSoup(html, "lxml")
    sections = []
    for sec in soup.select(section_sel):
        t = sec.select_one(title_sel)
        c = sec.select_one(content_sel)
        if not t or not c:
            continue
        title = t.get_text(" ", strip=True)
        links = []
        for a in c.find_all("a"):
            href = (a.get("href") or "").strip()
            text = a.get_text(" ", strip=True)
            if not href or href.startswith(("#", "javascript:")):
                continue
            links.append({"text": text, "url": href})
        sections.append({"title": title, "html": str(c), "links": links})
    return sections


def find_page_title(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "lxml")
    pt = soup.select_one(".page-title")
    st = soup.select_one(".subtitle")
    title = pt.get_text(" ", strip=True) if pt else (soup.title.get_text(" ", strip=True) if soup.title else "")
    subtitle = st.get_text(" ", strip=True) if st else ""
    return title, subtitle


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--section-selector", default=".Collapsible")
    ap.add_argument("--title-selector", default=".Collapsible__trigger")
    ap.add_argument("--content-selector", default=".Collapsible__contentInner")
    ap.add_argument("--out", default="raw")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            ignore_https_errors=True,
        )
        page = await ctx.new_page()
        html = await render_root(page, args.url)
        (out_dir / "root.html").write_text(html, encoding="utf-8")
        await browser.close()

    sections = extract_sections(html, args.section_selector, args.title_selector, args.content_selector)
    title, subtitle = find_page_title(html)

    data = {
        "root_url": args.url,
        "page_title": title,
        "subtitle": subtitle,
        "sections": sections,
    }
    (out_dir / "index.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    total_links = sum(len(s["links"]) for s in sections)
    print(f"Wrote {out_dir/'index.json'}: {len(sections)} sections, {total_links} inline links")


if __name__ == "__main__":
    asyncio.run(main())

"""Probe a SPA page: render it and dump structure to help pick selectors.

Usage: python probe.py <URL> [--out OUT_DIR]

Outputs:
  OUT_DIR/probe_root.html       — fully rendered HTML snapshot
  OUT_DIR/probe_anchors.json    — every <a> with text + href
  OUT_DIR/probe_classes.json    — class-name frequency (helps pick selectors)
  stdout: title, top class names, total anchors
"""
import argparse
import asyncio
import json
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


async def probe(url: str, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context()
        page = await ctx.new_page()
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(2500)

        html = await page.content()
        (out_dir / "probe_root.html").write_text(html, encoding="utf-8")

        anchors = await page.evaluate(
            """() => Array.from(document.querySelectorAll('a')).map(a => ({
                text: (a.innerText || '').trim().slice(0, 120),
                href: a.getAttribute('href') || ''
            }))"""
        )
        (out_dir / "probe_anchors.json").write_text(
            json.dumps(anchors, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        soup = BeautifulSoup(html, "lxml")
        classes: Counter = Counter()
        for el in (soup.body or soup).find_all(True):
            for c in (el.get("class") or []):
                classes[c] += 1
        top = classes.most_common(40)
        (out_dir / "probe_classes.json").write_text(
            json.dumps(top, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        print(f"Title: {await page.title()}")
        print(f"Anchors: {len(anchors)}")
        print(f"Body chars: {len((soup.body or soup).get_text())}")
        print("Top classes (count, name):")
        for c, n in top:
            print(f"  {n:5}  .{c}")
        await browser.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--out", default="raw", help="output dir (default: raw)")
    args = ap.parse_args()
    asyncio.run(probe(args.url, Path(args.out)))


if __name__ == "__main__":
    main()

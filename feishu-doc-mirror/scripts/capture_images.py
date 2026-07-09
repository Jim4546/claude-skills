# -*- coding: utf-8 -*-
"""Recover every image of a publicly-shared Feishu docx by rendering it headless
and intercepting image bytes, then map them to the document-ordered image tokens.

Usage:
  python capture_images.py <doc_url> --md raw/doc_content.md [--out clone_imgs]
                           [--min-blob 500000] [--manifest clone_manifest.json]

Why this exists: media-download is 403 cross-tenant, but a shared doc renders for
anonymous viewers. Cover/banner/grid images load via .../stream/download/v2/cover/
<TOKEN>/ (token in URL → exact map); body images surface as opaque blobs in scroll
order at full resolution (~1MB) → mapped to remaining tokens in order.

Outputs <out>/<token>.png for every content image + a {token: filename} manifest.
Exits 3 (dumping all blobs) if it cannot map every token — never ships a partial set.
"""
import argparse, json, re, hashlib, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

TOKEN_RE = re.compile(r"/stream/download/v2/cover/([A-Za-z0-9]+)/")
SKIP = ("feishu-static", "static-resource", "file_list_load_error", "sprite",
        "image_size=72x72")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")


def ordered_tokens(md):
    """All image tokens in document order: markdown images + inline <img src>."""
    toks = []
    for m in re.finditer(r'!\[\]\(https://feishu\.cn/file/([A-Za-z0-9]+)\)'
                         r'|<img[^>]*\bsrc="([A-Za-z0-9]+)"', md):
        toks.append(m.group(1) or m.group(2))
    return toks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("doc_url")
    ap.add_argument("--md", default="raw/doc_content.md")
    ap.add_argument("--out", default="clone_imgs")
    ap.add_argument("--manifest", default="clone_manifest.json")
    ap.add_argument("--min-blob", type=int, default=500000)
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    md = Path(a.md).read_text(encoding="utf-8")
    tokens = ordered_tokens(md)
    print("content image tokens:", len(tokens))
    if not tokens:
        Path(a.manifest).write_text("{}", encoding="utf-8")
        print("no images in document — nothing to capture")
        return

    token_imgs, blob_seq, seen = {}, [], set()

    def on_response(resp):
        try:
            url, ct = resp.url, resp.headers.get("content-type", "")
            if not ct.startswith("image/") or any(s in url for s in SKIP):
                return
            body = resp.body()
            if len(body) < 20000:
                return
            h = hashlib.md5(body).hexdigest()
            if h in seen:
                return
            seen.add(h)
            m = TOKEN_RE.search(url)
            if m:
                token_imgs[m.group(1)] = body
            else:
                blob_seq.append(body)
        except Exception:
            pass

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width": 1400, "height": 1000}, user_agent=UA)
        page = ctx.new_page()
        page.on("response", on_response)
        page.goto(a.doc_url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(4000)
        page.evaluate(
            """() => {let best=null,bh=0;document.querySelectorAll('*').forEach(el=>{
              const o=getComputedStyle(el).overflowY;
              if((o==='auto'||o==='scroll')&&el.scrollHeight>el.clientHeight+200){
                if(el.scrollHeight>bh){bh=el.scrollHeight;best=el;}}});
              if(best)best.setAttribute('data-scrollme','1');}""")
        H = page.evaluate("()=>{const e=document.querySelector('[data-scrollme]');return e?e.scrollHeight:0;}")
        if not H:  # fallback: wheel-scroll the window/content
            for _ in range(120):
                page.mouse.move(700, 500)
                page.mouse.wheel(0, 1200)
                page.wait_for_timeout(400)
        else:
            y = 0
            while y < H + 3000:
                page.evaluate(f"()=>{{const e=document.querySelector('[data-scrollme]');if(e)e.scrollTo(0,{y});}}")
                page.wait_for_timeout(450)
                y += 350
                H = page.evaluate("()=>{const e=document.querySelector('[data-scrollme]');return e?e.scrollHeight:0;}")
        page.wait_for_timeout(3000)
        b.close()

    hires = [x for x in blob_seq if len(x) > a.min_blob]
    manifest, bi, unmapped = {}, 0, []
    for t in tokens:
        if t in token_imgs:
            (out / f"{t}.png").write_bytes(token_imgs[t])
            manifest[t] = f"{t}.png"
        elif bi < len(hires):
            (out / f"{t}.png").write_bytes(hires[bi])
            manifest[t] = f"{t}.png"
            bi += 1
        else:
            unmapped.append(t)

    Path(a.manifest).write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                encoding="utf-8")
    exact = sum(1 for t in tokens if t in token_imgs)
    print(f"mapped {len(manifest)}/{len(tokens)} "
          f"(token-exact={exact}, blobs-used={bi}/{len(hires)}, total-blobs={len(blob_seq)})")
    if unmapped:
        for i, x in enumerate(blob_seq):
            (out / f"_blob_{i:03d}.png").write_bytes(x)
        print("UNMAPPED tokens:", unmapped,
              "\n-> dumped all blobs to", out, "for manual matching", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()

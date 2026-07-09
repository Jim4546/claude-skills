---
name: feishu-doc-mirror
description: Mirror (clone) a shared Feishu/Lark document or community article into the user's own Feishu space as a faithful, editable docx — text, structure, and all images. Use when the user gives a feishu.cn/community/prompts card URL or a shared /docx//wiki/ link and asks to download / save / clone / mirror (下载/保存/克隆/镜像/搬运) the full article, especially when the source has copy/export disabled. Requires lark-cli (authed) + Python/Playwright for image recovery.
---

# feishu-doc-mirror

Turn a shared Feishu article into a faithful copy in the user's own Feishu space:

1. resolve the real document behind the URL (a community card only *links* to the body)
2. clone it — natively if allowed, otherwise rebuild text + recovered images
3. verify the copy matches the source (image / heading / callout / text counts)

Title follows the user convention `名称_YYYYMMDD`.

## When to invoke

User provides a Feishu URL — `feishu.cn/community/prompts?id=...`, or a shared
`*.feishu.cn/docx/<token>` / `/wiki/<token>` — and wants the **whole article
saved/cloned/mirrored into their own Feishu cloud doc**. Especially relevant
when native "创建副本"/export is greyed out (author disabled copy).

If the user instead wants a local Word/PDF of a generic JS site, use
`spa-to-pdf`. If they only want to *read* a Feishu doc, use `lark-doc` directly.

## Prerequisites

- `lark-cli` installed and `auth login` done (user identity). See `lark-shared`.
- Python 3.10+ with Playwright (only the image-recovery step needs it):
  ```powershell
  pip install playwright
  playwright install chromium
  ```
- The image-recovery step requires the source doc to be **anonymously viewable**
  (community-shared docs are). If it needs login, that step fails — fall back to
  a text-only mirror and tell the user images couldn't be fetched.

All scripts live in `scripts/`. Run them from one scratch working dir (e.g.
`mirror_work/`); they read/write `raw/`, `clone_imgs/`, `seg/`, `plan.json`.

## Strategy ladder (cheapest first)

### 0. Resolve the source
```powershell
python scripts/resolve_source.py "<input_url>" --out raw
```
Writes `raw/source.json` = `{kind, docx_token, docx_url, title, worksLink, author}`.
- community card → parses embedded `_ROUTER_DATA`, reads `promptData.worksLink`
- `/docx//wiki/` link → uses it directly

### 1. Fetch the body text (read API — usually works even when export is blocked)
```powershell
lark-cli docs +fetch --api-version v2 --doc "<docx_token>" --doc-format markdown --as user --json |
  Out-File -Encoding utf8 raw/doc_raw.json
python -c "import json; d=json.load(open('raw/doc_raw.json',encoding='utf-8-sig')); open('raw/doc_content.md','w',encoding='utf-8').write(d['data']['document']['content'])"
```
> lark-cli JSON output carries a UTF-8 **BOM** → always parse with `utf-8-sig`.

### 2. Try the native clone first (best fidelity, one round-trip)
```powershell
lark-cli drive +export --token "<docx_token>" --doc-type docx --file-extension docx --output-dir . --overwrite --as user --json
# if ok -> lark-cli drive +import ...  (into the user's space) -> DONE
```
If this returns `no permission` (code **1069902**) or 403, the author disabled
copy/export → go to step 3 (rebuild). Do **not** keep retrying.

### 3. Rebuild (text + recovered images)
```powershell
# 3a. recover every image by rendering the public doc and intercepting bytes
python scripts/capture_images.py "<docx_url>" --md raw/doc_content.md --out clone_imgs
# 3b. turn fetched markdown + images into ordered build segments
python scripts/preprocess.py --md raw/doc_content.md --manifest clone_manifest.json --source raw/source.json
# 3c. linear build: create + append text + insert images (order preserved)
python scripts/build.py --plan plan.json
```
`build.py` prints the new clone's `document_id` + URL and records progress in
`build_state.json` (re-run to resume after a mid-way failure).

### 4. Verify before reporting success
```powershell
python scripts/verify.py --clone "<new_token>" --source-md raw/doc_content.md
```
Confirms the clone's image / callout / table / code-block / heading counts match
the source and spot-checks Chinese phrases for `?` corruption. **Always run it.**

## Important behaviors

- **`--content @file`, never piped stdin.** PowerShell 5.1 pipes to native exes
  as GBK and silently turns 中文/emoji into `?`. All create/append calls read
  content from a UTF-8 file via `--content @path`. (build.py already does this.)
- **`--doc-format markdown` faithfully renders Feishu's hybrid markdown** —
  `<callout>` (emoji kept), tables, code fences, blockquotes, bold, links all
  survive a fetch→create round-trip. Verified.
- **media-insert is append-only.** Positioning is achieved by building the doc
  top-to-bottom (linear append), so every text/image lands at the end in order.
  Do not try to move blocks afterward.
- **Images are protected** — `media-download` returns 403 cross-tenant. They are
  recovered only by rendering the public page and intercepting the image bytes.
- **Don't recursively expand linked sub-docs** (`<cite>` wiki refs) — keep them
  as hyperlinks to the originals, like `spa-to-pdf`'s "inline links only" rule.
- **Title** gets the `_YYYYMMDD` suffix (creation day) per the user convention.

For the full list of edge cases and *why* each fix exists, read
`references/pitfalls.md` before changing any script — several "obvious"
simplifications reintroduce bugs already fixed.

## Cleanup

Throwaway/verification docs are deleted with
`lark-cli drive +delete --file-token <token> --type docx --as user --yes`
(note: `--file-token`, not `--token`; docx delete is high-risk-write, needs `--yes`).

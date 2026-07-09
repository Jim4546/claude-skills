# Pitfalls & design rationale

Read this before changing any script. Each entry is a real bug/limitation hit
while building the first mirror; the "obvious" simplification usually
reintroduces it.

## 1. The article is two layers — the page is just a card

`feishu.cn/community/prompts?id=...` returns an SSR HTML shell whose real data
sits in an inline `window._ROUTER_DATA = {...}` script. The visible body is **not
there** — only a 99-char summary. The full article is a *separate* docx at
`promptData.worksLink` (e.g. `https://aiawaken.feishu.cn/docx/<token>`).

- Parse: find `_ROUTER_DATA = {`, then **brace-balance** to slice the JSON object
  (regex won't match nested braces). Walk it recursively for `promptData`.
- `resolve_source.py` does this and also handles direct `/docx//wiki/` links.

## 2. Read works; export / copy / media-download are often blocked

Cross-tenant, or when the author disables copy:

- `lark-cli drive +export` → `{"code":1069902,"message":"no permission"}`
- `lark-cli docs +media-download --token ...` → HTTP **403**
- But `lark-cli docs +fetch --doc-format markdown` returns the **full body**.

So: always try native export→import first (best fidelity), but expect to fall
back to rebuild. Don't loop-retry a 1069902 — it's a permission wall, not a blip.

## 3. PowerShell stdin corrupts non-ASCII → use `--content @file`

PowerShell 5.1 encodes pipeline bytes to native exes as **GBK**, silently turning
中文/emoji into `?`. Verified: piping markdown into `lark-cli docs +create
--content -` produced a doc full of `????` and dropped the callout's 🎁 (Feishu
defaulted it to 💡).

**Fix:** write content to a UTF-8 file and pass `--content @path`. lark-cli reads
the file as UTF-8. `build.py` always uses `@file`. Never pipe content via stdin
on Windows.

## 4. Feishu docx scrolls an inner container, not the window

`window.scrollTo` is a no-op — `document.body.scrollHeight` stays at viewport
height (~1000). Body images never enter the viewport, so they never lazy-load.

**Fix:** find the element with `overflowY: auto|scroll` and the largest
`scrollHeight` (in practice `.bear-web-x-container`) and scroll **that** element
in small steps with waits. `capture_images.py` detects it generically.

## 5. Cover images carry a token; body images arrive as opaque blobs

Two delivery paths for images, discovered by intercepting responses:

- Above-the-fold (cover/banner/grid) images load from
  `…/stream/download/v2/cover/<TOKEN>/?…` — the **token is in the URL**, so they
  map exactly.
- Body/chapter images are decoded client-side and surface as `blob:` responses
  with **no token**. They come in **scroll order** and at full resolution
  (~1 MB) alongside ~130 KB low-res previews.

**Mapping (heuristic):** take the document-ordered token list from the fetched
markdown; for each token use the exact-token capture if present, else assign the
next unused **high-res blob** (`> ~500 KB`) in scroll order. Then **validate
count == number of content images**; on mismatch, dump all blobs and stop for
manual review — never silently ship a partial set.

## 6. `--doc-format markdown` faithfully round-trips Feishu's hybrid markdown

Feishu's "markdown" embeds XML (`<callout>`, `<grid>`, `<cite>`). A create from
that content renders real blocks: callout (emoji preserved), tables, code fences
(```), blockquotes, bold, links — all verified intact. So rebuilding via markdown
append is safe; you do **not** need to hand-translate to XML.

## 7. media-insert is append-only → build top-to-bottom (linear append)

`docs +media-insert` can only add an image at the **end** of the doc. Rather than
insert-then-`block_move_after` (fragile, needs block-id bookkeeping), build the
whole doc in document order: create the first text segment, then alternately
`append` text and `media-insert` images. Everything lands at the end in order —
positions are correct for free.

## 8. Fidelity touch-ups during preprocessing

- `\*\*` in fetched markdown is escaped mid-word bold → restore to `**` so it
  renders bold (Feishu handles `**…**` around CJK).
- `<cite doc-id="X" title="T">` → `[T](<source-tenant>/wiki/X)` — keep as a link
  to the original; do **not** recursively inline the linked sub-doc.
- `<grid>…</grid>` → flatten columns to linear blocks (h4 / p / `@@IMG@@`); a
  2-column layout isn't worth reconstructing for a faithful-enough mirror.

## 9. Output encoding gotchas

- lark-cli `--json` output is UTF-8 **with BOM** → parse with `encoding="utf-8-sig"`.
- The Windows console is GBK and **crashes on emoji `print()`**. Write results to
  a file and read them; don't `print()` content that may contain emoji.

## 10. drive +delete flag name

Deleting throwaway/verification docs uses `--file-token` (NOT `--token`):
```
lark-cli drive +delete --file-token <token> --type docx --as user --yes
```
docx delete is `high-risk-write` → requires `--yes`.

## 11. Naming convention

Per the user's standing rule, the clone title gets a `_YYYYMMDD` suffix
(creation day): `名称_YYYYMMDD`. `preprocess.py` applies it to `<title>`.

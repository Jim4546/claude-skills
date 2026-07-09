---
name: spa-to-pdf
description: Scrape a single-page-app (SPA) website with multiple collapsible/sectioned content blocks and produce a Word document plus a PDF with an auto-filled table of contents and clickable inline hyperlinks. Use when the user provides a SPA URL (hash routes, JS-rendered content) and asks for a Word/PDF export of all sections. Requires Windows + Microsoft Word for the final PDF step.
---

# spa-to-pdf

Turn a JS-rendered SPA page (e.g. `https://example.com/#/some/section`) into:

1. `output.docx` — cover, bilingual TOC, every section as Heading 1 with original paragraphs/lists/hyperlinks preserved
2. `output.pdf` — same, with TOC fields filled and heading bookmarks

## When to invoke

Trigger this skill when the user asks to "scrape / save / export / archive a
website's content into Word or PDF" AND the site looks like a SPA (URL has
`#/...`, content is dynamic, or `curl` returns an empty shell). For plain
static HTML pages, a simpler `WebFetch + pandoc` pipeline is enough — skip
this skill there.

## Prerequisites

- Python 3.10+
- Windows + Microsoft Word installed (needed for PDF + TOC fields)
- One-time setup:
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install playwright python-docx beautifulsoup4 lxml pywin32
  playwright install chromium
  ```

## Pipeline

Run the four scripts in `scripts/` in order. They share a working dir (defaults
to `./raw/` for intermediate files and `./output.docx`, `./output.pdf` for
products). All scripts take CLI args — see `--help` on each.

### 1. Probe (optional but recommended)

```powershell
python scripts/probe.py <URL>
```

Dumps the rendered HTML and the top CSS class names. Use the output to pick
selectors for step 2. If the page is a typical Collapsible-based site (e.g.
World Scholar's Cup themes), the defaults already work.

### 2. Scrape

```powershell
python scripts/scrape.py <URL> `
    --section-selector .Collapsible `
    --title-selector .Collapsible__trigger `
    --content-selector .Collapsible__contentInner
```

Writes `raw/index.json` with `{root_url, page_title, subtitle, sections: [{title, html, links}]}`.

### 3. Build Word

```powershell
python scripts/build_doc.py --in raw/index.json --out output.docx
```

### 4. Verify

```powershell
python scripts/verify.py --in raw/index.json --docx output.docx
```

Exits 0 if every section's character count, hyperlink count, and word set
roughly matches the source HTML. If not, the script prints what's missing
per section. **Always run this before showing the doc to the user.**

### 5. Export PDF

```powershell
python scripts/to_pdf.py output.docx output.pdf
```

Opens Word, updates TOC fields + bookmarks, exports PDF, closes Word.

## Important behaviors

- **Inline links only.** Do NOT visit each outbound link and append its
  content — the source page already places the links inline with context;
  duplicating the targets bloats the doc and adds noise.
- **No `add_page_break()`.** Use `paragraph_format.page_break_before = True`
  on Heading 1 — manual page breaks cause trailing blank pages when content
  happens to fill a page.
- **TOC page title must NOT be Heading 1.** Otherwise the TOC contains itself.
  Use a plain styled paragraph (see `build_doc.py`).
- **Always run `verify.py` before reporting success.** It catches missing
  nested lists, dropped runs, and character-encoding bugs that aren't
  visible at a glance.

For the full list of edge cases and *why* each fix exists, read
`references/pitfalls.md`. Read it before changing any of the scripts —
several of the "obvious" simplifications will reintroduce bugs we already
fixed.

## Cross-platform note

The PDF step depends on `pywin32` and Microsoft Word. On macOS this can be
ported to AppleScript / `appscript`; on Linux, use LibreOffice headless with
a TOC-update macro. PRs welcome.

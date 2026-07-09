# Pitfalls and design decisions

This list exists because every item below was a real bug we hit, with the
fix that made it go away. Read this before changing the scripts.

## SPA hash routing renders empty for static fetchers

**Symptom:** `WebFetch` / `curl` returns a near-empty `<body>` because the
content is rendered by JS after the page loads.

**Fix:** Use Playwright with `wait_until="networkidle"` plus an additional
small settle delay (≈1.5s). Wait for a known selector (e.g. `.Collapsible`)
to be sure the SPA finished its first render before reading `page.content()`.

## Non-standard nested `<ul>` (sibling of `<li>`, not inside it)

**Symptom:** Sub-bullets vanish from the docx. Source HTML looks like:

```html
<ul>
  <li>main item</li>
  <li>main item</li>
  <ul>                  <!-- nested ul as a sibling of <li>, NOT wrapped in one -->
    <li>sub item</li>
  </ul>
  <li>main item</li>
</ul>
```

**Fix:** When rendering a `<ul>`/`<ol>`, iterate **all Tag children**, not just
direct `<li>`. If a child is `<ul>`/`<ol>`, recurse into it with deeper indent.
See `_render_list` in `build_doc.py`.

## XML-illegal control characters in scraped text

**Symptom:** `python-docx` writes fail with
`ValueError: All strings must be XML compatible: Unicode or ASCII, no NULL
bytes or control characters` when scraping certain news/blog pages.

**Fix:** Strip `[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]` (allow `\t`, `\n`, `\r`)
from every string before passing it to docx. See `clean()` in `build_doc.py`.

## `add_page_break()` produces extra blank pages

**Symptom:** A trailing blank page appears after some sections, when the
content happens to fill the previous page exactly.

**Fix:** Don't insert manual page breaks. Set
`paragraph_format.page_break_before = True` on the section's Heading 1
paragraph (skipping the first section so the doc doesn't start with a blank
page). Each section begins on a fresh page, and there's no trailing waste.

## PDF table of contents is blank

**Symptom:** `docx2pdf` (or any "open and export" tool) produces a PDF where
the TOC field is unfilled — the page just shows the title.

**Why:** Word writes the TOC field but doesn't *update* it until you press F9
or open the file interactively. `docx2pdf` doesn't trigger an update.

**Fix:** Use `pywin32` directly:
```python
for story in doc.StoryRanges:
    story.Fields.Update()
for toc in doc.TablesOfContents:
    toc.Update()
doc.Save()                # required — without this the export ignores the new TOC
doc.ExportAsFixedFormat(..., CreateBookmarks=1, ...)
```
See `to_pdf.py`.

## TOC contains itself

**Symptom:** The TOC's first entry is "目录 / Table of Contents → page 2",
which points at its own page.

**Why:** The TOC heading was styled as Heading 1, and the TOC field includes
all H1-H3 by default.

**Fix:** Use a plain styled paragraph (large bold, with explicit fonts) for
the TOC page title — NOT a Heading style. See the TOC block in `build_doc.py`.

## Visually inconsistent Chinese/English font sizes

**Symptom:** Heading like "目录 / Table of Contents" looks like `目` and `录`
are different sizes — Chinese characters are using a different fallback font
from Latin characters, and that font renders at a different visual weight at
the same point size.

**Fix:** Explicitly set both `w:ascii` and `w:eastAsia` on the run's
`w:rFonts`:
```python
rFonts.set(qn("w:ascii"), "Calibri")
rFonts.set(qn("w:hAnsi"), "Calibri")
rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
rFonts.set(qn("w:cs"), "Calibri")
```
See `set_run_fonts()` in `build_doc.py`. Apply this to any prominent run that
mixes Chinese and Latin glyphs.

## Don't include "fetched-link-target content" as an appendix

**Anti-feature:** It's tempting to also visit every outbound link in each
section and append the target page's body text as an appendix. **Don't.**

**Why:** The source page already shows the link in context — the linked text
is the meaningful anchor. Appending target content:
- Inflates the PDF from ~75KB to ~600KB+ for typical pages
- Adds noise from cookie banners, related-article rails, paywalls
- Forces the reader past 20+ pages of low-value text before reaching the
  next section

Keep links as clickable inline hyperlinks. If the user truly wants the
appendix, ask before adding it.

## Always verify before declaring success

A docx that *opens* is not a docx that's *correct*. Run `verify.py` after
every build: it diffs the source HTML's word set, char count, and link count
against the docx, per section. This is how the original run caught the
missing nested lists — visually the doc looked fine, but verify.py would
have flagged 60+ words missing per affected section.

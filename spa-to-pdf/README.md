# spa-to-pdf

A [Claude Code](https://claude.com/claude-code) skill that scrapes a JS-rendered
single-page-app (SPA) website and produces a polished Word document and PDF
with a clickable table of contents and inline hyperlinks preserved.

Built to handle the kinds of details that make these tools fail in practice:
SPA hash routing, non-standard nested HTML lists, Word's TOC field never
auto-updating, Chinese/English font fallback inconsistency, and more. See
[`references/pitfalls.md`](references/pitfalls.md) for the full list.

## Install

```powershell
# Clone into your Claude Code skills directory
git clone https://github.com/<you>/spa-to-pdf.git "$env:USERPROFILE\.claude\skills\spa-to-pdf"

# One-time Python deps
cd "$env:USERPROFILE\.claude\skills\spa-to-pdf"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

Claude Code auto-discovers skills under `~/.claude/skills/` on startup.

## Use

In Claude Code, ask:

> 把 `https://example.com/#/some-page` 上的所有章节整理成 Word 和 PDF

Claude will invoke this skill automatically. You can also run the scripts
directly:

```powershell
python scripts/probe.py <URL>                              # inspect structure
python scripts/scrape.py <URL>                             # → raw/index.json
python scripts/build_doc.py --in raw/index.json --out a.docx
python scripts/verify.py --in raw/index.json --docx a.docx # quality gate
python scripts/to_pdf.py a.docx a.pdf                      # → PDF with TOC
```

## Requirements

- Windows + Microsoft Word installed (for the final PDF + TOC step)
- Python 3.10+

The PDF step relies on Word automation via `pywin32`. Ports to LibreOffice /
macOS Word are welcome — see the cross-platform note in `SKILL.md`.

## License

MIT — see [LICENSE](LICENSE).

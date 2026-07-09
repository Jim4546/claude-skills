"""Convert docx → PDF on Windows using Word COM, with TOC fields updated.

Usage: python to_pdf.py <input.docx> [output.pdf]

Why not docx2pdf? docx2pdf calls Word but does NOT update TOC fields, so
the table of contents in the PDF comes out empty. Here we:
  1. Open docx in Word
  2. Update every field in every story (this fills the TOC)
  3. Update each TablesOfContents object
  4. Save (required before ExportAsFixedFormat picks up changes)
  5. ExportAsFixedFormat → PDF with heading bookmarks
"""
import argparse
import sys
from pathlib import Path

import win32com.client as win32  # type: ignore[import-not-found]


def convert(docx_path: Path, pdf_path: Path):
    word = win32.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        doc = word.Documents.Open(str(docx_path.resolve()), ReadOnly=False)
        for story in doc.StoryRanges:
            story.Fields.Update()
        for toc in doc.TablesOfContents:
            toc.Update()
        doc.Save()
        doc.ExportAsFixedFormat(
            OutputFileName=str(pdf_path.resolve()),
            ExportFormat=17,        # wdExportFormatPDF
            OpenAfterExport=False,
            OptimizeFor=0,           # wdExportOptimizeForPrint
            Range=0,                 # wdExportAllDocument
            Item=0,                  # wdExportDocumentContent
            IncludeDocProps=True,
            KeepIRM=True,
            CreateBookmarks=1,       # wdExportCreateHeadingBookmarks
            DocStructureTags=True,
            BitmapMissingFonts=True,
            UseISO19005_1=False,
        )
        doc.Close(SaveChanges=False)
    finally:
        word.Quit()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("pdf", nargs="?", default=None)
    args = ap.parse_args()

    docx_path = Path(args.docx)
    if not docx_path.exists():
        print(f"Not found: {docx_path}", file=sys.stderr)
        sys.exit(1)
    pdf_path = Path(args.pdf) if args.pdf else docx_path.with_suffix(".pdf")
    convert(docx_path, pdf_path)
    print(f"Wrote {pdf_path}")


if __name__ == "__main__":
    main()

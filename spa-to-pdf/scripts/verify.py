"""Cross-check the generated docx against the source raw/index.json.

Reports per-section character counts, hyperlink counts, and the set of words
that appear in the source HTML but not in the docx (a signal that something
was dropped during rendering).

Usage: python verify.py [--in raw/index.json] [--docx output.docx]
"""
import argparse
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup
from docx import Document
from docx.oxml.ns import qn


def normalize(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("—", "-").replace("–", "-")
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()


def words(s: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", normalize(s)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="raw/index.json")
    ap.add_argument("--docx", default="output.docx")
    args = ap.parse_args()

    data = json.loads(Path(args.inp).read_text(encoding="utf-8"))

    src_sections = {}
    src_links = {}
    for sec in data["sections"]:
        soup = BeautifulSoup(sec["html"], "lxml")
        src_sections[sec["title"]] = soup.get_text(" ", strip=True)
        src_links[sec["title"]] = [a.get("href", "") for a in soup.find_all("a") if a.get("href")]

    doc = Document(args.docx)
    rels = doc.part.rels

    def has_rel(rid):
        return bool(rels.get(rid))

    section_text = {}
    section_link_count = {}
    current = None
    for p in doc.paragraphs:
        style = p.style.name if p.style else ""
        if style == "Heading 1":
            current = p.text.strip()
            section_text[current] = []
            section_link_count[current] = 0
            continue
        if current is None:
            continue
        section_text[current].append(p.text)
        for h in p._p.findall(qn("w:hyperlink")):
            rid = h.get(qn("r:id"))
            if rid and has_rel(rid):
                section_link_count[current] += 1

    issues = 0
    print(f"Sections: source={len(src_sections)} docx={len(section_text)}")
    for title, src_text in src_sections.items():
        if title not in section_text:
            print(f"  MISSING in docx: {title}")
            issues += 1
            continue
        doc_text = " ".join(section_text[title])
        only_src = words(src_text) - words(doc_text)
        link_diff = len(src_links[title]) - section_link_count[title]
        ok = link_diff == 0 and len(only_src) <= 5
        marker = "OK" if ok else ">>"
        print(f"  {marker} {title}: chars src={len(src_text)} doc={len(doc_text)} "
              f"links src={len(src_links[title])} doc={section_link_count[title]} "
              f"only-in-src={len(only_src)}")
        if not ok:
            issues += 1
            if only_src:
                print(f"      sample missing words: {sorted(only_src)[:15]}")
    print(f"\nSections with issues: {issues}")
    raise SystemExit(0 if issues == 0 else 1)


if __name__ == "__main__":
    main()

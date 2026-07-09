# -*- coding: utf-8 -*-
"""Verify a clone against its source: structural counts + Chinese-integrity spot
checks. Run before reporting success.

Usage:
  python verify.py --clone <clone_token> --source-md raw/doc_content.md

Compares image / callout / table / code-block / heading counts (source vs clone)
and confirms a sample of source Chinese phrases survived intact in the clone.
"""
import argparse, json, re, subprocess, sys, tempfile, os
from pathlib import Path


def fetch_xml(token):
    r = subprocess.run(
        f'lark-cli docs +fetch --api-version v2 --doc {token} '
        f'--doc-format xml --as user --json',
        shell=True, capture_output=True, text=True, encoding="utf-8")
    out = (r.stdout or "")
    i = out.find("{")
    if i < 0:
        print("FETCH FAILED:", out[:400], r.stderr[:400], file=sys.stderr)
        sys.exit(2)
    # lark-cli JSON may carry a BOM; lstrip it
    j = json.loads(out[i:].lstrip("﻿"))
    return j["data"]["document"]["content"]


def ordered_tokens(md):
    return re.findall(r'!\[\]\(https://feishu\.cn/file/[A-Za-z0-9]+\)'
                      r'|<img[^>]*\bsrc="[A-Za-z0-9]+"', md)


def source_counts(md):
    return {
        "images": len(ordered_tokens(md)),
        "callouts": md.count("<callout"),
        "headings": len(re.findall(r'(?m)^#{1,6} ', md)) + len(re.findall(r'<h[1-6]>', md)),
        "code": md.count("```") // 2 + len(re.findall(r'<pre', md)),
        "tables": len(re.findall(r'(?m)^\s*\|?(?:\s*:?-{2,}:?\s*\|)+\s*$', md))
                  + len(re.findall(r'<table', md)),
    }


def clone_counts(xml):
    return {
        "images": len(re.findall(r'<img\b', xml)),
        "callouts": len(re.findall(r'<callout', xml)),
        "headings": len(re.findall(r'<h[1-6]\b', xml)),
        "code": len(re.findall(r'<pre\b', xml)),
        "tables": len(re.findall(r'<table\b', xml)),
    }


def sample_phrases(md, n=6, length=8):
    # distinctive long CJK runs spread across the document
    runs = re.findall(r'[一-鿿]{%d,}' % length, md)
    if not runs:
        return []
    step = max(1, len(runs) // n)
    picks = [runs[i][:length] for i in range(0, len(runs), step)][:n]
    return picks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clone", required=True, help="clone document token")
    ap.add_argument("--source-md", default="raw/doc_content.md")
    a = ap.parse_args()

    md = Path(a.source_md).read_text(encoding="utf-8")
    xml = fetch_xml(a.clone)

    sc, cc = source_counts(md), clone_counts(xml)
    print(f"{'metric':10} {'source':>8} {'clone':>8}  status")
    ok = True
    for k in ("images", "callouts", "tables", "code", "headings"):
        good = cc[k] >= sc[k]  # clone may add the flattened-grid heading; never fewer
        ok = ok and good
        print(f"{k:10} {sc[k]:>8} {cc[k]:>8}  {'OK' if good else 'MISMATCH'}")

    print("\nChinese integrity spot-check:")
    bad = []
    for ph in sample_phrases(md):
        present = ph in xml
        print(f"  {'OK ' if present else 'MISS'} {ph}")
        if not present:
            bad.append(ph)
    if bad:
        ok = False
        print("  -> some phrases missing — possible encoding corruption or dropped text")

    if "?" * 4 in xml:
        ok = False
        print("\nWARNING: found runs of '????' in clone — GBK corruption (use --content @file)")

    print("\nRESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Linear build driver: create the clone doc, then append text / insert images in
document order. Everything lands at the end → order is preserved without moves.

Usage:
  python build.py [--plan plan.json] [--state build_state.json]
                  [--parent-token <fld/wiki token> | --parent-position my_library]

Re-run to resume after a mid-way failure (progress is recorded in --state).
Content is passed via --content @file (NEVER piped stdin) to avoid PowerShell GBK
corruption of Chinese/emoji. Run this from the scratch working dir so the relative
image paths in plan.json resolve.
"""
import argparse, json, subprocess, sys, time, os
from pathlib import Path

V = "--api-version v2"
AS = "--as user --json"


def run(cmd):
    r = subprocess.run(cmd, shell=True, cwd=os.getcwd(),
                       capture_output=True, text=True, encoding="utf-8")
    out = (r.stdout or "").strip()
    try:
        return json.loads(out)
    except Exception:
        i = out.find("{")
        if i >= 0:
            try:
                return json.loads(out[i:])
            except Exception:
                pass
        return {"ok": False, "raw": out[:800], "stderr": (r.stderr or "")[:800]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default="plan.json")
    ap.add_argument("--state", default="build_state.json")
    ap.add_argument("--parent-token", default=None)
    ap.add_argument("--parent-position", default=None)
    a = ap.parse_args()

    plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    state_f = Path(a.state)
    state = json.loads(state_f.read_text(encoding="utf-8")) if state_f.exists() \
        else {"doc_id": None, "done": -1}

    def save():
        state_f.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    parent = ""
    if a.parent_token:
        parent = f"--parent-token {a.parent_token}"
    elif a.parent_position:
        parent = f"--parent-position {a.parent_position}"

    # 1) create from first segment (must be text, carries the <title>)
    if not state["doc_id"]:
        seg0 = plan[0]
        if seg0["type"] != "text":
            print("ERROR: first segment is not text (no title to create from)", file=sys.stderr)
            sys.exit(1)
        j = run(f'lark-cli docs +create {V} --doc-format markdown '
                f'--content @{seg0["file"]} {parent} {AS}')
        if not j.get("ok"):
            print("CREATE FAILED:", json.dumps(j, ensure_ascii=False)[:600])
            sys.exit(1)
        doc = j["data"]["document"]
        state.update(doc_id=doc["document_id"], url=doc.get("url", ""), done=0)
        save()
        print("CREATED:", state["doc_id"], state.get("url"))

    doc = state["doc_id"]

    # 2) iterate remaining segments
    for idx in range(state["done"] + 1, len(plan)):
        seg = plan[idx]
        if seg["type"] == "text":
            j = run(f'lark-cli docs +update {V} --doc {doc} --command append '
                    f'--doc-format markdown --content @{seg["file"]} {AS}')
        else:
            if not Path(seg["imgfile"]).exists():
                print(f"[{idx}] SKIP missing image {seg['imgfile']}")
                state["done"] = idx
                save()
                continue
            j = run(f'lark-cli docs +media-insert --doc {doc} '
                    f'--file {seg["imgfile"]} --align center {AS}')
        label = (seg.get("file") or seg.get("token") or "")[:42]
        ok = j.get("ok")
        print(f"[{idx}/{len(plan)-1}] {seg['type']:5} {label:42} -> ok={ok}")
        if not ok:
            print("STEP FAILED:", json.dumps(j, ensure_ascii=False)[:600])
            save()
            sys.exit(2)
        state["done"] = idx
        save()
        time.sleep(0.3)

    print("DONE. doc:", doc, state.get("url"))


if __name__ == "__main__":
    main()

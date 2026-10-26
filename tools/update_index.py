#!/usr/bin/env python3
"""Rebuild data/index.json from data/editions/*.json; keep newest KEEP."""
import json, os, glob

KEEP = 14
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ed_dir = os.path.join(root, "data", "editions")
files = sorted(glob.glob(os.path.join(ed_dir, "*.json")), reverse=True)

entries = []
for i, f in enumerate(files):
    if i >= KEEP:
        os.remove(f)
        print("removed", os.path.basename(f))
        continue
    d = json.load(open(f, encoding="utf-8"))
    entries.append({
        "id": d["id"],
        "file": "data/editions/" + os.path.basename(f),
        "generated_at": d["generated_at"],
        "count": len(d.get("stories", [])),
    })

json.dump({"editions": entries}, open(os.path.join(root, "data", "index.json"),
          "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("index:", ", ".join(e["id"] for e in entries))

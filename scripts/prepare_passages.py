# scripts/prepare_passages.py
import json, glob
from pathlib import Path

INDIR = Path("data/trusted_docs")
OUTFILE = Path("data/passages.txt")

passages = []
for f in sorted(INDIR.glob("*.json")):
    j = json.load(open(f, encoding="utf8"))
    t = j.get("type")
    if t == "news":
        txt = f"{j.get('ticker','')}: {j.get('headline','')} - {j.get('summary','')}"
    elif t == "quote":
        q = j.get("quote",{})
        txt = f"{j.get('ticker')}: price={q.get('c')} open={q.get('o')} high={q.get('h')} low={q.get('l')}"
    else:
        txt = json.dumps(j)
    passages.append(txt.strip())

OUTFILE.parent.mkdir(parents=True, exist_ok=True)
OUTFILE.write_text("\n\n".join(passages), encoding="utf8")
print("Wrote", OUTFILE, "with", len(passages), "passages")

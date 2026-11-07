"""Word count for the Kaggle Writeup (limit 1,500, title line excluded).

Prints three counts, strictest first:
  raw      every whitespace-separated token after the title line (markdown marks, URLs, table bars included)
  words    tokens with at least one letter or digit (drops bare |, -, >, ---, #)
  no-img   `words` without the image lines, which Kaggle replaces with gallery uploads
Usage: .venv/bin/python research/paper/v8_notes/scripts/wc_writeup.py [path]
"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import re
import sys

path = sys.argv[1] if len(sys.argv) > 1 else (_REPO + "/research/paper/v8/writeup.md")
lines = open(path, encoding="utf-8").read().split("\n")
assert lines[0].startswith("# "), "first line must be the title"
body = lines[1:]
raw = " ".join(body).split()
words = [t for t in raw if re.search(r"[0-9A-Za-zÀ-ÿ]", t)]
no_img = [t for t in " ".join(l for l in body if not l.lstrip().startswith("![")).split()
          if re.search(r"[0-9A-Za-zÀ-ÿ]", t)]
print(f"title: {lines[0][2:]}")
print(f"raw tokens {len(raw)}; words {len(words)}; words without image lines {len(no_img)}; limit 1500, margin {1500 - len(raw)} on raw")
for sec in re.split(r"\n(?=## )", "\n".join(body)):
    head = sec.strip().split("\n")[0][:40]
    print(f"  {head:42s} {len(sec.split()):5d}")

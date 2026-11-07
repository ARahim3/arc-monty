"""Word count of the writeup draft, the way a reader (or Kaggle's editor) would count rendered words.

Strips the HTML comment, markdown markup, table rules and link URLs; a word = a whitespace token containing a letter
or digit. Placeholders count as one word each (they become one number or link). Reports title+subtitle, body,
body without references, and the per-section split, so the 1,500-word limit can be checked under any reading.
Usage: python research/paper/scripts/wordcount.py [research/paper/draft.md]
"""
import re
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "research/paper/draft.md"
text = re.sub(r"<!--.*?-->", "", open(path).read(), flags=re.S)


def words(s):
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)          # [text](url) -> text
    s = re.sub(r"^\s*\|?[-:| ]+\|?\s*$", "", s, flags=re.M)  # table rules
    s = re.sub(r"[|*_`#>]", " ", s)
    return [w for w in s.split() if re.search(r"[A-Za-z0-9]", w)]


lines = text.strip().split("\n")
title = [l for l in lines if l.startswith("# ")][:1]
sub = [l for l in lines if l.startswith("*Subtitle:*")][:1]
body_lines = [l for l in lines if l not in title + sub]
body = "\n".join(body_lines)
refs_at = body.find("## References")
body_norefs = body[:refs_at] if refs_at >= 0 else body
print(f"title+subtitle: {len(words(chr(10).join(title + sub)))}")
print(f"body (all):     {len(words(body))}")
print(f"body w/o refs:  {len(words(body_norefs))}")
print(f"everything:     {len(words(text))}")
print("placeholders:", sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", text))))
sec, cur = {}, "front"
for l in body_lines:
    if l.startswith("## "):
        cur = l[3:].strip()
    sec[cur] = sec.get(cur, 0) + len(words(l))
for k, v in sec.items():
    print(f"  {v:4d}  {k}")

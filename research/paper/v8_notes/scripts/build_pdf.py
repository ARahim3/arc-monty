#!/usr/bin/env python
"""Build the paper PDF: Markdown -> Typst (pandoc) -> PDF (typst), A4, STIX Two 10 pt.

Usage: python build_pdf.py [--md research/paper/v8/paper.md] [--out research/paper/v8/paper.pdf]
Runs from the project root with the project venv: `.venv/bin/python research/paper/v8_notes/scripts/build_pdf.py`
(typst 0.15 and pymupdf were installed into .venv on 2026-11-07; pandoc 3.11 on PATH; STIX Two is a macOS system font).
The .typ is written next to the Markdown so `../figures/` paths resolve; typst root is research/paper.
Prints page count, the page of each main heading, and renders every page to PNG under v8_notes/pdf_pages/ for review.
"""
import argparse, pathlib, re, subprocess, sys
import typst, fitz

PREAMBLE = r'''
#set page(paper: "a4", margin: 2cm, numbering: "1")
#set text(font: "STIX Two Text", size: 10pt)
#set par(justify: true, spacing: 0.75em)
#set table(stroke: 0.4pt + luma(140), inset: 3.5pt)
#show table: set text(size: 8pt)
#show table: set par(justify: false)
#show heading.where(level: 1): it => { set text(size: 15pt); v(0.4em); it; v(0.5em) }
#show heading.where(level: 2): it => { set text(size: 12pt); v(0.6em); it; v(0.3em) }
#show heading.where(level: 3): it => { set text(size: 10.5pt); v(0.4em); it; v(0.2em) }
#show figure: set block(above: 1em, below: 1em)
#show figure.caption: set text(size: 9pt)
#show figure.caption: it => it.body
#show figure.where(kind: table): set block(breakable: true)
#show figure.where(kind: table): set figure(placement: none)
#show image: it => align(center, it)
#show link: set text(fill: rgb("#1a4f8a"))
#show raw.where(block: false): set text(size: 0.92em)
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--md', default='research/paper/v8/paper.md')
    ap.add_argument('--out', default=None)
    ap.add_argument('--no-pages', action='store_true')
    a = ap.parse_args()
    md = pathlib.Path(a.md).resolve()
    out = pathlib.Path(a.out).resolve() if a.out else md.with_suffix('.pdf')
    root = pathlib.Path('research/paper').resolve()
    body_typ = md.with_name(md.stem + '_body.typ')
    main_typ = md.with_name(md.stem + '.typ')
    subprocess.run(['pandoc', str(md), '-t', 'typst', '--columns=100000', '-o', str(body_typ)], check=True)
    text = body_typ.read_text()
    # pandoc turns a Markdown image into a block image; keep width to the text width
    text = text.replace('#box(image(', '#box(width: 100%, image(')
    body_typ.write_text(text)
    main_typ.write_text(PREAMBLE + f'\n#include "{body_typ.name}"\n')
    typst.compile(str(main_typ), output=str(out), root=str(root))
    doc = fitz.open(str(out))
    print(f'{out}: {len(doc)} pages')
    seen = set()
    for i, pg in enumerate(doc):
        for line in pg.get_text().splitlines():
            m = re.match(r'^(\d+\.\s+[A-Z].{3,60}|Appendix [A-Z]\..{0,60}|References|Abstract)$', line.strip())
            if m and m.group(0) not in seen:
                seen.add(m.group(0)); print(f'  p{i+1}: {m.group(0)}')
    if not a.no_pages:
        d = pathlib.Path('research/paper/v8_notes/pdf_pages'); d.mkdir(exist_ok=True)
        for f in d.glob('page_*.png'): f.unlink()
        for i, pg in enumerate(doc):
            pg.get_pixmap(dpi=70).save(str(d / f'page_{i+1:02d}.png'))
        print(f'  pages rendered to {d}/')

if __name__ == '__main__':
    main()

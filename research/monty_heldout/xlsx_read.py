"""Minimal stdlib .xlsx reader (treats the file as data). rows(path) -> {sheet name: list of rows}."""
import re
import xml.etree.ElementTree as ET
import zipfile

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}


def _col(ref):
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n - 1


def rows(path):
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            shared.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
    out = {}
    for s in wb.find("m:sheets", NS):
        target = rels[s.get("{%s}id" % NS["r"])]
        sheet = ET.fromstring(z.read("xl/" + target.lstrip("/").replace("xl/", "")))
        tab = []
        for row in sheet.find("m:sheetData", NS):
            vals = {}
            for c in row:
                v = c.find("m:v", NS)
                if v is None:
                    continue
                vals[_col(c.get("r"))] = shared[int(v.text)] if c.get("t") == "s" else v.text
            tab.append([vals.get(i) for i in range(max(vals) + 1)] if vals else [])
        out[s.get("name")] = tab
    return out

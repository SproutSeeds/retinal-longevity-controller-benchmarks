#!/usr/bin/env python3
"""Read the original CC BY human panel without modifying the source workbook."""
import argparse
import csv
import io
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def extract(path):
    with zipfile.ZipFile(path) as archive:
        strings = ["".join(node.itertext()) for node in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall("s:si", NS)]
        panels = []
        for name in archive.namelist():
            if not (name.startswith("xl/worksheets/sheet") and name.endswith(".xml")):
                continue
            cells = {}
            for node in ET.fromstring(archive.read(name)).findall(".//s:c", NS):
                value = node.find("s:v", NS)
                if value is not None:
                    if node.find("s:f", NS) is not None:
                        raise ValueError("Unexpected formula in source panel")
                    cells[node.attrib["r"]] = strings[int(value.text)] if node.get("t") == "s" else value.text
            if cells.get("A1") == "Gene(human)":
                genes = [(cell, value) for cell, value in cells.items() if cell.startswith("A") and cell[1:].isdigit() and cell != "A1"]
                genes.sort(key=lambda item: int(item[0][1:]))
                panels.append((name, genes))
    if len(panels) != 1 or len(panels[0][1]) != 125:
        raise ValueError("Expected one original 125-gene human panel")
    genes = panels[0][1]
    if len({gene for _, gene in genes}) != 125 or any(not gene or gene != gene.strip() for _, gene in genes):
        raise ValueError("Blank, duplicate or whitespace-altered reference gene")
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(["gene_symbol", "source_sheet_xml", "source_cell"])
    writer.writerows((gene, panels[0][0], cell) for cell, gene in genes)
    return buffer.getvalue()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = extract(args.source)
    args.output.write_text(value)
    print("Extracted exactly 125 unique human genes; source workbook unchanged.")

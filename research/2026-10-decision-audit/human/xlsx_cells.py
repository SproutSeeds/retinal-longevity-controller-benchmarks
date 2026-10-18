#!/usr/bin/env python3
"""Read source XLSX cells without changing files or evaluating formulas."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import posixpath
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

MAIN = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
NS = {'m': MAIN}
HERE = Path(__file__).resolve().parent


def read_workbook(path):
    with zipfile.ZipFile(path) as archive:
        shared = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            shared = [''.join(e.itertext()) for e in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
        rels = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        targets = {e.attrib['Id']: posixpath.normpath(posixpath.join('xl', e.attrib['Target']))
                   if not e.attrib['Target'].startswith('/') else e.attrib['Target'].lstrip('/') for e in rels}
        root = ET.fromstring(archive.read('xl/workbook.xml'))
        out = []
        for sheet in root.findall('m:sheets/m:sheet', NS):
            data = ET.fromstring(archive.read(targets[sheet.attrib['{' + REL + '}id']]))
            cells = []
            for c in data.findall('.//m:sheetData/m:row/m:c', NS):
                typ = c.attrib.get('t', 'n')
                raw = c.find('m:v', NS)
                formula = c.find('m:f', NS)
                if typ == 'inlineStr':
                    inline = c.find('m:is', NS)
                    value = ''.join(inline.itertext()) if inline is not None else ''
                elif raw is None or raw.text is None:
                    value = None
                elif typ == 's':
                    value = shared[int(raw.text)]
                elif typ == 'b':
                    value = raw.text == '1'
                elif typ == 'n':
                    value = float(raw.text)
                    if value.is_integer():
                        value = int(value)
                else:
                    value = raw.text
                cells.append({'cell': c.attrib['r'], 'type': typ, 'value': value,
                              'formula': formula.text if formula is not None else None})
            dim = data.find('m:dimension', NS)
            out.append({'sheet': sheet.attrib['name'], 'dimension': dim.attrib['ref'] if dim is not None else None,
                        'cells': cells})
        return out


def assert_freeze():
    bindings = {'human/' + name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                for name in ['reference-audit-contract.json', 'reference-inputs.json']}
    records = [json.loads(line) for line in (HERE.parent / 'FREEZES.jsonl').read_text().splitlines()]
    if not any(r.get('lane') == 'human' and r.get('files') == bindings
               and r.get('stage') == 'before_numeric_workbook_inspection' for r in records):
        raise ValueError('Matching pre-inspection human freeze is required')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--inspect', action='store_true')
    args = parser.parse_args()
    assert_freeze()
    inputs = json.loads((HERE / 'reference-inputs.json').read_text())
    inventory = []
    for source in inputs['sources']:
        if not source['id'].endswith('.xlsx'):
            continue
        path = args.cache / source['id']
        if hashlib.sha256(path.read_bytes()).hexdigest() != source['sha256']:
            raise ValueError('Source hash mismatch: ' + source['id'])
        for sheet in read_workbook(path):
            row = {'source': source['id'], 'sheet': sheet['sheet'], 'dimension': sheet['dimension'],
                   'nonempty_cells': sum(c['value'] is not None for c in sheet['cells']),
                   'numeric_cells': sum(c['type'] == 'n' and c['value'] is not None for c in sheet['cells']),
                   'formula_cells': sum(c['formula'] is not None for c in sheet['cells'])}
            inventory.append(row)
            if args.inspect:
                byrow = collections.defaultdict(list)
                for c in sheet['cells']:
                    if c['value'] is not None:
                        rn = int(''.join(filter(str.isdigit, c['cell'])))
                        byrow[rn].append((c['cell'], c['value'], c['formula']))
                print(row)
                for rn in sorted(byrow)[:6]:
                    print(byrow[rn][:14])
    (HERE / 'workbook-inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')


if __name__ == '__main__':
    main()

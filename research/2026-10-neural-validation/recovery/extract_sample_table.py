#!/usr/bin/env python3
"""Read SuppTable1 only; preserve coordinates and do not read outcome sheets."""
import hashlib
import json
from pathlib import Path
import argparse
import posixpath
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).parent
CACHE = Path('/tmp/cx004-neural-validation-2026-10-18')
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}


def main():
    path = CACHE / '43587_2024_594_MOESM2_ESM.xlsx'
    data = path.read_bytes()
    assert len(data) == 83405567
    assert hashlib.md5(data).hexdigest() == 'a78aada4da430056e95d44851c6ba3e8'
    with zipfile.ZipFile(path) as z:
        book = ET.fromstring(z.read('xl/workbook.xml'))
        sheets = [s for s in book.findall('s:sheets/s:sheet', NS) if s.attrib['name'] == 'SuppTable1']
        assert len(sheets) == 1
        rid = sheets[0].attrib['{' + NS['r'] + '}id']
        relationships = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        target = next(r.attrib['Target'] for r in relationships if r.attrib['Id'] == rid)
        sheet_path = posixpath.normpath(posixpath.join('xl', target))
        root = ET.fromstring(z.read(sheet_path))
        cells = []
        required_strings = set()
        for cell in root.findall('.//s:sheetData/s:row/s:c', NS):
            value = cell.find('s:v', NS)
            if value is not None:
                record = {'coordinate': cell.attrib['r'], 'type': cell.attrib.get('t', 'n'), 'value': value.text}
                cells.append(record)
                if record['type'] == 's':
                    required_strings.add(int(record['value']))
        strings = {}
        index = 0
        with z.open('xl/sharedStrings.xml') as handle:
            for _, element in ET.iterparse(handle, events=['end']):
                if element.tag == '{' + NS['s'] + '}si':
                    if index in required_strings:
                        strings[index] = ''.join(t.text or '' for t in element.iter('{' + NS['s'] + '}t'))
                    index += 1
                    element.clear()
        assert set(strings) == required_strings
        for cell in cells:
            if cell['type'] == 's':
                cell['value'] = strings[int(cell['value'])]
        result = {'claim_level': 'Verified', 'source_url': 'https://static-content.springer.com/esm/art%3A10.1038%2Fs43587-024-00594-3/MediaObjects/43587_2024_594_MOESM2_ESM.xlsx',
                  'source_size_bytes': len(data), 'source_md5': hashlib.md5(data).hexdigest(),
                  'source_sha256': hashlib.sha256(data).hexdigest(), 'sheet': 'SuppTable1',
                  'worksheet_xml_read': [sheet_path], 'other_worksheet_xml_read': False,
                  'shared_strings_decoded': 'Only indices referenced by SuppTable1 cells.',
                  'cells': cells}
    (HERE / 'supplementary-table1-cells.json').write_text(json.JSONEncoder(indent=2, sort_keys=True).encode(result) + '\n')
    for cell in cells:
        print(cell['coordinate'], cell['value'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, default=CACHE)
    args = parser.parse_args()
    CACHE = args.cache
    main()

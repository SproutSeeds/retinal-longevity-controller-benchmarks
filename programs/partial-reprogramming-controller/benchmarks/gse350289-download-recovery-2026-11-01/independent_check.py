#!/usr/bin/env python3
"""Independent scalar-cell census of the newly downloaded workbook."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import openpyxl

HERE = Path(__file__).resolve().parent


def main(cache):
    expected = json.loads((HERE / 'RESULTS.json').read_text())
    path = cache / 'GSE350289_metadata_individual_cells.xlsx'
    fingerprint = hashlib.sha256(path.read_bytes()).hexdigest()
    assert fingerprint == expected['current_workbook_sha256']
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=False)
    observed = []
    for sheet in workbook:
        columns = Counter()
        rows = 0
        ages = Counter()
        for cells in sheet.iter_rows():
            populated = False
            for i, cell in enumerate(cells):
                if cell.data_type == 'f':
                    raise ValueError('Unexpected source formula')
                value = cell.value
                if value is not None and value != '':
                    columns[openpyxl.utils.get_column_letter(i + 1)] += 1
                    populated = True
                    if i == 3:
                        ages[str(value)] += 1
            rows += populated
        observed.append({'sheet': sheet.title, 'nonempty_rows': rows, 'nonempty_cells_by_column': dict(columns), 'column_D_value_counts': dict(ages)})
    workbook.close()
    assert len(observed) == len(expected['sheets']) == 5
    for actual, pinned in zip(observed, expected['sheets']):
        for key, value in actual.items():
            assert value == pinned[key], (actual['sheet'], key)
    return {'schema': 'controller.independent-current-workbook-census/1', 'status': 'PASS', 'reader': 'openpyxl ' + openpyxl.__version__, 'source_sha256': fingerprint, 'current_workbook_reacquisition_verified': True, 'imports_primary_XML_reader': False, 'sheets_checked': len(observed), 'nonempty_nonREADME_cells': sum(sum(s['nonempty_cells_by_column'].values()) for s in observed if s['sheet'] != 'README'), 'sheets': observed, 'scope': 'The newly downloaded source workbook only; no experimental assignments or biological outcome admitted.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=HERE.parents[1] / '.data/gse350289-download-recovery-2026-11-01/admitted-workbook')
    parser.add_argument('--emit', type=Path)
    args = parser.parse_args()
    result = main(args.cache)
    output = json.JSONEncoder(indent=2, sort_keys=True).encode(result) + '\n'
    if args.emit:
        args.emit.write_text(output)
    print(output.strip())

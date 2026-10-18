#!/usr/bin/env python3
"""Extract reported reference ages; do not infer ages from expression."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import re
from pathlib import Path
from xlsx_cells import assert_freeze, read_workbook

HERE = Path(__file__).resolve().parent


def rows_from_sheet(sheet, header_row):
    byrow = collections.defaultdict(dict)
    for c in sheet['cells']:
        match = re.fullmatch(r'([A-Z]+)([0-9]+)', c['cell'])
        byrow[int(match[2])][match[1]] = c
    header = {col: c['value'] for col, c in byrow[header_row].items() if c['value'] is not None}
    if len(set(header.values())) != len(header):
        raise ValueError('Duplicate header in ' + sheet['sheet'])
    rows = []
    for rn in sorted(byrow):
        if rn <= header_row:
            continue
        values, coordinates, formulas = {}, {}, {}
        for col, label in header.items():
            cell = byrow[rn].get(col)
            values[label] = cell['value'] if cell else None
            coordinates[label] = col + str(rn)
            if cell and cell['formula'] is not None:
                formulas[label] = cell['formula']
        if any(v is not None for v in values.values()):
            rows.append({'row': rn, 'values': values, 'coordinates': coordinates, 'formulas': formulas})
    return rows


def exact_unique_lookup(rows, field):
    grouped = collections.defaultdict(list)
    for row in rows:
        value = row.get(field)
        if value is not None:
            grouped[value].append(row)
    return grouped


def join_reference(record, metadata):
    """Require an exact unique library key plus agreement of available fields."""
    val = record['values']
    sample = val.get('SampleID')
    if sample is None:
        return {'status': 'no_library_identifier'}
    matches = metadata.get(sample, [])
    if len(matches) != 1:
        return {'status': 'missing_library_identifier' if not matches else 'duplicate_library_identifier', 'matches': len(matches)}
    match = matches[0]
    comparisons = []
    fields = [('Line', 'donor_or_line'), ('Line_age', 'age_years'), ('Passage', 'passage')]
    for source, target in fields:
        if source in val and val[source] is not None:
            comparisons.append({'field': source, 'reference': val[source], 'geo': match.get(target), 'agrees': val[source] == match.get(target)})
    if val.get('Gene') is not None:
        aliases = {'BFP': 'mTagBFP2', 'NTg': 'WT'}
        # Literal agreement wins. Some GEO controls are labelled NTg and
        # others WT; canonicalizing only one side would reject valid NTg.
        expected = val['Gene'] if val['Gene'] == match.get('genotype') else aliases.get(val['Gene'], val['Gene'])
        comparisons.append({'field': 'Gene', 'reference': val['Gene'], 'geo': match.get('genotype'),
                            'alias_applied': expected != val['Gene'], 'agrees': expected == match.get('genotype')})
    if 'Dox' in val and val['Dox'] is not None:
        treatment = match.get('treatment', '')
        dose = re.search(r'Dox_(\d+)ng/mL', treatment)
        observed = int(dose[1]) if dose else (0 if treatment == 'NT' else None)
        comparisons.append({'field': 'Dox', 'reference': val['Dox'], 'geo': observed, 'agrees': val['Dox'] == observed})
    # A bare recycled S identifier without matching donor metadata is inadequate.
    enough_identity = any(x['field'] == 'Line' for x in comparisons) and len(comparisons) >= 3
    passed = bool(enough_identity and all(x['agrees'] for x in comparisons)
                  and match.get('matrix_column_present') is True)
    return {'status': 'verified_exact_library_and_metadata' if passed else 'identifier_only_or_metadata_conflict',
            'sample_id': match.get('sample_id'), 'matrix_column': match.get('matrix_column'),
            'matrix_column_present': match.get('matrix_column_present'), 'sequencing_batch': match.get('sequencing_batch'),
            'off_days_geo': match.get('off_days_geo'), 'on_days_geo': match.get('on_days_geo'),
            'checks': comparisons}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    assert_freeze()
    inputs = json.loads((HERE / 'reference-inputs.json').read_text())
    addendum = json.loads((HERE / 'reference-input-addendum.json').read_text())
    binding = addendum['join_manifest']
    if hashlib.sha256(args.manifest.read_bytes()).hexdigest() != binding['sha256']:
        raise ValueError('Changed bound sample manifest; see post-inspection input addendum')
    meta = json.loads(args.manifest.read_text())['samples']
    meta = [r for r in meta if r.get('accession') == 'GSE325735' and r.get('organism') == 'Homo sapiens']
    lookup = exact_unique_lookup(meta, 'library')
    specifications = {'srsf1-source-fig1.xlsx': {s: 1 for s in ['1c', '1d', '1e', '1f', '1g']},
                      'srsf1-source-fig3.xlsx': {'3a': 1}, 'srsf1-supplement4.xlsx': {'Predicted ages': 6}}
    results = []
    for filename, selected in specifications.items():
        binding = next(x for x in inputs['sources'] if x['id'] == filename)
        path = args.cache / filename
        if hashlib.sha256(path.read_bytes()).hexdigest() != binding['sha256']:
            raise ValueError('Changed workbook')
        for sheet in read_workbook(path):
            if sheet['sheet'] not in selected:
                continue
            for row in rows_from_sheet(sheet, selected[sheet['sheet']]):
                row.update(source=filename, sheet=sheet['sheet'], source_sha256=binding['sha256'])
                # Initial-screen and external-reference IDs are deliberately not guessed.
                row['join'] = join_reference(row, lookup)
                results.append(row)
    summary = []
    for filename, selected in specifications.items():
        for sheet in selected:
            group = [r for r in results if r['source'] == filename and r['sheet'] == sheet]
            summary.append({'source': filename, 'sheet': sheet, 'prediction_rows': len(group),
                            'joins': dict(sorted(collections.Counter(r['join']['status'] for r in group).items()))})
    result = {'schema_version': 1, 'claim': 'Verified extraction and exact-reference audit; reported ages are not independently replayed',
              'manifest_sha256': hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
              'join_input_binding': 'reference-input-addendum.json; declared after numerical workbook inspection',
              'scope': 'Initial screen, validation and external references; these files do not by themselves identify withdrawal predictions',
              'aliases': {'BFP': 'mTagBFP2', 'NTg': 'WT'}, 'summary': summary, 'reported_reference_rows': results}
    (HERE / 'reference-output-audit.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    for r in summary:
        print(r)


if __name__ == '__main__':
    main()

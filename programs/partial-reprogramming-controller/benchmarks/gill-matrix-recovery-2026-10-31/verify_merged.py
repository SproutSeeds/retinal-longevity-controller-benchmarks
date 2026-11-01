#!/usr/bin/env python3
"""Independently compare every recovered source cell with the merged cache."""
import argparse
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=HERE.parents[1] / '.data/gill-source-recovery-2026-10-31')
    parser.add_argument('--emit', type=Path)
    args = parser.parse_args()
    contract = json.loads((HERE / 'MATRIX_CONTRACT.json').read_text())
    merged_path = args.cache / 'gill-locus-aligned-log2-RPM.tsv.gz'
    key_fields = contract['locus_key_fields']
    key_for = lambda row: tuple(row[field] for field in key_fields)
    with gzip.open(merged_path, 'rt', newline='') as stream:
        reader = csv.DictReader(stream, delimiter='\t')
        merged_header = reader.fieldnames
        merged = {}
        for row in reader:
            key = key_for(row)
            if key in merged or None in row or any(value is None for value in row.values()):
                raise ValueError('Duplicate or malformed merged locus')
            merged[key] = row
    observed_columns, compared_values, sources = set(), 0, []
    for source in contract['sources']:
        path = args.cache / source['filename']
        if path.stat().st_size != source['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != source['sha256']:
            raise ValueError('Original source identity differs')
        seen, source_values = set(), 0
        with gzip.open(path, 'rt', newline='') as stream:
            reader = csv.DictReader(stream, delimiter='\t')
            annotation_columns = contract['annotation_columns']
            samples = reader.fieldnames[len(annotation_columns):]
            if observed_columns.intersection(samples):
                raise ValueError('Reused source expression column')
            observed_columns.update(samples)
            for row in reader:
                key = key_for(row)
                if key in seen or key not in merged or None in row or any(value is None for value in row.values()):
                    raise ValueError('Duplicate, unmatched or malformed source locus')
                seen.add(key)
                if any(row[column] != merged[key][column] for column in reader.fieldnames):
                    raise ValueError('A source annotation or numeric text value changed')
                if any(not math.isfinite(float(row[column])) for column in samples):
                    raise ValueError('Nonfinite original expression value')
                source_values += len(samples)
        if seen != set(merged):
            raise ValueError('Source and merged locus sets differ')
        compared_values += source_values
        sources.append({'source_id': source['source_id'], 'source_rows_compared': len(seen),
                        'source_expression_values_compared': source_values, 'original_sha256': source['sha256']})
    if merged_header != [*contract['annotation_columns'], *[label for source in contract['sources'] for label in _labels(args.cache / source['filename'], len(contract['annotation_columns']))]]:
        raise ValueError('Merged column order or labels differ from original source order')
    receipt = {'schema': 'gill.original-value-preservation/1', 'status': 'PASS',
               'method': 'Independent csv.DictReader comparison from each original row and named source column to the merged compound locus key; no import of recover.py.',
               'merged_sha256': hashlib.sha256(merged_path.read_bytes()).hexdigest(),
               'feature_rows_compared': len(merged), 'expression_columns_compared': len(observed_columns),
               'expression_values_compared': compared_values, 'changed_source_cells': 0,
               'sources': sources, 'scientific_joint_comparison': 'DEFERRED'}
    if args.emit:
        args.emit.write_text(json.JSONEncoder(indent=2).encode(receipt) + '\n', encoding='utf-8')
    print('PASS independent original-value preservation: %d rows; %d columns; %d finite source values; zero changed cells.' % (len(merged), len(observed_columns), compared_values))


def _labels(path, annotation_count):
    with gzip.open(path, 'rt', newline='') as stream:
        return next(csv.reader(stream, delimiter='\t'))[annotation_count:]


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Recover pinned Gill RNA matrices and align loci without inferring function."""
import argparse
from collections import Counter
import csv
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import tempfile
import urllib.request

HERE = Path(__file__).resolve().parent


def encode(value):
    return json.JSONEncoder(indent=2, ensure_ascii=False, allow_nan=False).encode(value) + '\n'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tsv(rows, fields):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, delimiter='\t', lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def validate_payload(data, source):
    if len(data) != source['bytes']:
        raise ValueError('Source byte length differs: ' + source['filename'])
    if hashlib.sha256(data).hexdigest() != source['sha256']:
        raise ValueError('Source hash differs: ' + source['filename'])
    # Validate the complete gzip stream, including its CRC, before retaining bytes.
    gzip.decompress(data)


def download(source, cache):
    destination = cache / source['filename']
    if destination.exists():
        validate_payload(destination.read_bytes(), source)
        return
    request = urllib.request.Request(source['url'], headers={'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'})
    with urllib.request.urlopen(request, timeout=45) as response:
        if response.status != 200:
            raise ValueError('Expected a full HTTP 200 response')
        data = response.read()
    validate_payload(data, source)
    cache.mkdir(parents=True, exist_ok=True)
    # Failed transfers never create or replace an accepted source file.
    with tempfile.NamedTemporaryFile(dir=cache, prefix='.gill-source-', delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
    try:
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def read_matrix(stream, contract):
    reader = csv.reader(stream, delimiter='\t')
    header = next(reader, [])
    annotations = contract['annotation_columns']
    n = len(annotations)
    if header[:n] != annotations or len(header) <= n or len(header) != len(set(header)):
        raise ValueError('Invalid annotation schema or duplicate/absent sample columns')
    samples = header[n:]
    if any(not label.strip() for label in samples):
        raise ValueError('Empty sample label')
    positions = [annotations.index(name) for name in contract['locus_key_fields']]
    rows, order = {}, []
    minimum, maximum = math.inf, -math.inf
    for source_row, row in enumerate(reader, 2):
        if len(row) != len(header):
            raise ValueError('Ragged source row: ' + str(source_row))
        key = tuple(row[i] for i in positions)
        if any(not value for field, value in zip(contract['locus_key_fields'], key) if field != 'ID'):
            raise ValueError('Missing locus coordinate: ' + str(source_row))
        if key in rows:
            raise ValueError('Duplicate compound locus key: ' + repr(key))
        try:
            values = [float(value) for value in row[n:]]
        except ValueError as error:
            raise ValueError('Nonnumeric expression value at row ' + str(source_row)) from error
        if not all(math.isfinite(value) for value in values):
            raise ValueError('Nonfinite expression value at row ' + str(source_row))
        minimum, maximum = min(minimum, min(values)), max(maximum, max(values))
        rows[key] = {'source_row': source_row, 'annotation': row[:n], 'values': row[n:]}
        order.append(key)
    if not rows:
        raise ValueError('Empty expression matrix')
    return {'samples': samples, 'rows': rows, 'order': order, 'minimum': minimum, 'maximum': maximum}


def aligned_rows(matrices):
    first = matrices[0]
    expected = set(first['rows'])
    for matrix in matrices[1:]:
        if set(matrix['rows']) != expected:
            raise ValueError('Source locus sets differ')
        for key in first['order']:
            if matrix['rows'][key]['annotation'] != first['rows'][key]['annotation']:
                raise ValueError('Source annotations disagree for locus: ' + repr(key))
    for key in first['order']:
        yield key, first['rows'][key]['annotation'], [value for matrix in matrices for value in matrix['rows'][key]['values']]


def match_columns(matrices, metadata, contract):
    titles = {row['title']: row for row in metadata}
    if len(titles) != len(metadata) or len({row['sample_id'] for row in metadata}) != len(metadata):
        raise ValueError('Duplicate metadata title or sample ID')
    matches, used_ids, used_labels = [], set(), set()
    for source, matrix in zip(contract['sources'], matrices):
        for column, label in enumerate(matrix['samples'], len(contract['annotation_columns']) + 1):
            title, status = label, 'exact_title'
            if title not in titles:
                title = contract['provisional_title_aliases'].get(label)
                status = 'provisional_format_alias'
            if title not in titles:
                raise ValueError('Unrecognized source sample label: ' + label)
            sample_id = titles[title]['sample_id']
            if sample_id in used_ids or label in used_labels:
                raise ValueError('Reused sample ID or source sample label')
            used_ids.add(sample_id)
            used_labels.add(label)
            matches.append({'source_id': source['source_id'], 'source_column_1based': column,
                            'source_label': label, 'geo_sample_id': sample_id,
                            'geo_title': title, 'match_status': status})
    return matches


def contrast_coverage(matches, pairs):
    by_id = {row['geo_sample_id']: row for row in matches}
    coverage = []
    for pair in pairs:
        arms = [by_id.get(pair[arm + '_rna_id']) for arm in ('control', 'treated')]
        if any(arm is None or arm['match_status'] != 'exact_title' for arm in arms):
            raise ValueError('Frozen contrast lacks two exact RNA column matches: ' + pair['pair_id'])
        coverage.append({**pair, 'control_matrix': arms[0]['source_id'], 'treated_matrix': arms[1]['source_id'],
                         'rna_expression_available': 'true', 'original_clock_values_available': 'false',
                         'migration_values_available': 'false', 'function_crosswalk_available': 'false',
                         'joint_comparison': 'DEFERRED'})
    return coverage


def derive(cache):
    contract = json.loads((HERE / 'MATRIX_CONTRACT.json').read_text())
    for relative, expected in contract['frozen_dependencies'].items():
        if sha(HERE / relative) != expected:
            raise ValueError('Frozen dependency changed: ' + relative)
    with (HERE.parent / 'linked-function-admission-2026-10-31/rna-samples.tsv').open(newline='') as stream:
        metadata = [row for row in csv.DictReader(stream, delimiter='\t') if row['accession'] == contract['accession']]
    with (HERE.parent / 'gill-migration-comparison-2026-10-31/rna-pairs.tsv').open(newline='') as stream:
        pairs = list(csv.DictReader(stream, delimiter='\t'))
    matrices = []
    for source in contract['sources']:
        path = cache / source['filename']
        validate_payload(path.read_bytes(), source)
        with gzip.open(path, 'rt', newline='') as stream:
            matrices.append(read_matrix(stream, contract))
    # Exhaust this validation before constructing any merged output.
    for _ in aligned_rows(matrices):
        pass
    matches = match_columns(matrices, metadata, contract)
    if {row['geo_sample_id'] for row in matches} != {row['sample_id'] for row in metadata}:
        raise ValueError('Source columns do not cover the metadata roster')
    coverage = contrast_coverage(matches, pairs)
    eligible = {pair[arm + '_rna_id'] for pair in pairs for arm in ('control', 'treated')}
    for row in matches:
        row['in_frozen_comparison'] = str(row['geo_sample_id'] in eligible).lower()
    first = matrices[0]
    index = contract['annotation_columns'].index('ID')
    gene_counts = Counter(row['annotation'][index] for row in first['rows'].values())
    reordered, issues = [], []
    for key in first['order']:
        left, right = (matrix['rows'][key] for matrix in matrices)
        annotations = left['annotation']
        entry = dict(zip(contract['locus_key_fields'], key))
        entry.update(probe=annotations[0], part1_source_row=left['source_row'], part2_source_row=right['source_row'])
        if left['source_row'] != right['source_row']:
            reordered.append(entry)
        gene_id = annotations[index]
        if not gene_id or gene_counts[gene_id] > 1:
            issues.append({**entry, 'issue': 'blank_gene_id' if not gene_id else 'repeated_gene_id',
                           'rows_sharing_gene_id': gene_counts[gene_id]})
    matrix_summaries = []
    for source, matrix in zip(contract['sources'], matrices):
        matrix_summaries.append({'source_id': source['source_id'], 'feature_rows': len(matrix['rows']),
                                 'sample_columns': len(matrix['samples']), 'finite_numeric_values': len(matrix['rows']) * len(matrix['samples']),
                                 'minimum_log2_RPM': matrix['minimum'], 'maximum_log2_RPM': matrix['maximum'],
                                 'source_sha256': source['sha256']})
    positional_numeric_differences = sum(
        float(correct) != float(positional)
        for matrix in matrices[1:]
        for expected_key, positional_key in zip(first['order'], matrix['order'])
        if expected_key != positional_key
        for correct, positional in zip(matrix['rows'][expected_key]['values'], matrix['rows'][positional_key]['values']))
    qc = {'schema': 'gill.matrix-recovery-qc/1', 'claim_level': 'Verified',
          'scope': 'Pinned source acquisition, matrix validity, locus alignment and within-RNA sample availability only.',
          'matrices': matrix_summaries, 'merged_feature_rows': len(first['rows']),
          'unique_locus_keys': len(first['rows']), 'sample_columns': len(matches),
          'finite_numeric_values_preserved': sum(row['finite_numeric_values'] for row in matrix_summaries),
          'exact_title_matches': sum(row['match_status'] == 'exact_title' for row in matches),
          'provisional_format_aliases': sum(row['match_status'] == 'provisional_format_alias' for row in matches),
          'eligible_comparison_RNA_arms_exactly_matched': len(eligible), 'frozen_RNA_contrasts_covered': len(coverage),
          'reordered_feature_rows': len(reordered), 'unique_nonempty_gene_ids': sum(bool(gene_id) for gene_id in gene_counts),
          'numeric_cells_differing_under_a_positional_join': positional_numeric_differences,
          'row_permutation_scope': 'The two reordered features have identical expression vectors within each source. Their identity/order differs; this permutation does not change observed numeric values.',
          'repeated_nonempty_gene_ids': sum(bool(gene_id) and count > 1 for gene_id, count in gene_counts.items()),
          'rows_with_repeated_nonempty_gene_id': sum(count for gene_id, count in gene_counts.items() if gene_id and count > 1),
          'blank_gene_id_rows': gene_counts.get('', 0), 'source_row_alignment': 'PASS: unique compound keys and matching per-key annotations',
          'gene_id_only_model_input': 'UNRESOLVED: preserve loci; no gene-ID collapse or choice among repeated IDs is authorized.',
          'quantity': 'Source log2 RPM values, not raw counts or molecular ages. Negative values are retained.',
          'joint_comparison': 'DEFERRED', 'new_admitted_function_pairs': 0,
          'missing_joint_inputs': ['original per-sample Figure 3C custom clock values', 'original technical-replicate migration speeds',
                                  'authoritative function-culture to RNA mapping and context'],
          'Phase_483': 'UNCHANGED: public source recovery does not constitute supervised external evaluation.'}
    row_fields = [*contract['locus_key_fields'], 'probe', 'part1_source_row', 'part2_source_row']
    outputs = {'MATRIX_QC.json': encode(qc),
               'sample-columns.tsv': tsv(matches, list(matches[0])),
               'contrast-coverage.tsv': tsv(coverage, list(coverage[0])),
               'reordered-features.tsv': tsv(reordered, row_fields),
               'gene-id-issues.tsv': tsv(issues, [*row_fields, 'issue', 'rows_sharing_gene_id'])}
    return outputs, matrices, contract


def write_merged(cache, matrices, contract):
    destination = cache / 'gill-locus-aligned-log2-RPM.tsv.gz'
    cache.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=cache, prefix='.gill-merged-', delete=False) as stream:
        temporary = Path(stream.name)
    try:
        with temporary.open('wb') as raw:
            with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as compressed:
                with io.TextIOWrapper(compressed, encoding='utf-8', newline='') as text:
                    writer = csv.writer(text, delimiter='\t', lineterminator='\n')
                    writer.writerow([*contract['annotation_columns'], *[label for matrix in matrices for label in matrix['samples']]])
                    for _, annotation, values in aligned_rows(matrices):
                        writer.writerow([*annotation, *values])
        digest = sha(temporary)
        if destination.exists() and sha(destination) != digest:
            raise ValueError('Existing merged output differs; preserve it and choose another cache directory')
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return {'filename': destination.name, 'sha256': digest, 'bytes': destination.stat().st_size,
            'quantity': 'Untransformed source log2 RPM text; columns retain original source labels.',
            'method': 'Unique compound-locus-key alignment, preserving first-file locus order and both input column orders.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=HERE.parents[1] / '.data/gill-source-recovery-2026-10-31')
    parser.add_argument('--download', action='store_true', help='Download only missing pinned expression matrices; never retry silently.')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--write', action='store_true', help='Write the source-QC tables.')
    mode.add_argument('--verify', action='store_true', help='Replay and compare released QC tables; the default.')
    parser.add_argument('--merge', action='store_true', help='With --write, save a locus-aligned matrix in the ignored cache.')
    args = parser.parse_args()
    if args.merge and not args.write:
        parser.error('--merge requires --write')
    contract = json.loads((HERE / 'MATRIX_CONTRACT.json').read_text())
    if args.download:
        for source in contract['sources']:
            download(source, args.cache)
    outputs, matrices, contract = derive(args.cache)
    for name, content in outputs.items():
        path = HERE / name
        if args.write:
            path.write_text(content, encoding='utf-8')
        elif path.read_text(encoding='utf-8') != content:
            raise ValueError('Released QC output differs: ' + name)
    if args.merge:
        merged = write_merged(args.cache, matrices, contract)
        (args.cache / 'MERGED_MATRIX.json').write_text(encode(merged), encoding='utf-8')
        print('Merged matrix SHA-256: ' + merged['sha256'])
    print('PASS source recovery: 2 pinned matrices; locus-key alignment; exact frozen RNA contrast coverage. Joint comparison remains DEFERRED.')


if __name__ == '__main__':
    main()

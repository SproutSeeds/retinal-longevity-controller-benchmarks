#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["rdata==1.1.0", "numpy==2.5.4", "pandas==3.0.6", "scipy==1.18.1"]
# ///
"""Inspect observed metadata and RNA count integrity; no expression contrasts."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import rdata
from scipy.sparse import csc_matrix


def deref(node):
    while node.info.type.name == 'REF':
        node = node.referenced_object
    return node


def attrs(obj):
    result = {}
    node = deref(obj).attributes
    while node is not None and deref(node).info.type.name != 'NILVALUE':
        node = deref(node)
        key = deref(deref(node.tag).value).value.decode()
        assert key not in result
        result[key] = node.value[0]
        node = node.value[1]
    return result


def converted(node):
    return rdata.conversion.convert(node)


def tabulate(series):
    return {str(k): int(v) for k, v in series.value_counts(dropna=False).items() if v > 0}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--rds', type=Path, required=True)
    p.add_argument('--prefix', required=True)
    args = p.parse_args()
    here = Path(__file__).parent
    receipt = json.loads((here / (args.rds.name + '.receipt.json')).read_text())
    assert hashlib.sha256(args.rds.read_bytes()).hexdigest() == receipt['sha256']
    print('Parsing metadata and count integrity only:', args.rds.name, flush=True)
    root = attrs(rdata.parser.parse_file(args.rds).object)
    meta = converted(root['meta.data'])
    assays = deref(root['assays'])
    names = list(converted(attrs(assays)['names']))
    assert names.count('RNA') == 1
    assay_slots = {str(k): attrs(v) for k, v in zip(names, assays.value)}
    slots = attrs(assay_slots['RNA']['counts'])
    dims = tuple(int(x) for x in converted(slots['Dim']))
    genes, columns = converted(slots['Dimnames'])
    assert dims == (len(genes), len(columns)) and len(set(genes)) == len(genes)
    assert list(meta.index) == list(columns) and not meta.index.has_duplicates
    values, indices, offsets = [np.asarray(converted(slots[k])) for k in ['x', 'i', 'p']]
    assert np.isfinite(values).all() and (values >= 0).all() and (values % 1 == 0).all()
    assert len(offsets) == dims[1] + 1 and offsets[0] == 0 and offsets[-1] == len(values)
    assert len(indices) == len(values) and (np.diff(offsets) >= 0).all()
    assert (indices >= 0).all() and (indices < dims[0]).all()
    counts = csc_matrix((values, indices, offsets), shape=dims)
    counts.check_format(full_check=True)
    assert counts.has_canonical_format
    totals = np.asarray(counts.sum(axis=0)).ravel()
    features = np.diff(offsets)
    assert np.array_equal(totals, meta['nCount_RNA'].to_numpy()) and (totals > 0).all()
    assert np.array_equal(features, meta['nFeature_RNA'].to_numpy())
    sample_key = 'MULTI_classification_rescued' if 'MULTI_classification_rescued' in meta else 'hash.ID'
    assert meta[sample_key].notna().all()
    categorical = [k for k in ['orig.ident', 'hash.ID', 'age_genotype', 'age', 'genotype',
                   'Treatment', 'treatment', 'Age_Treatment', 'age_treatment', 'Celltype',
                   'Celltype.LowRes', 'LMO2_classification.global', 'LMO_classification.global',
                   'MULTI_classification.global', 'MULTI_classification_rescued'] if k in meta]
    groups = []
    for key, subset in meta.groupby(sample_key, observed=True, sort=True):
        groups.append({'sample_id': str(key), 'cells': len(subset),
                       'observed_metadata': {k: tabulate(subset[k]) for k in categorical}})
    assay_info = {}
    for name, slot in assay_slots.items():
        if 'counts' not in slot:
            continue
        s = attrs(slot['counts'])
        feature_names, cell_names = converted(s['Dimnames'])
        assay_info[name] = {'shape': [int(x) for x in converted(s['Dim'])],
                            'cell_order_matches_RNA': list(cell_names) == list(columns)}
        if name != 'RNA' and len(feature_names) < 100:
            assay_info[name]['feature_names'] = [str(x) for x in feature_names]
    result = {'claim_level': 'Verified', 'scope': 'observed metadata and count integrity only',
              'source': receipt, 'expression_analysis_executed': False,
              'cells': dims[1], 'rna_genes': dims[0], 'sample_key': sample_key,
              'metadata_columns': list(meta.columns), 'animals': groups,
              'observed_metadata': {k: tabulate(meta[k]) for k in categorical},
              'assays': assay_info,
              'checks': {'source_checksum': True, 'raw_counts_valid': True,
                         'cell_order_matches': True, 'RNA_totals_match_metadata': True,
                         'RNA_features_match_metadata': True, 'unique_genes_and_cells': True}}
    (here / (args.prefix + '-metadata.json')).write_text(json.JSONEncoder(indent=2, sort_keys=True).encode(result) + '\n')
    meta[categorical].to_csv(here / (args.prefix + '-cell-metadata.tsv'), sep='\t', index_label='cell_barcode')
    print('PASS:', dims, 'animals:', len(groups), flush=True)
    for group in groups:
        print(group['sample_id'], group['cells'], flush=True)


if __name__ == '__main__':
    main()

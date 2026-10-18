#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["rdata==1.1.0", "numpy==2.5.4", "pandas==3.0.6", "scipy==1.18.1"]
# ///
"""Read data slots only; never execute the deposited R analysis code."""
import argparse
import hashlib
import json
from pathlib import Path
import re

import numpy as np
import rdata
from scipy.sparse import csc_matrix
from analyze import checked, save, sha, soft_samples


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
        if key in result:
            raise ValueError('Duplicate R attribute')
        result[key] = node.value[0]
        node = node.value[1]
    return result


def code_mapping(code, variable):
    pattern = (rf'{variable}\s*<-\s*plyr::mapvalues\(x\s*=\s*svz_sing\$hash.ID,\s*'
               r'from\s*=\s*c\((.*?)\),\s*to\s*=\s*c\((.*?)\)\s*\)')
    matches = list(re.finditer(pattern, code, flags=re.S))
    if len(matches) != 1:
        raise ValueError('Missing or ambiguous author-code mapping')
    match = matches[0]
    keys, values = [re.findall(r'"([^"]+)"', group) for group in match.groups()]
    if len(keys) != len(values) or len(keys) != len(set(keys)):
        raise ValueError('Author-code mapping is not one-to-one by sample key')
    return dict(zip(keys, values)), [code[:match.start()].count('\n') + 1, code[:match.end()].count('\n') + 1]


def validate_metadata(meta, columns, ages, treatments):
    required = ['hash.ID', 'orig.ident', 'age_genotype', 'age', 'genotype', 'Treatment', 'Celltype', 'LMO_classification.global']
    if meta.index.has_duplicates or len(set(columns)) != len(columns) or list(meta.index) != list(columns):
        raise ValueError('Cell metadata does not match unique RNA count columns in order')
    if meta[required].isna().any().any():
        raise ValueError('Missing required cell metadata')
    if set(meta['LMO_classification.global']) != {'Singlet'}:
        raise ValueError('Non-singlet assignments require a new admission decision')
    for sample, group in meta.groupby('hash.ID', observed=True, sort=True):
        if sample not in ages or sample not in treatments:
            raise ValueError('Unmapped animal/sample identity')
        match = re.fullmatch(r'[A-L]-([^-]+)-\d{8}-lane([123])-(untr|2Dox0|2Dox5)-[ACGT]+', sample)
        if not match:
            raise ValueError('Unexpected sample identifier')
        age, genotype = ages[sample].split('_')
        expected = {'age_genotype': ages[sample], 'age': age, 'genotype': genotype,
                    'Treatment': treatments[sample], 'orig.ident': 'Lane' + match[2]}
        if match[3] != treatments[sample]:
            raise ValueError('Treatment token conflicts with author-code map')
        for field, value in expected.items():
            if set(group[field]) != {value}:
                raise ValueError('Animal-level metadata conflict: ' + field)
    return True


def main(cache):
    name = 'svz_iOSKM_cohort2_toshare.rds'
    path = checked(cache, name)
    repository = json.loads(checked(cache, 'svz-zenodo.json').read_text())
    source = next(row for row in repository['files'] if row['key'] == name)
    checksum = 'md5:' + hashlib.md5(path.read_bytes()).hexdigest()
    if checksum != source['checksum'] or path.stat().st_size != source['size']:
        raise ValueError('RDS differs from Zenodo repository checksum or size')
    code_path = checked(cache, 'svz-iOSKM_cohort2-iOSKM2_seurat_part2.R')
    code = code_path.read_text()
    ages, age_lines = code_mapping(code, 'age_genotype')
    treatments, treatment_lines = code_mapping(code, 'treatment')
    if set(ages) != set(treatments):
        raise ValueError('Author-code mapping coverage differs')
    parsed = rdata.parser.parse_file(path)
    root = attrs(parsed.object)
    meta = rdata.conversion.convert(root['meta.data'])
    assays = deref(root['assays'])
    assay_names = list(rdata.conversion.convert(attrs(assays)['names']))
    if assay_names.count('RNA') != 1:
        raise ValueError('Missing or duplicate raw RNA assay')
    count_slots = attrs(attrs(assays.value[assay_names.index('RNA')])['counts'])
    dims = tuple(int(x) for x in rdata.conversion.convert(count_slots['Dim']))
    genes, columns = rdata.conversion.convert(count_slots['Dimnames'])
    if dims != (len(genes), len(columns)) or len(set(genes)) != len(genes):
        raise ValueError('RNA count dimension/identifier mismatch')
    values, indices, offsets = [np.asarray(rdata.conversion.convert(count_slots[key])) for key in ['x', 'i', 'p']]
    if (not np.isfinite(values).all() or (values < 0).any() or (values % 1 != 0).any()
            or len(offsets) != dims[1] + 1 or offsets[0] != 0 or offsets[-1] != len(values)
            or len(indices) != len(values) or (np.diff(offsets) < 0).any()
            or (indices < 0).any() or (indices >= dims[0]).any()):
        raise ValueError('Invalid sparse raw counts')
    counts = csc_matrix((values, indices, offsets), shape=dims)
    counts.check_format(full_check=True)
    if not counts.has_canonical_format:
        raise ValueError('Duplicate/unsorted sparse count coordinates')
    totals = np.asarray(counts.sum(axis=0)).ravel()
    if not np.array_equal(totals, meta['nCount_RNA'].to_numpy()) or (totals <= 0).any():
        raise ValueError('Raw count totals disagree with cell metadata')
    validate_metadata(meta, columns, ages, treatments)
    geo = soft_samples(checked(cache, 'GSE224438-samples.txt').read_text())
    lanes = {}
    for row in geo:
        match = re.fullmatch(r'Whole-body reprogramming, cohort 2, lane ([123]) \(multiplexed scRNA-seq\)', row['title'][0])
        if match:
            lanes['Lane' + match[1]] = row['accession']
    if set(lanes) != {'Lane1', 'Lane2', 'Lane3'}:
        raise ValueError('Incomplete GEO cohort/lane join')
    animals = []
    for sample, group in meta.groupby('hash.ID', observed=True, sort=True):
        row = group.iloc[0]
        animals.append({'hash_id': str(sample), 'animal_label': sample.split('-')[1],
                        'age_group': str(row['age']), 'genotype': str(row['genotype']),
                        'treatment': str(row['Treatment']), 'cohort': 2, 'lane': str(row['orig.ident']),
                        'geo_library': lanes[row['orig.ident']], 'cells': len(group),
                        'celltype_counts': {str(k): int(v) for k, v in group['Celltype'].value_counts().items() if v > 0}})
    if len({a['animal_label'] for a in animals}) != len(animals):
        raise ValueError('Animal label duplicated across hash IDs')
    celltypes = {str(k): int(v) for k, v in meta['Celltype'].value_counts().items() if v > 0}
    group_counts = []
    for (age, treatment), group in meta.groupby(['age', 'Treatment'], observed=True, sort=True):
        group_counts.append({'age': str(age), 'treatment': str(treatment), 'cells': len(group),
                             'animals': int(group['hash.ID'].nunique())})
    result = {'claim_level': 'Verified', 'evidence_class': 'observed_metadata_admission',
              'source_sha256': sha(path), 'zenodo_checksum': checksum, 'zenodo_license': repository['metadata']['license']['id'],
              'author_code_commit': '011586aea2e8612c794e57d2a260fa1a29d417a0',
              'author_code_sha256': sha(code_path), 'author_code_map_lines': {'age_genotype': age_lines, 'treatment': treatment_lines},
              'rna_genes': dims[0], 'cells': dims[1], 'metadata_columns': len(meta.columns), 'animals': animals,
              'group_counts': group_counts, 'celltype_counts': celltypes,
              'unresolved_numeric_celltype_labels': {k: v for k, v in celltypes.items() if k.isdigit()},
              'author_code_sample_count': len(ages), 'absent_author_code_samples': sorted(set(ages) - set(meta['hash.ID'])),
              'checks': {'raw_counts_valid': True, 'cell_order_matches': True, 'RNA_totals_match_metadata': True,
                         'animal_metadata_matches_author_code': True, 'cohort_lane_join_complete': True},
              'decision': 'admit_for_separately_frozen_animal_level_mouse_neural_comparator',
              'expression_analysis_executed': False,
              'timing': 'GEO: three 2-day-on/5-day-off pulses. Present treated animals carry 2Dox0; no 2Dox5 cells survive in this deposited subset.',
              'constraints': ['Only two old treated animals and three old controls; no cell-level replication claims.',
                              'Both young controls occur only in lane 3; age contrasts require explicit lane-confounding limits.',
                              'Old treated/control comparison shares lanes 1 and 2; the third old control is in lane 3.',
                              'Four numeric clusters totaling 70 cells lack biological labels; do not silently assign or discard them.',
                              'Counts describe recovered sequenced cells, not unbiased tissue abundances.',
                              'No withdrawal cohort in the deposited object; no human or retinal measurements.'],
              'next_contract': 'Freeze animal-by-cell-type pseudobulk, composition denominators, minimum cell counts, lane sensitivity and replication rules before expression testing.',
              'readouts': {f'CX004-R0{i}': 'insufficient_signal' for i in range(1, 5)}}
    save('neural-admission.json', result)
    print('Neural admission:', dims, 'raw RNA; animals', len(animals), '; groups', group_counts)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, required=True)
    main(parser.parse_args().cache)

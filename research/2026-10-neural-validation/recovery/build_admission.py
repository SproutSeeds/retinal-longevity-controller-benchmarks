#!/usr/bin/env python3
"""Reconcile observed cohort-1 metadata with the pinned author sample map."""
import hashlib
import json
from pathlib import Path
import argparse
import re

HERE = Path(__file__).parent
PRIOR = HERE.parent.parent / 'cx004-independent-comparator-2026-10-18'
if not PRIOR.is_dir():
    PRIOR = HERE.parent.parent / '2026-10-independent-comparator'
CACHE = Path('/tmp/cx004-independent-comparator-2026-10-18')
COMMIT = '011586aea2e8612c794e57d2a260fa1a29d417a0'


def save(name, data):
    (HERE / name).write_text(json.JSONEncoder(indent=2, sort_keys=True).encode(data) + '\n')


def code_map(code, variable):
    pattern = (rf'{variable}\s*<-\s*plyr::mapvalues\(x\s*=\s*svz_sing\$hash.ID,\s*'
               r'from\s*=\s*c\((.*?)\),\s*to\s*=\s*c\((.*?)\)\s*\)')
    matches = list(re.finditer(pattern, code, re.S))
    assert len(matches) == 1
    m = matches[0]
    keys, values = [re.findall(r'"([^"]+)"', x) for x in m.groups()]
    assert len(keys) == len(values) == len(set(keys))
    return dict(zip(keys, values)), [code[:m.start()].count('\n') + 1, code[:m.end()].count('\n') + 1]


def main():
    metadata = json.loads((HERE / 'cohort1-metadata.json').read_text())
    source = next(x for x in json.loads((PRIOR / 'input-files.json').read_text())['sources']
                  if x['id'] == 'svz-iOSKM_cohort1-seurat_part2.R')
    code_path = CACHE / source['id']
    code_sha = hashlib.sha256(code_path.read_bytes()).hexdigest()
    assert code_sha == source['expected_sha256']
    mapping, lines = code_map(code_path.read_text(), 'treatment')
    observed = {x['sample_id']: x for x in metadata['animals']}
    animals, full_map = [], []
    for key, treatment in mapping.items():
        m = re.fullmatch(r'Sample([1-6])-([^-]+)-DOB(\d{8})-(untr|2Dox0|2Dox5)-([ACGT]{8})', key)
        assert m and m[4] == treatment
        full_map.append({'hash_id': key, 'animal_label': m[2], 'birthdate_token': m[3],
                         'treatment': treatment, 'multiplex_oligo': m[5],
                         'observed_in_deposited_object': key in observed})
        if key not in observed:
            continue
        row = observed[key]
        fields = row['observed_metadata']
        assert fields['Treatment'] == {treatment: row['cells']}
        assert fields['orig.ident'] == {'SeuratProject': row['cells']}
        assert fields['LMO2_classification.global'] == {'Singlet': row['cells']}
        assert sum(fields['Celltype'].values()) == row['cells']
        animals.append({'hash_id': key, 'animal_label': m[2], 'age_group': 'old',
                        'age_months_range': [18, 20], 'sex': 'male', 'genotype': 'OSKM',
                        'treatment': treatment, 'cohort': 1,
                        'lane': 'cohort1_single_multiplexed_lane', 'orig_ident': 'SeuratProject',
                        'geo_library': 'GSM7022367', 'cells': row['cells'],
                        'celltype_counts': fields['Celltype']})
    cohort2 = json.loads((PRIOR / 'neural-admission.json').read_text())
    labels1 = set(metadata['observed_metadata']['Celltype'])
    labels2 = {x for x in cohort2['celltype_counts'] if not x.isdigit()}
    assert labels1 == labels2
    assert len(animals) == 4 and sum(x['cells'] for x in animals) == 1194
    assert {t: sum(x['treatment'] == t for x in animals) for t in ['2Dox0', 'untr']} == {'2Dox0': 2, 'untr': 2}
    result = {
        'claim_level': 'Verified', 'evidence_class': 'observed_metadata_admission',
        'decision': 'admit_same_study_cross_cohort_direction_comparator',
        'pre_outcome_admission': True, 'expression_analysis_executed': False,
        'source_sha256': metadata['source']['sha256'],
        'source_url': metadata['source']['url'],
        'zenodo_checksum': metadata['source']['repository_checksum'],
        'author_code_commit': COMMIT, 'author_code_sha256': code_sha,
        'author_code_url': source['url'], 'author_code_map_lines': {'treatment': lines},
        'cells': metadata['cells'], 'rna_genes': metadata['rna_genes'], 'animals': animals,
        'celltype_counts': metadata['observed_metadata']['Celltype'],
        'group_counts': [{'age': 'old', 'treatment': t,
                          'animals': sum(a['treatment'] == t for a in animals),
                          'cells': sum(a['cells'] for a in animals if a['treatment'] == t)}
                         for t in ['2Dox0', 'untr']],
        'author_code_sample_count': len(mapping),
        'absent_author_code_samples': sorted(set(mapping) - set(observed)),
        'timing': {'regimen': 'Three 2-day doxycycline pulses with 5-day withdrawal intervals.',
                   'present_treated_endpoint': 'Immediately after the final 2-day pulse.',
                   'post_final_pulse_withdrawal_days': 0,
                   'withdrawal_observations': 0,
                   'source_url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC12036604/',
                   'source_locator': 'Results, Partial reprogramming boosts neuroblast proportion in old mice'},
        'metadata_sources': {
            'age_and_sex': {'url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC12036604/',
                           'locator': 'Extended Data Fig. 2b: 18-20 months, two males per condition'},
            'genotype_and_chemistry': {'url': 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM7022367',
                                      'locator': 'genotype, treatment_protocol and extract_protocol'},
            'lane': {'url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC12036604/',
                     'locator': 'Extended Data Fig. 2c: six mice into one 10x lane',
                     'note': 'Descriptive cohort-specific lane ID; object orig.ident is SeuratProject.'}},
        'label_compatibility': {'named_celltype_labels_identical': True,
             'cohort1_numeric_unresolved_cells': 0, 'cohort2_numeric_unresolved_cells': 70,
             'cohort1_annotation_collapses': {
                 'qNSC.primed': 'Astrocyte_qNSC', '33': 'Microglia', '36': 'Microglia',
                 'Vasc.Smooth.Muscle': 'Mural', 'Pericyte': 'Mural'},
             'source_locator': 'Pinned cohort1 seurat_part2.R lines 155-162 and 223-225'},
        'differences_from_cohort2': [
             'Cohort1 is 18-20 months and all male; cohort2 old mice are 24-26 months with both sexes.',
             'Cohort1 uses 10x v3.0; cohort2 uses v3.1.',
             'Cohort1 has a single lane with both conditions; cohort2 has two shared old-treatment/control lanes plus an extra control on lane 3.',
             'Ten named labels agree; annotation collapses differ and cohort2 retains 70 unresolved numeric cells.',
             'Cohort1 has two treated and two controls; no young comparator or post-final-pulse withdrawal cells.'],
        'constraints': [
             'Use as a same-study direction comparator with independent animals; age, sex and chemistry preclude exact replication.',
             'Sparse animal-by-celltype strata must fail the separately frozen minimum-cell threshold openly.',
             'Recovered-cell fractions do not estimate absolute tissue abundance.',
             'Absent 2Dox5 sample names in LMO features are not evidence of observed withdrawal cells.',
             'No human or retinal measurements; no late recovery, function or calibrated rare-state risk endpoint.'],
        'checks': {**metadata['checks'], 'animal_metadata_matches_author_code': True,
                   'cohort_lane_join_complete': True, 'named_celltype_labels_match_cohort2': True},
        'readouts': {f'CX004-R0{i}': 'insufficient_signal' for i in range(1, 5)}}
    save('cohort1-admission.json', result)
    save('cohort1-author-sample-map.json', {'source_url': source['url'], 'source_sha256': code_sha,
                                         'source_lines': lines, 'samples': full_map})
    print('PASS cohort1 admission: 4 animals; 1194 cells; 10 matching named labels; no withdrawal cells')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, default=CACHE)
    parser.add_argument('--prior', type=Path, default=PRIOR)
    args = parser.parse_args()
    CACHE, PRIOR = args.cache, args.prior
    main()

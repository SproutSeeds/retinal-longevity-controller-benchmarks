#!/usr/bin/env python3
"""Offline consistency and frozen-artifact checks; no biological certification."""
import argparse
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    checks = []
    def read(name):
        return json.loads((HERE / name).read_text())
    def check(name, passed):
        checks.append({'name': name, 'status': 'PASS' if passed else 'FAIL'})
    params = read('srsf1-clock-parameters.json')
    terms = params['terms']
    genes = [r for r in terms if r['term'].startswith('ENSG')]
    check('295 unique model terms', len(terms) == len({r['term'] for r in terms}) == 295)
    check('292 gene terms', len(genes) == params['gene_terms'] == 292)
    check('intercept and library terms', {r['term'] for r in terms} - {r['term'] for r in genes} == {'Intercept', 'LibType.Total', 'LibType.mRNA'})
    check('finite coefficients', all(math.isfinite(r[k]) for r in terms for k in ['coefficient', 'standardized_coefficient']))
    coverage = params['matrix_coverage']
    check('complete gene coverage', coverage['gene_terms_present'] == 292 and coverage['missing_genes'] == [] and coverage['duplicated_model_gene_ids'] == [])
    check('807 human libraries', coverage['libraries'] == 807)
    check('exact replay remains blocked', params['exact_replay_status'] == 'BLOCKED' and len(params['remaining_dependencies']) == 4)
    sample = read('srsf1-recovery-samples.json')
    rows = sample['samples']
    check('72 explicitly joined human recovery libraries', len(rows) == sample['recovery_library_count'] == len({r['matrix_column'] for r in rows}) == 72)
    check('human species retained', all(r['organism_ch1'] == ['Homo sapiens'] for r in rows))
    check('32 mouse libraries separated', sample['excluded_nonhuman_off_libraries'] == 32 and sample['all_species_off_library_count'] == 104)
    check('three human donor lines', sample['independent_human_donor_lines'] == len({r['characteristics']['cell line'] for r in rows}) == 3)
    check('construct counts reconcile previous subset', sample['human_construct_counts'] == {'SRSF1': 30, 'mTagBFP2': 30, 'OSKM': 12})
    check('seven source-native human schedules', len(sample['schedule_counts']) == 7 and sum(sample['schedule_counts'].values()) == 72)
    check('timing remains unresolved', sample['chronology_status'].startswith('UNRESOLVED'))
    history = read('clock-dependency-audit.json')
    check('27 pinned commits', history['commit_count'] == len(set(history['commit_ids'])) == 27)
    check('history head pinned', history['head'] == '7ae5f38b7ea74f76cb13076b64350d5930bb152f')
    check('21 distinct historical paths, six current', len(history['all_historical_paths']) == 21 and len(history['current_paths']) == 6)
    check('one branch, no tags/releases', len(history['branches']) == 1 and history['tags'] == history['releases'] == [])
    check('application overwrite recorded without execution', history['fsva_output_overwritten_in_apply_script'] is True)
    mapping = read('geo350289-mapping-audit.json')
    check('GSE350289 remains blocked', mapping['status'] == 'mapping_blocked')
    check('two empty perturbation sheets', mapping['sheets']['Sample 2']['nonempty_rows'] == mapping['sheets']['Sample 3']['nonempty_rows'] == 0)
    ocular = read('ocular-source-clarification.json')
    check('ocular claims retain author attribution', ocular['evidence_role'].startswith('Author-reported'))
    check('ocular sources anchored', set(ocular['source_anchors']) == {'OSK_clock', 'GSTA4_clock', 'clock_method'})
    check('ocular library quantities', {k: len(v) for k, v in ocular['cohorts'].items()} == {'GSE304038': 18, 'GSE304043': 7})
    clocks = read('ocular-clock-artifacts.json')
    check('two inventoried archives without model download', len(clocks['archives']) == 2 and all(x['model_files_downloaded'] is False for x in clocks['archives']))
    decision = read('reuse-decision.json')
    check('four human readouts remain open', len(decision['readouts']) == 4 and set(decision['readouts'].values()) == {'insufficient_signal'})
    check('experiment replacement inconclusive', decision['experiment_replacement_verdict'] == 'INCONCLUSIVE')
    check('no operation or outreach claimed', decision['wet_lab_purchased_or_arranged'] is decision['outreach_sent'] is False)
    receipts = [read('retrieval-' + str(i) + '.json') for i in range(1, 4)]
    sources = [r for x in receipts for r in x['sources']]
    check('30 retrieval attempts, 27 retained files', len(sources) == 30 and sum(r['status'] == 'retrieved' for r in sources) == 27)
    source_hashes = {r['id']: r.get('sha256') for r in sources}
    check('parameters bound to supplement', params['source_sha256'] == source_hashes['srsf1-coefficients.xlsx'])
    check('sample joins bound to GEO snapshot', sample['source_sha256'] == source_hashes['gse325735-samples.txt'])
    for name, expected in read('artifact-hashes.json')['files'].items():
        path = HERE / name
        check('sha256:' + name, path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected)
    result = {'status': 'PASS' if all(x['status'] == 'PASS' for x in checks) else 'FAIL',
              'scope': 'Frozen-artifact integrity, parameter extraction bookkeeping, species/sample separation and bounded admission decisions; not biological validation.',
              'passed': sum(x['status'] == 'PASS' for x in checks), 'total': len(checks), 'checks': checks}
    if args.write:
        (HERE / 'VERIFICATION.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(result['status'], str(result['passed']) + '/' + str(result['total']))
    for row in checks:
        if row['status'] == 'FAIL':
            print(row['name'])
    raise SystemExit(result['status'] != 'PASS')


if __name__ == '__main__':
    main()

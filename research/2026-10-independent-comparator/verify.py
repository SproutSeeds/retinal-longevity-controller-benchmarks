#!/usr/bin/env python3
"""Independent arithmetic, claim-boundary and file-integrity audit (stdlib)."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(write=False):
    checks = []
    def read(name): return json.loads((HERE / name).read_text())
    def check(name, passed): checks.append({'name': name, 'status': 'PASS' if passed else 'FAIL'})
    def close(x, y): return math.isclose(x, y, rel_tol=1e-10, abs_tol=1e-10)
    h, n, s = [read(name) for name in ['human-results.json', 'neural-admission.json', 'synthetic-results.json']]
    manifest = read('input-files.json')['sources']
    source_hash = {r['id']: r['expected_sha256'] for r in manifest}
    check('Human input hash bound', h['source_sha256'] == source_hash['GSE297233_raw_counts_matrix.csv.gz'])
    check('HGNC mapping hash bound', h['hgnc_sha256'] == source_hash['hgnc_complete_set.txt'])
    check('Neural input hash bound', n['source_sha256'] == source_hash['svz_iOSKM_cohort2_toshare.rds'])
    check('Both outcome analyses bind frozen contract', h['contract_sha256'] == s['contract_sha256'] == sha(HERE / 'analysis-contract.json'))
    check('Human join amendment bound', h['join_amendment_sha256'] == sha(HERE / 'join-amendment.json'))
    check('Eight libraries and one donor', h['libraries'] == 8 and h['independent_donors'] == 1 and len(h['sample_manifest']) == 8)
    check('Counts and all 46 panel genes available', h['rows'] == 62703 and h['fractional_count_entries'] == 0 and h['missing_genes'] == [] and len(h['gene_map']) == 46)
    check('Human sample identifiers unique', len({r['matrix_column'] for r in h['sample_manifest']}) == 8)
    check('All ten predefined comparisons reported', len(h['contrasts']) == 10)
    panel = read('panels.json')
    panel['reprogramming_without_OSK_overlap'] = [g for g in panel['reprogramming_state'] if g not in ['POU5F1', 'SOX2']]
    for row in h['contrasts']:
        name = row['construct'] + ':' + row['panel']
        check(name + ': fixed membership', row['genes'] == panel[row['panel']])
        treated = [r['matrix_column'] for r in h['sample_manifest'] if r['construct'] == row['construct'] and r['condition'] == 'dox']
        control = [r['matrix_column'] for r in h['sample_manifest'] if r['construct'] == row['construct'] and r['condition'] == 'no dox']
        for method, result in row['methods'].items():
            values = h['gene_values'][method]
            scores = {col: mean(values[g][col] for g in row['genes']) for col in treated + control}
            effect = mean(scores[col] for col in treated) - mean(scores[col] for col in control)
            pairs = [scores[t] - scores[c] for t, c in itertools.product(treated, control)]
            omissions = {}
            for omit in row['genes']:
                genes = [g for g in row['genes'] if g != omit]
                omissions[omit] = mean(mean(values[g][c] for g in genes) for c in treated) - mean(mean(values[g][c] for g in genes) for c in control)
            check(name + ':' + method + ': recomputed from gene values',
                  close(effect, result['mean_difference']) and all(close(scores[c], result['library_scores'][c]) for c in scores)
                  and all(close(x, y) for x, y in zip(pairs, result['four_library_differences'])))
            check(name + ':' + method + ': omission and library ranges',
                  all(close(omissions[g], result['single_gene_omission_differences'][g]) for g in omissions)
                  and all(close(x, y) for x, y in zip([min(pairs), max(pairs)], result['pairwise_range']))
                  and all(close(x, y) for x, y in zip([min(omissions.values()), max(omissions.values())], result['omission_range'])))
    stress = next(r for r in h['contrasts'] if r['construct'] == 'OSK' and r['panel'] == 'stress_panel')
    check('OSK stress normalization reversal retained', stress['methods']['log2_cpm']['mean_difference'] > 0 > stress['methods']['log2_median_ratio_cpm_equivalent']['mean_difference'])
    check('Neural 3857 cells and seven animals', n['cells'] == sum(r['cells'] for r in n['animals']) == 3857 and len(n['animals']) == 7)
    check('Neural unique animals and raw RNA dimensions', n['rna_genes'] == 31057 and len({r['animal_label'] for r in n['animals']}) == 7)
    check('Animal celltype counts reconcile', all(sum(r['celltype_counts'].values()) == r['cells'] for r in n['animals']))
    check('Celltype totals reconcile across animals', all(sum(r['celltype_counts'].get(k, 0) for r in n['animals']) == v for k, v in n['celltype_counts'].items()))
    check('Four unresolved clusters retained', len(n['unresolved_numeric_celltype_labels']) == 4 and sum(n['unresolved_numeric_celltype_labels'].values()) == 70)
    check('Two old treated, three old controls, two young controls', {(r['age'], r['treatment']): (r['animals'], r['cells']) for r in n['group_counts']} == {('old', '2Dox0'): (2, 732), ('old', 'untr'): (3, 1254), ('young', 'untr'): (2, 1871)})
    check('Withdrawal samples absent', all(r['treatment'] != '2Dox5' for r in n['animals']) and len(n['absent_author_code_samples']) == 5)
    check('Neural admission remains separate from expression testing', n['expression_analysis_executed'] is False and n['decision'].startswith('admit_for_separately_frozen'))
    check('All neural identity checks pass', set(n['checks'].values()) == {True})
    check('Synthetic-only label retained', s['evidence_class'] == 'synthetic_only')
    check('48 synthetic scenarios and 24 all-null scenarios', len(s['scenarios']) == 48 and len(s['all_null_scenarios']) == 24)
    check('Fixed 1200-cell allocation', all(sum(r['allocation']) == 1200 for r in s['scenarios'] + s['all_null_scenarios']))
    check('Confirmation probabilities valid and ordered', all(0 <= r['two_or_more_donors_flagged'] <= r['any_donor_flagged'] <= 1 for r in s['scenarios'] + s['all_null_scenarios']))
    check('Quadrature convergence and independent Monte Carlo', s['quadrature_max_absolute_error'] < 1e-6 and all(r['absolute_error'] <= r['tolerance'] for r in s['monte_carlo_check'].values()))
    independent_nulls = [r for r in s['all_null_scenarios'] if r['false_positive_donor_correlation'] == 0]
    check('Independent all-null closed form', all(close(r['any_donor_flagged'], 1 - r['specificity'] ** 1200) for r in independent_nulls))
    check('Four CX004 readouts remain insufficient', all(len(x['readouts']) == 4 and set(x['readouts'].values()) == {'insufficient_signal'} for x in [h, n]))
    decision = read('reuse-decision.json')
    check('No experiment replacement promotion', decision['experiment_replacement_verdict'] == 'INCONCLUSIVE')
    check('Scope and no spend preserved', decision['wet_lab_purchased_or_arranged'] is False and decision['paid_compute_used'] is False and decision['new_outreach_sent_this_pass'] is False)
    tests = read('TESTS.json')
    check('15 adversarial tests passed', tests['exit_code'] == 0 and tests['tests'] == 15 and tests['status'] == 'PASS')
    replay = read('REPRODUCTION.json')
    check('All three result files reproduce byte for byte', replay['status'] == 'PASS' and len(replay['files']) == 3 and all(r['before_sha256'] == r['after_sha256'] for r in replay['files']))
    for name, digest in read('artifact-hashes.json')['files'].items():
        check('sha256:' + name, (HERE / name).is_file() and sha(HERE / name) == digest)
    result = {'status': 'PASS' if all(r['status'] == 'PASS' for r in checks) else 'FAIL',
              'scope': 'Input/provenance integrity, independent arithmetic, bounded data admission, simulation consistency and code tests. Biological experiment replacement remains INCONCLUSIVE.',
              'passed': sum(r['status'] == 'PASS' for r in checks), 'total': len(checks), 'checks': checks}
    if write: (HERE / 'VERIFICATION.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(result['status'], f"{result['passed']}/{result['total']}")
    for row in checks:
        if row['status'] == 'FAIL': print(row['name'])
    return int(result['status'] != 'PASS')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--write', action='store_true')
    raise SystemExit(main(parser.parse_args().write))

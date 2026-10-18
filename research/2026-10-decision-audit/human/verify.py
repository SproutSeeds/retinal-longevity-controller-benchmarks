#!/usr/bin/env python3
"""Portable integrity and arithmetic checks; never interprets a check as biology."""
import argparse
import collections
import hashlib
import json
import math
import re
import statistics
from pathlib import Path
from extract_reference import exact_unique_lookup, join_reference
from xlsx_cells import assert_freeze

HERE = Path(__file__).resolve().parent


def load(name):
    return json.loads((HERE / name).read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path)
    parser.add_argument('--extra', type=Path)
    parser.add_argument('--write', type=Path)
    args = parser.parse_args()
    checks = []
    def check(name, value):
        checks.append({'name': name, 'status': 'PASS' if value else 'FAIL'})
    try:
        assert_freeze()
        check('Original pre-inspection contract and workbook input hashes preserved', True)
    except (ValueError, OSError):
        check('Original pre-inspection contract and workbook input hashes preserved', False)
    add = load('reference-input-addendum.json')
    manifest_bytes = (HERE / 'reference-join-manifest.json').read_bytes()
    check('Post-inspection join binding is explicit and intact', add['stage'] == 'post_numeric_inspection_input_binding_correction' and hashlib.sha256(manifest_bytes).hexdigest() == add['join_manifest']['sha256'])
    meta = load('reference-join-manifest.json')['samples']
    lookup = exact_unique_lookup(meta, 'library')
    check('807 uniquely identified human library records retained', len(meta) == len(lookup) == 807 and all(len(v) == 1 for v in lookup.values()))
    structure = load('raw-counts-structure.json')
    check('Count matrix has 807 unique count columns and no gene-length field', structure['column_count'] == 808 and structure['unique_library_columns'] == 807 and structure['columns'][0] == 'Geneid' and not structure['contains_length_column'])
    check('Every accepted metadata count column exists in count-header receipt', all(r['matrix_column'] in structure['columns'][1:] for r in meta))
    audit = load('reference-output-audit.json')
    rows = audit['reported_reference_rows']
    check('Original extraction has 1027 row occurrences', len(rows) == 1027)
    check('Every source coordinate preserves its row number', all(all(re.fullmatch(r'[A-Z]+' + str(r['row']), c) for c in r['coordinates'].values()) for r in rows))
    check('Every original reference join recomputes from bound metadata', all(join_reference(r, lookup) == r['join'] for r in rows))
    check('Source summaries recompute without dropping failed rows', all(s['prediction_rows'] == sum(r['source'] == s['source'] and r['sheet'] == s['sheet'] for r in rows) and s['joins'] == dict(collections.Counter(r['join']['status'] for r in rows if r['source'] == s['source'] and r['sheet'] == s['sheet'])) for s in audit['summary']))
    fig3 = [r for r in rows if r['source'] == 'srsf1-source-fig3.xlsx' and r['sheet'] == '3a']
    check('Fig. 3a retains all 76 unique reference IDs from six donor lines', len(fig3) == len(set(r['values']['SampleID'] for r in fig3)) == 76 and len(set(r['values']['Line'] for r in fig3)) == 6)
    check('66 exact Fig. 3a joins and 10 absent IDs', collections.Counter(r['join']['status'] for r in fig3) == {'verified_exact_library_and_metadata': 66, 'missing_library_identifier': 10})
    check('All ten unmatched validation IDs are BFP and remain unassigned', all(r['values']['Gene'] == 'BFP' and r['values']['SampleID'] not in lookup for r in fig3 if r['join']['status'] == 'missing_library_identifier'))
    recovery = load('recovery-reference-audit.json')
    ext = load('recovery-reference-addendum.json')
    check('Recovery reference extension declares post-inspection status', ext['stage'] == 'post_inspection_descriptive_extension' and recovery['analysis_status'] == 'retrospective_descriptive_audit')
    check('Recovery has 12 reference rows from three biological donor units', len(recovery['rows']) == recovery['technical_reference_rows'] == 12 and recovery['biological_units'] == 3 and len(set(r['values']['Line'] for r in recovery['rows'])) == 3)
    check('Recovery AgeDiff arithmetic independently recomputes', all(abs(r['values']['AgeDiff'] - r['values']['Predicted_age'] + r['values']['Line_age']) < 1e-10 for r in recovery['rows']))
    groups = recovery['groups']
    check('Six donor/construct groups retain two technical reference rows each', len(groups) == 6 and all(sorted(g['technical_replicates']) == [1, 2] and len(g['geo_libraries']) == 2 for g in groups))
    check('Recovery reference rows remain group-mapped without individual library joins', all(g['mapping_status'] == 'donor_construct_schedule_group_only' and g['individual_reference_to_library_join'] is False for g in groups) and all('SampleID' not in r['values'] for r in recovery['rows']))
    group_ok = True
    for g in groups:
        selected = [r['values'] for r in recovery['rows'] if r['values']['Line'] == g['line'] and r['values']['Gene'] == g['construct']]
        group_ok &= math.isclose(statistics.mean(r['Predicted_age'] for r in selected), g['mean_reported_age_years'], abs_tol=1e-12)
        genotype = 'mTagBFP2' if g['construct'] == 'BFP' else g['construct']
        expected = sorted(r['library'] for r in meta if r['donor_or_line'] == g['donor'] and r['genotype'] == genotype and r['on_days_geo'] == 5 and r['off_days_geo'] == 2)
        group_ok &= expected == g['geo_libraries']
    check('Group means and all eligible schedule memberships recompute', group_ok)
    contrasts = recovery['donor_reference_contrasts']
    contrasts_ok = True
    for contrast in contrasts:
        g = {r['construct']: r['mean_reported_age_years'] for r in groups if r['line'] == contrast['line']}
        contrasts_ok &= math.isclose(g['SRSF1'] - g['BFP'], contrast['reported_reference_srsf1_minus_bfp_years'], abs_tol=1e-12)
    contrasts_ok &= math.isclose(statistics.mean(r['reported_reference_srsf1_minus_bfp_years'] for r in contrasts), recovery['equal_donor_mean_reported_difference_years'], abs_tol=1e-12)
    check('Paired descriptive arithmetic uses three equally weighted donor means', contrasts_ok and len(contrasts) == 3)
    check('No clock replay or new inferential p-values claimed', recovery['clock_replayed'] is False and recovery['new_p_values_computed'] is False and load('clock-readiness.json')['model_executed'] is False)
    timing = load('chronology-audit.json')
    check('72 factor-off libraries include 12 timing-consistent short recovery libraries', timing['human_factor_off_libraries'] == sum(r['off_days_geo'] is not None for r in meta) == 72 and timing['agreed_schedule']['libraries'] == 12 and sum(timing['geo_schedule_counts'].values()) == 72)
    search = load('search-ledger.json')
    check('Discovery result pages match 84, 257 and 263 retrieved records', [r['retrieved_records'] for r in search['queries']] == [84, 257, 263] and all(r['complete_result_page'] for r in search['queries']) and len(search['geo_records']) == 263)
    sources = load('SOURCES.json')['sources']
    check('All retrieval records and failures retained', len(sources) == 49 and sum(r['status'] == 'retrieved' for r in sources) == 48 and all(re.fullmatch('[0-9a-f]{64}', r['sha256']) for r in sources if r['status'] == 'retrieved'))
    inventory = load('complete-workbook-inventory.json')['sheets']
    check('All 15 workbooks and 46 sheets inventoried', len(inventory) == 46 and len(set(r['source'] for r in inventory)) == 15)
    if args.cache or args.extra:
        if not args.cache or not args.extra:
            raise ValueError('Both cache paths are required for source-byte checks')
        check('All 48 downloaded source hashes match receipts', all(hashlib.sha256(((args.extra if r['retrieval_receipt'] == 'retrieval-4.json' else args.cache) / r['id']).read_bytes()).hexdigest() == r['sha256'] for r in sources if r['status'] == 'retrieved'))
    result = {'schema_version': 1, 'status': 'PASS' if all(r['status'] == 'PASS' for r in checks) else 'FAIL',
              'scope': 'Source integrity, identifier joins, and reported-reference arithmetic. Software checks do not establish rejuvenation, safety, lineage, or experiment replacement.',
              'source_byte_check': bool(args.cache), 'checks': checks, 'passed': sum(r['status'] == 'PASS' for r in checks), 'total': len(checks)}
    if args.write:
        args.write.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(result['status'], str(result['passed']) + '/' + str(result['total']))
    for r in checks:
        if r['status'] != 'PASS':
            print(r)
    raise SystemExit(0 if result['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()

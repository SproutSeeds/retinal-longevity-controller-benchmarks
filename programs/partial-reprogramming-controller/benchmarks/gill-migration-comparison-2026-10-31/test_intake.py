"""Synthetic software controls; none are observed biological measurements."""
from copy import deepcopy
import csv
import tempfile
import unittest
from pathlib import Path

from intake import HERE, evaluate, frozen, load_packet, sha


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.contract, self.pairs = frozen()
        evidence = {'schema': 'gill.migration-input/1', 'fixture_kind': 'synthetic_control',
                    'review': {'status': 'verified', 'reviewer': 'synthetic_test', 'reviewed_at': '2026-10-31', 'basis': 'synthetic controls only'},
                    'analysis_permitted': True, 'sources': [], 'excluded_pairs': {}}
        for role in ('crosswalk', 'migration', 'molecular_age'):
            p = self.base / (role + '.txt')
            p.write_text('Synthetic source for ' + role)
            evidence['sources'].append({'source_id': role, 'role': role, 'url': 'https://example.invalid/synthetic',
                                        'locator': 'synthetic', 'path': p.name, 'sha256': sha(p),
                                        'granularity': 'technical_replicate_speed' if role == 'migration' else 'synthetic'})
        self.bundle = {'base': self.base, 'evidence': evidence, 'crosswalk': [], 'migration': [], 'molecular_age': []}
        for pair in self.pairs:
            for arm, condition, speed, age in [('control', 'negative_control', 1, 50), ('treated', 'transiently_reprogrammed', 3, 40)]:
                rid = pair[arm + '_rna_id']
                context = {k: pair[k] for k in ('donor_label', 'reprogramming_days', 'experiment')}
                context.update(condition=condition, exposure_context='documented source protocol',
                               withdrawal_context='documented matched withdrawal', collection_context='documented matched collection')
                self.bundle['crosswalk'].append({**context, 'rna_id': rid, 'rna_parent_culture_id': rid + '-culture',
                                                  'function_culture_id': rid + '-culture', 'link_level': 'same_parent_culture_aliquots', 'source_id': 'crosswalk'})
                self.bundle['molecular_age'].append({'rna_id': rid, 'age_years': str(age),
                                                     'clock_id': self.contract['primary_molecular']['clock_id'], 'source_id': 'molecular_age'})
                for i in range(2):
                    self.bundle['migration'].append({**context, 'observation_id': rid + '-well-' + str(i),
                                                     'function_culture_id': rid + '-culture', 'speed': str(speed + 2*i),
                                                     'speed_units': 'um_per_hour', 'source_id': 'migration'})

    def run_case(self, bundle=None):
        return evaluate(bundle or self.bundle, allow_synthetic=True)

    def assert_deferred(self, bundle, reason):
        result = self.run_case(bundle)
        self.assertEqual(result['decision'], 'DEFERRED')
        self.assertIn(reason, result['issues'])
        self.assertEqual(result['pair_effects'], [])

    def test_hand_calculated_effects_and_duration_donor_counts(self):
        result = self.run_case()
        self.assertEqual(result['decision'], 'READY_FOR_DESCRIPTIVE_COMPARISON')
        self.assertEqual(result['input_kind'], 'synthetic_control')
        self.assertFalse(result['biological_validation'])
        self.assertEqual(len(result['pair_effects']), 13)
        for row in result['pair_effects']:
            self.assertEqual(row['delta_age_years'], -10)
            self.assertEqual(row['delta_speed_um_per_hour'], 2)
        counts = {r['reprogramming_days']: r['independent_donor_count'] for r in result['duration_summaries']}
        self.assertEqual(counts, {10: 3, 13: 2, 15: 1, 17: 3})
        one_donor = next(r for r in result['duration_summaries'] if r['reprogramming_days'] == 15)
        self.assertEqual(one_donor['leave_one_donor_out'], [])

    def test_empty_observed_intake_stays_deferred(self):
        result = evaluate(load_packet(HERE, templates=True))
        self.assertEqual(result['decision'], 'DEFERRED')
        self.assertEqual(result['migration_observations_received'], 0)
        self.assertEqual(result['pair_effects'], [])

    def test_synthetic_requires_explicit_test_path(self):
        result = evaluate(self.bundle)
        self.assertIn('synthetic_not_observed_evidence', result['issues'])
        self.assertEqual(result['pair_effects'], [])

    def test_every_context_field_must_match(self):
        for field in self.contract['unit_policy']['context_fields']:
            with self.subTest(field=field):
                case = deepcopy(self.bundle)
                case['migration'][0][field] = 'different'
                self.assert_deferred(case, 'rna_function_context_mismatch')

    def test_no_row_order_or_donor_only_join(self):
        for level in ('row_order', 'donor_only', 'condition_only', ''):
            case = deepcopy(self.bundle)
            case['crosswalk'][0]['link_level'] = level
            self.assert_deferred(case, 'link_level_not_admitted')

    def test_reused_observation_or_culture_is_rejected(self):
        case = deepcopy(self.bundle)
        case['migration'].append(case['migration'][0])
        self.assert_deferred(case, 'observation_reused_or_missing')
        case = deepcopy(self.bundle)
        case['crosswalk'][1]['function_culture_id'] = case['crosswalk'][0]['function_culture_id']
        self.assert_deferred(case, 'rna_or_culture_reused')

    def test_value_unit_clock_and_summary_substitution_rejected(self):
        for field, value, reason in [('speed', 'NaN', 'migration_value_invalid'),
                                     ('speed', 'inf', 'migration_value_invalid'), ('speed_units', 'pixels_per_hour', 'migration_units_incompatible')]:
            case = deepcopy(self.bundle)
            case['migration'][0][field] = value
            self.assert_deferred(case, reason)
        case = deepcopy(self.bundle)
        case['molecular_age'][0]['clock_id'] = 'alternate_clock'
        self.assert_deferred(case, 'molecular_clock_mismatch')
        case = deepcopy(self.bundle)
        case['evidence']['sources'][1]['granularity'] = 'culture_summary'
        self.assert_deferred(case, 'migration_granularity_not_admitted')

    def test_signed_edge_slopes_and_unfavorable_directions_are_retained(self):
        case = deepcopy(self.bundle)
        for row in case['migration']:
            if row['condition'] == 'transiently_reprogrammed':
                row['speed'] = '-1'
        for row in case['molecular_age']:
            row['age_years'] = '50'
        result = self.run_case(case)
        self.assertEqual(result['decision'], 'READY_FOR_DESCRIPTIVE_COMPARISON')
        self.assertTrue(all(not r['molecular_lower'] and not r['migration_higher'] for r in result['pair_effects']))
        self.assertTrue(all(r['delta_speed_um_per_hour'] == -3 for r in result['pair_effects']))

    def test_provenance_permissions_and_missing_review(self):
        case = deepcopy(self.bundle)
        case['evidence']['analysis_permitted'] = False
        self.assert_deferred(case, 'analysis_permission_unresolved')
        case = deepcopy(self.bundle)
        case['evidence']['review']['status'] = 'pending'
        self.assert_deferred(case, 'source_and_coverage_review_pending')
        case = deepcopy(self.bundle)
        case['evidence']['sources'][0]['sha256'] = '0'*64
        self.assert_deferred(case, 'source_hash_mismatch')
        case = deepcopy(self.bundle)
        case['evidence']['sources'][0]['path'] = '../outside.txt'
        self.assert_deferred(case, 'source_path_invalid')

    def test_missing_pair_cannot_be_silently_dropped(self):
        case = deepcopy(self.bundle)
        case['molecular_age'].pop()
        self.assert_deferred(case, 'pair_coverage_unresolved:' + self.pairs[-1]['pair_id'])

    def test_donor_weights_and_leave_one_out_are_not_pair_weights(self):
        case = deepcopy(self.bundle)
        excluded = next(p for p in self.pairs if p['pair_id'] == 'O2-d13-e2')
        rids = {excluded['control_rna_id'], excluded['treated_rna_id']}
        case['crosswalk'] = [r for r in case['crosswalk'] if r['rna_id'] not in rids]
        case['molecular_age'] = [r for r in case['molecular_age'] if r['rna_id'] not in rids]
        case['migration'] = [r for r in case['migration'] if r['function_culture_id'] not in {rid+'-culture' for rid in rids}]
        case['evidence']['excluded_pairs'][excluded['pair_id']] = {'reason': 'Synthetic missing culture control', 'source_id': 'crosswalk'}
        target = next(p['treated_rna_id'] for p in self.pairs if p['pair_id'] == 'O3-d13-e2')
        for row in case['migration']:
            if row['function_culture_id'] == target + '-culture':
                row['speed'] = str(float(row['speed']) + 6)
        result = self.run_case(case)
        self.assertEqual(result['decision'], 'READY_FOR_DESCRIPTIVE_COMPARISON')
        summary = next(r for r in result['duration_summaries'] if r['reprogramming_days'] == 13)
        self.assertEqual(summary['independent_donor_count'], 2)
        self.assertEqual(summary['mean_delta_speed_um_per_hour'], 3.5)
        loo = {r['excluded_donor']: r['delta_speed_um_per_hour'] for r in summary['leave_one_donor_out']}
        self.assertEqual(loo, {'O2': 5, 'O3': 2})

    def test_parent_sibling_and_control_collection_rules(self):
        case = deepcopy(self.bundle)
        case['crosswalk'][0]['rna_parent_culture_id'] = 'different'
        self.assert_deferred(case, 'same_parent_id_mismatch')
        case['crosswalk'][0]['link_level'] = 'explicitly_matched_sibling_cultures'
        self.assertEqual(self.run_case(case)['decision'], 'READY_FOR_DESCRIPTIVE_COMPARISON')
        case = deepcopy(self.bundle)
        case['crosswalk'][1]['collection_context'] = 'different'
        cid = case['crosswalk'][1]['function_culture_id']
        for row in case['migration']:
            if row['function_culture_id'] == cid:
                row['collection_context'] = 'different'
        self.assert_deferred(case, 'control_treated_collection_mismatch')

    def test_schema_loader_rejects_shifted_columns(self):
        for table in self.contract['table_columns']:
            (self.base/(table+'.tsv')).write_text('wrong\tcolumns\n')
        with self.assertRaisesRegex(ValueError, 'Unexpected TSV columns'):
            load_packet(self.base)


if __name__ == '__main__':
    unittest.main()

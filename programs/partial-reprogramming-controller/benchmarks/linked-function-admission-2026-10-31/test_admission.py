import copy
import json
from pathlib import Path
import unittest

from admission import evaluate
from audit_sources import gill_pairs

HERE = Path(__file__).resolve().parent


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads((HERE / 'ADMISSION_CONTRACT.json').read_text())
        # Synthetic positive control exercises the gate. It is never included
        # in CANDIDATES.json or counted as an observed biological admission.
        context = {name: 'explicit_source_context' for name in self.contract['required_comparison_fields']}
        self.fixture = {'candidate_id': 'SYNTHETIC_GATE_CONTROL', 'system': 'adult_primary',
                        'evidence': {name: 'verified' for name in self.contract['required_evidence']},
                        'link_level': 'explicitly_matched_sibling_cultures',
                        'unit_crosswalk_authority': {'url': 'https://example.org/synthetic-fixture',
                                                     'locator': 'synthetic-only table', 'sha256': 'a' * 64},
                        'unit_crosswalk': [{'rna': dict(context, sample_id='RNA-A'),
                                            'function': dict(context, observation_id='FUNCTION-A',
                                                             measurement_kind='direct_function')}]}

    def check_rejected(self, fixture):
        self.assertFalse(evaluate(fixture, self.contract)['joint_analysis_admitted'])

    def test_synthetic_acceptance_control_is_separate_from_observed_roster(self):
        result = evaluate(self.fixture, self.contract)
        self.assertTrue(result['joint_analysis_admitted'])
        self.assertEqual(result['independent_donors'], 1)
        self.assertNotIn(self.fixture['candidate_id'], (HERE / 'CANDIDATES.json').read_text())

    def test_row_order_condition_and_donor_only_links_are_rejected(self):
        for level in self.contract['insufficient_link_levels']:
            changed = dict(self.fixture, link_level=level)
            with self.subTest(level=level):
                self.check_rejected(changed)

    def test_missing_or_mismatched_dose_timing_donor_and_culture_are_rejected(self):
        for field in self.contract['required_comparison_fields']:
            for value in ['', 'different_context']:
                changed = copy.deepcopy(self.fixture)
                changed['unit_crosswalk'][0]['function'][field] = value
                with self.subTest(field=field, value=value):
                    self.check_rejected(changed)

    def test_unverified_evidence_and_unbound_crosswalk_are_rejected(self):
        for field in self.contract['required_evidence']:
            changed = copy.deepcopy(self.fixture)
            changed['evidence'][field] = 'unresolved'
            self.check_rejected(changed)
        self.check_rejected(dict(self.fixture, unit_crosswalk_authority=None))
        self.check_rejected(dict(self.fixture, unit_crosswalk=[]))

    def test_stem_cell_and_reprogrammed_descendant_scopes_stay_distinct(self):
        stem = evaluate(dict(self.fixture, system='pluripotent_derived'), self.contract)
        self.assertEqual(stem['decision'], 'joint_support_only')
        self.assertFalse(stem['adult_primary_admitted'])
        descendant = evaluate(dict(self.fixture, system='adult_primary_reprogrammed_descendants'), self.contract)
        self.assertEqual(descendant['decision'], 'joint_adult_origin_descendant_only')
        self.assertFalse(descendant['adult_primary_admitted'])
        self.check_rejected(dict(self.fixture, system='unknown'))

    def test_biomarkers_reused_observations_and_continuity_promotion_are_rejected(self):
        changed = copy.deepcopy(self.fixture)
        changed['unit_crosswalk'][0]['function']['measurement_kind'] = 'protein_biomarker'
        self.check_rejected(changed)
        changed = copy.deepcopy(self.fixture)
        changed['unit_crosswalk'] *= 2
        self.check_rejected(changed)
        self.check_rejected(dict(self.fixture, same_cell_continuity_claim=True))

    def test_within_rna_pairing_requires_complete_explicit_unique_labels(self):
        rows = [{'sample_id': 'RNA-C', 'title': 'O1_negative_control_13days_exp1',
                 'characteristics': ['donor age (years): 53']},
                {'sample_id': 'RNA-T', 'title': 'O1_transiently_reprogrammed_13days_exp1',
                 'characteristics': ['donor age (years): 53']}]
        pairs = gill_pairs(rows)
        self.assertEqual(len(pairs), 1)
        self.assertFalse(pairs[0]['joint_function_admitted'])
        self.assertEqual(gill_pairs(rows[:1]), [])
        self.assertEqual(gill_pairs([rows[0], dict(rows[1], title='O2_transiently_reprogrammed_13days_exp1')]), [])
        with self.assertRaises(ValueError):
            gill_pairs(rows + [rows[1]])
        with self.assertRaises(ValueError):
            gill_pairs([rows[0], dict(rows[1], characteristics=['donor age (years): 38'])])


if __name__ == '__main__':
    unittest.main()

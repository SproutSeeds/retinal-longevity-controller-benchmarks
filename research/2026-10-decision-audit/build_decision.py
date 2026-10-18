#!/usr/bin/env python3
"""Assemble the narrow decision from saved calculations and named dependencies."""
import argparse
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def build():
    human = json.loads((HERE / 'human/recovery-reference-audit.json').read_text())
    recovery = json.loads((HERE / 'recovery/decision.json').read_text())
    assignment = json.loads((HERE / 'assignment/results.json').read_text())
    with (HERE / 'ocular/results/contrasts.csv').open(newline='') as stream:
        mouse = next(r for r in csv.DictReader(stream) if r['panel']=='cycle_panel' and r['method']=='CPM')
    return {
        'schema':'cx004-integrated-decision/v1', 'date':'2026-10-18',
        'decision_claim_level':'Heuristic',
        'calculation_claim_level':'Verified within the named arithmetic and provenance checks',
        'stage':'newly_admitted_computations_complete_specific_input_dependencies_remain',
        'experiment_replacement':'INCONCLUSIVE',
        'readouts':{f'CX004-R0{i}':'insufficient_signal' for i in range(1,5)},
        'public_search_universal_exhaustion_claim':False,
        'unconditional_wetlab_necessity_proven':False,
        'retinal_efficacy_established':False,
        'new_wetlab_purchase_or_arrangement':False,
        'paid_compute_used':False,
        'new_independent_clock_replay_completed':False,
        'new_observed_data_generated':False,
        'computations_completed':[
            {'id':'human_reference', 'kind':'published_prediction_arithmetic',
             'biological_donors':human['biological_units'],
             'technical_reference_rows':human['technical_reference_rows'],
             'schedule_days':{'induction':human['induction_days'],'off':human['off_days']},
             'srsf1_minus_bfp_model_years':human['equal_donor_mean_reported_difference_years'],
             'individual_prediction_to_library_join':False,
             'artifact':'human/recovery-reference-audit.json'},
            {'id':'independent_mouse', 'kind':'public_counts_independent_fixed_panel_analysis',
             'treated_animals':int(mouse['n_OSK']), 'control_animals':int(mouse['n_GFP']),
             'cycle_primary_difference':float(mouse['delta']),
             'conditional_permutation_p':float(mouse['p']),
             'four_test_holm_p':float(mouse['holm_p']),
             'animal_batch_map_available':False, 'artifact':'ocular/results/contrasts.csv'},
            {'id':'assignment_recheck', 'kind':'fresh_source_hash_comparison',
             'source_unchanged':assignment['workbook_unchanged'],
             'artifact':'assignment/results.json'}
        ],
        'remaining_inputs':[
            {'id':'xu_withdrawal', 'existing_design_found':recovery['new_existing_experiment_found'],
             'status':'requires_verified_assignment_and_timing',
             'artifact':'recovery/decision.json'},
            {'id':'retinal_historical_clock', 'status':'requires_historical_pipeline_preprocessing_and_joins',
             'artifact':'NEXT_STEPS.md'},
            {'id':'human_clock_replay', 'status':'requires_preprocessing_reference_and_sample_binding',
             'artifact':'human/REPORT.md'},
            {'id':'large_perturbation_screen', 'status':assignment['status'],
             'artifact':'assignment/results.json'}
        ],
        'conditional_measurement_requirement':
            'For the intended matched human claim, acquire new measurements only if compatible existing observations cannot be recovered; banked material may reduce culture work but still requires an assay.',
        'retinal_bridge_requirement':
            'A relevant ocular system, appropriate function and endpoint-specific sample joins are additional requirements.',
        'synthetic_scope':
            'Design and software stress tests; no substitution for observations, sample identity, recovery or biological safety labels.',
        'model_training_disposition':
            'No new rejuvenation or safety predictor: trustworthy target labels and independent donor/study-held-out validation remain prerequisites.',
        'reopen_rule':
            'A changed public source or supplied exact input passes provenance, identity, chronology, reuse and design admission before new outcomes are analyzed.',
    }


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--write',action='store_true')
    args=p.parse_args()
    result=build()
    if args.write:
        (HERE/'decision.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    elif result!=json.loads((HERE/'decision.json').read_text()):
        raise SystemExit('FAIL: integrated decision differs from saved evidence')
    print('PASS: integrated decision; experiment replacement INCONCLUSIVE')

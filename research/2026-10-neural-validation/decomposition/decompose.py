#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["rdata==1.1.0", "numpy==2.5.4", "pandas==3.0.6", "scipy==1.18.1"]
# ///
"""Exact decomposition of a conditional cell-average score, not pseudobulk."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'analysis'))
from neural_analysis import (aggregate, load_cohort2, panel_coverage, require_freeze,
                             save_json, sha, support_failures)


def symmetric(p_t, p_c, mu_t, mu_c):
    arrays = [np.asarray(x, dtype=float) for x in [p_t, p_c, mu_t, mu_c]]
    if any(x.ndim != 1 or not x.size or not np.isfinite(x).all() for x in arrays):
        raise ValueError('Finite nonempty vectors are required')
    if len({x.shape for x in arrays}) != 1:
        raise ValueError('Common support must have identical dimensions')
    p_t, p_c, mu_t, mu_c = arrays
    if any((x < 0).any() or abs(x.sum() - 1) > 1e-12 for x in [p_t, p_c]):
        raise ValueError('Fractions must be nonnegative and sum to one')
    total = float(p_t @ mu_t - p_c @ mu_c)
    comp = .5 * (p_t - p_c) * (mu_t + mu_c)
    within = .5 * (p_t + p_c) * (mu_t - mu_c)
    error = abs(total - float(comp.sum() + within.sum()))
    if error > 1e-10:
        raise ValueError('Decomposition arithmetic identity failed')
    return {'total': total, 'composition': float(comp.sum()),
            'within_type': float(within.sum()), 'composition_by_type': comp.tolist(),
            'within_by_type': within.tolist(), 'identity_error': error,
            'opposed_components': bool(comp.sum() * within.sum() < 0)}


def run(raw, contract, orthology):
    named = contract['cell_types']['named']
    pb = aggregate(raw, named + contract['cell_types']['unresolved'])
    qc = {(r['animal_id'], r['celltype']): r for r in pb.qc}
    panels = panel_coverage(orthology, raw.genes, contract['thresholds'])
    pairs = contract['cohort2_primary']['pairs']
    animals = [a for p in pairs for a in [p['treated'], p['control']]]
    meta = raw.metadata
    library = np.asarray(raw.counts.sum(axis=0)).ravel()
    support_rows, outputs = [], []
    for floor in [20, 10]:
        failure = {ct: {a: support_failures(qc[(a, ct)], floor, 500) for a in animals}
                   for ct in named}
        common = [ct for ct in named if not any(failure[ct].values())]
        retained_mask = meta['celltype'].isin(common).to_numpy()
        denominators = {}
        for a in animals:
            animal = (meta['animal_id'] == a).to_numpy()
            retained = int((animal & retained_mask).sum())
            total = int(animal.sum())
            denominators[a] = {'retained_cells': retained, 'all_recovered_cells': total,
                               'excluded_cells': total - retained,
                               'retained_fraction': retained / total,
                               'counts_by_retained_type': {ct: qc[(a, ct)]['cells'] for ct in common}}
        support_rows.append({'cell_floor': floor, 'gene_floor': 500, 'common_named_types': common,
                             'all_type_support_failures': failure, 'denominators': denominators})
        for name, panel in panels.items():
            if not common or panel['failures']:
                for scale in [10000, 1000000]:
                    outputs.append({'cell_floor': floor, 'panel': name, 'scale': scale,
                                    'status': 'unavailable',
                                    'reason': 'empty_common_support' if not common else panel['failures']})
                continue
            selected = raw.counts[panel['indices'], :].toarray().astype(float)
            for scale in [10000, 1000000]:
                scores = np.log2(1 + scale * selected / library).mean(axis=0)
                means, fractions, direct = {}, {}, {}
                for a in animals:
                    animal = (meta['animal_id'] == a).to_numpy()
                    means[a] = [float(scores[animal & (meta['celltype'] == ct).to_numpy()].mean()) for ct in common]
                    fractions[a] = [qc[(a, ct)]['cells'] / denominators[a]['retained_cells'] for ct in common]
                    direct[a] = float(scores[animal & retained_mask].mean())
                    if abs(np.asarray(fractions[a]) @ means[a] - direct[a]) > 1e-10:
                        raise ValueError('Weighted type means differ from direct cell average')
                lanes = []
                for pair in pairs:
                    t, c = pair['treated'], pair['control']
                    values = symmetric(fractions[t], fractions[c], means[t], means[c])
                    direct_delta = direct[t] - direct[c]
                    if abs(values['total'] - direct_delta) > 1e-10:
                        raise ValueError('Direct cell-average contrast mismatch')
                    lanes.append({**pair, **values, 'direct_cell_average_difference': direct_delta,
                                  'fractions_treated': fractions[t], 'fractions_control': fractions[c],
                                  'means_treated': means[t], 'means_control': means[c]})
                average = {field: float(np.mean([x[field] for x in lanes]))
                           for field in ['total', 'composition', 'within_type']}
                outputs.append({'cell_floor': floor, 'panel': name, 'scale': scale, 'status': 'available',
                                'common_types': common, 'panel_genes': panel['present_mouse_genes'],
                                'lane_contrasts': lanes, 'equal_lane_mean': average,
                                'authority': 'Conditional cell-average log expression; not a pseudobulk decomposition.'})
    return {'claim_level': 'Verified', 'evidence_class': 'observed_recovered_cell_descriptive_algebra',
            'source_sha256': raw.source_sha256, 'support': support_rows, 'results': outputs,
            'interpretation': 'Composition and within-type components are an exact algebraic partition of this conditional summary. Neither is causal, calibrated biological benefit, or unbiased tissue abundance.',
            'within_type_limit': 'Within a named type, subtype/state mixture and capture effects remain possible.',
            'synthetic_data_in_observed_results': False}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--cache', type=Path, required=True)
    p.add_argument('--replay-frozen-hashes', action='store_true')
    p.add_argument('--output', type=Path, default=HERE / 'results.json')
    args = p.parse_args()
    root = HERE.parent
    freeze = json.loads((root / 'FREEZE.json').read_text())
    if sha(HERE / 'contract.json') != freeze['decomposition_contract_sha256']:
        raise ValueError('Decomposition contract changed since the prospective freeze')
    if args.replay_frozen_hashes:
        for field, filename in [('contract_sha256', 'contract.json'), ('orthology_sha256', 'orthology.json')]:
            if sha(root / 'analysis' / filename) != freeze[field]:
                raise ValueError('Frozen input mismatch')
        if freeze.get('expression_execution_authorized') is not True:
            raise ValueError('Missing original execution authorization')
    else:
        require_freeze(root / 'FREEZE.json', root / 'analysis/contract.json', root / 'analysis/orthology.json')
        git_root = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=HERE, text=True).strip())
        relative = (HERE / 'contract.json').relative_to(git_root).as_posix()
        committed = subprocess.check_output(['git', 'show', f"{freeze['commit']}:{relative}"], cwd=git_root)
        if hashlib.sha256(committed).hexdigest() != freeze['decomposition_contract_sha256']:
            raise ValueError('Committed decomposition contract differs from the frozen hash')
    contract = json.loads((root / 'analysis/contract.json').read_text())
    orthology = json.loads((root / 'analysis/orthology.json').read_text())
    result = run(load_cohort2(args.cache), contract, orthology)
    result['contract_sha256'] = sha(HERE / 'contract.json')
    result['code_sha256'] = sha(Path(__file__))
    result['analysis_loader_sha256'] = sha(root / 'analysis/neural_analysis.py')
    save_json(args.output, result)
    print('PASS: descriptive decomposition;', len(result['results']), 'panel/support/scale rows')


if __name__ == '__main__':
    main()

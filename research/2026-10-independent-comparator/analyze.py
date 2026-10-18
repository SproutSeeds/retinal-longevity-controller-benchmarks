#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["numpy==2.5.4", "pandas==3.0.6", "scipy==1.18.1", "matplotlib==3.11.2"]
# ///
"""Frozen human expression comparison and explicitly synthetic sampling scenarios."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd
from scipy.special import roots_jacobi

HERE = Path(__file__).resolve().parent


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + '\n')


def checked(cache, name):
    entries = []
    for path in sorted(HERE.glob('retrieval*.json')):
        entries.extend(row for row in json.loads(path.read_text()).get('sources', [])
                       if row.get('status') == 'retrieved' and row['id'] == name)
    if not entries or len({x['sha256'] for x in entries}) != 1:
        raise ValueError('Missing or conflicting source receipt: ' + name)
    path = cache / name
    if not path.is_file() or sha(path) != entries[0]['sha256']:
        raise ValueError('Missing or changed source: ' + name)
    return path


def soft_samples(text):
    records = []
    for chunk in text.split('^SAMPLE = ')[1:]:
        lines = chunk.splitlines()
        row = {'accession': lines[0].strip()}
        for line in lines[1:]:
            if line.startswith('!Sample_') and ' = ' in line:
                key, value = line[len('!Sample_'):].split(' = ', 1)
                row.setdefault(key, []).append(value)
        records.append(row)
    if not records or len({r['accession'] for r in records}) != len(records):
        raise ValueError('Missing or duplicate GEO samples')
    return records


def human_join(samples, columns):
    if len(columns) != 8 or len(set(columns)) != 8 or len(samples) != 8:
        raise ValueError('Expected exactly eight unique columns and samples')
    rows = []
    for sample in samples:
        descriptions = [x.split(': ', 1)[1] for x in sample.get('description', [])
                        if x.startswith('Column name in raw_counts_matrix.csv: ')]
        if len(descriptions) != 1:
            raise ValueError('Missing or ambiguous metadata column key')
        declared = descriptions[0]
        match = re.fullmatch(r'(OSK|O4YRSK)_([04])D_([12])', declared)
        if not match:
            raise ValueError('Unadmitted alias: ' + declared)
        construct, day, replicate = match.groups()
        resolved = f'{construct}_D{day}_{replicate}'
        if re.sub(r'_D([04])_', r'_\1D_', resolved) != declared:
            raise ValueError('Alias is not reversible')
        condition = 'dox' if day == '4' else 'no dox'
        expected_title = f'{construct}, {condition}, 4 days, rep{replicate}'
        characteristics = dict(x.split(': ', 1) for x in sample['characteristics_ch1'] if ': ' in x)
        if sample['title'] != [expected_title] or characteristics.get('treatment') != f'{construct}, {condition}, 4 days':
            raise ValueError('Title/characteristic/alias disagreement')
        if sample['organism_ch1'] != ['Homo sapiens'] or characteristics.get('cell line') != 'GM00731':
            raise ValueError('Unexpected species or donor')
        rows.append({'accession': sample['accession'], 'title': expected_title,
                     'metadata_column': declared, 'matrix_column': resolved,
                     'construct': construct, 'condition': condition, 'library_replicate_label': replicate,
                     'donor': 'GM00731', 'batch_label': characteristics.get('batch'),
                     'exact_string_match': declared == resolved,
                     'time_interpretation': 'GEO title says four days; D0 is retained as a column token, not a harvest-time inference.'})
    keys = [x['matrix_column'] for x in rows]
    if len(set(keys)) != 8 or set(keys) != set(columns):
        raise ValueError('Aliased join does not cover matrix one-to-one')
    return sorted(rows, key=lambda r: r['accession'])


def validate_counts(frame):
    x = frame.to_numpy(dtype=float)
    if frame.columns.has_duplicates or frame.index.has_duplicates or frame.index.isna().any():
        raise ValueError('Duplicate or missing count identifier')
    if x.ndim != 2 or not np.isfinite(x).all() or (x < 0).any() or (x.sum(axis=0) <= 0).any():
        raise ValueError('Invalid count values or empty library')
    return x


def normalizations(frame):
    x = validate_counts(frame)
    totals = x.sum(axis=0)
    positive = x[(x > 0).all(axis=1)]
    if len(positive) == 0:
        raise ValueError('No positive genes for median-ratio sensitivity')
    geometric_means = np.exp(np.log(positive).mean(axis=1))
    factors = np.median(positive / geometric_means[:, None], axis=0)
    factors /= np.exp(np.log(factors).mean())
    effective_depth = factors * np.exp(np.log(totals).mean())
    transforms = {
        'log2_cpm': pd.DataFrame(np.log2(1 + x / totals * 1e6), index=frame.index, columns=frame.columns),
        'log2_median_ratio_cpm_equivalent': pd.DataFrame(np.log2(1 + x / effective_depth * 1e6), index=frame.index, columns=frame.columns),
    }
    return transforms, totals, factors, len(positive)


def approved_gene_map(path, symbols):
    found = {symbol: [] for symbol in symbols}
    with path.open() as stream:
        for row in csv.DictReader(stream, delimiter='\t'):
            if row['symbol'] in found and row['status'] == 'Approved':
                found[row['symbol']].append({'symbol': row['symbol'], 'hgnc_id': row['hgnc_id'],
                                            'ensembl_gene_id': row['ensembl_gene_id']})
    for symbol, matches in found.items():
        if len(matches) != 1 or not re.fullmatch(r'ENSG\d+', matches[0]['ensembl_gene_id']):
            raise ValueError('Ambiguous or missing approved gene mapping: ' + symbol)
    result = {symbol: matches[0] for symbol, matches in found.items()}
    if len({row['ensembl_gene_id'] for row in result.values()}) != len(result):
        raise ValueError('Multiple panel symbols map to the same gene')
    return result


def compare_panel(values, treated, controls):
    scores = values.mean(axis=0)
    effect = float(scores[treated].mean() - scores[controls].mean())
    combinations = [float(scores[t] - scores[c]) for t, c in itertools.product(treated, controls)]
    omissions = {gene: float(values.drop(index=gene)[treated].mean().mean() - values.drop(index=gene)[controls].mean().mean())
                 for gene in values.index}
    return {'mean_difference': effect, 'library_scores': {k: float(v) for k, v in scores.items()},
            'four_library_differences': combinations, 'single_gene_omission_differences': omissions,
            'pairwise_range': [min(combinations), max(combinations)],
            'omission_range': [min(omissions.values()), max(omissions.values())],
            'all_four_pairs_share_mean_sign': bool(all(np.sign(x) == np.sign(effect) for x in combinations)),
            'all_omissions_share_mean_sign': bool(all(np.sign(x) == np.sign(effect) for x in omissions.values()))}


def human(cache):
    contract = json.loads((HERE / 'analysis-contract.json').read_text())
    path = checked(cache, 'GSE297233_raw_counts_matrix.csv.gz')
    with gzip.open(path, 'rt') as stream:
        header = next(csv.reader(stream))
    if len(header) != len(set(header)):
        raise ValueError('Duplicate source header before pandas parsing')
    raw = pd.read_csv(path, index_col=0)
    original_ids = raw.index.tolist()
    raw.index = raw.index.str.replace(r'\.\d+$', '', regex=True)
    validate_counts(raw)
    samples = human_join(soft_samples(checked(cache, 'GSE297233-samples.txt').read_text()), raw.columns.tolist())
    all_panels = json.loads((HERE / 'panels.json').read_text())
    panels = {key: all_panels[key] for key in ['fibroblast_identity', 'cycle_panel', 'stress_panel', 'reprogramming_state']}
    panels['reprogramming_without_OSK_overlap'] = [g for g in panels['reprogramming_state'] if g not in ['POU5F1', 'SOX2']]
    symbols = sorted(set(itertools.chain.from_iterable(panels.values())))
    mapping = approved_gene_map(checked(cache, 'hgnc_complete_set.txt'), symbols)
    transforms, totals, factors, positive_count = normalizations(raw)
    missing = [g for g in symbols if mapping[g]['ensembl_gene_id'] not in raw.index]
    panel_genes = {name: [g for g in genes if g not in missing] for name, genes in panels.items()}
    for name, genes in panel_genes.items():
        if len(genes) / len(panels[name]) < contract['human']['minimum_panel_coverage']:
            raise ValueError('Insufficient panel coverage: ' + name)
    gene_values = {}
    for method, values in transforms.items():
        gene_values[method] = {g: {k: float(v) for k, v in values.loc[mapping[g]['ensembl_gene_id']].items()}
                               for g in symbols if g not in missing}
    contrasts = []
    for construct in ['OSK', 'O4YRSK']:
        treated = [r['matrix_column'] for r in samples if r['construct'] == construct and r['condition'] == 'dox']
        controls = [r['matrix_column'] for r in samples if r['construct'] == construct and r['condition'] == 'no dox']
        if len(treated) != 2 or len(controls) != 2:
            raise ValueError('Expected two libraries per group')
        for name, genes in panel_genes.items():
            methods = {method: compare_panel(pd.DataFrame({g: gene_values[method][g] for g in genes}).T, treated, controls)
                       for method in transforms}
            contrasts.append({'construct': construct, 'panel': name, 'genes': genes,
                              'missing_genes': sorted(set(panels[name]) - set(genes)),
                              'transgene_overlap': sorted(set(genes) & {'POU5F1', 'SOX2'}), 'methods': methods,
                              'normalization_signs_agree': bool(len({int(np.sign(m['mean_difference'])) for m in methods.values()}) == 1)})
    result = {'claim_level': 'Heuristic', 'computation_level': 'Verified', 'evidence_class': 'derived_observed',
              'contract_sha256': sha(HERE / 'analysis-contract.json'), 'join_amendment_sha256': sha(HERE / 'join-amendment.json'),
              'source_sha256': sha(path), 'hgnc_sha256': sha(checked(cache, 'hgnc_complete_set.txt')),
              'rows': len(raw), 'libraries': len(raw.columns), 'independent_donors': 1,
              'version_suffix_changes': sum(a != b for a, b in zip(original_ids, raw.index)),
              'fractional_count_entries': int((raw.to_numpy() % 1 != 0).sum()),
              'sample_manifest': samples, 'gene_map': mapping, 'missing_genes': missing,
              'normalization_positive_genes': positive_count,
              'library_qc': [{'column': col, 'count_sum': float(totals[i]), 'detected_genes': int((raw[col] > 0).sum()),
                              'median_ratio_size_factor': float(factors[i])} for i, col in enumerate(raw.columns)],
              'gene_values': gene_values, 'contrasts': contrasts,
              'independent_study_validation': False,
              'authority': 'Different-intervention, single-donor expression comparator; no age, safety, retinal function or withdrawal-recovery validation.',
              'readouts': {f'CX004-R0{i}': 'insufficient_signal' for i in range(1, 5)}}
    save('human-results.json', result)
    for row in contrasts:
        print(row['construct'], row['panel'], {k: round(v['mean_difference'], 4) for k, v in row['methods'].items()})
    print('Human matrix:', len(raw), 'genes;', len(raw.columns), 'libraries; 1 donor')


def no_flag_probability(n, prevalence, rho, sensitivity, fpr, nodes=256):
    if n <= 0 or not 0 <= prevalence <= 1 or not 0 <= rho < 1 or not 0 <= sensitivity <= 1 or not 0 <= fpr <= 1:
        raise ValueError('Invalid synthetic sampling parameter')
    if sensitivity == fpr:
        return float((1 - fpr) ** n)
    if prevalence in [0, 1] or rho == 0:
        q = sensitivity * prevalence + fpr * (1 - prevalence)
        return float((1 - q) ** n)
    concentration = 1 / rho - 1
    a, b = prevalence * concentration, (1 - prevalence) * concentration
    x, w = roots_jacobi(nodes, b - 1, a - 1)
    p = (x + 1) / 2
    q = sensitivity * p + fpr * (1 - p)
    return float(np.dot(w / w.sum(), (1 - q) ** n))


def confirmation(no_flags):
    q = np.asarray(no_flags, dtype=float)
    if len(q) < 1 or not np.isfinite(q).all() or (q < 0).any() or (q > 1).any():
        raise ValueError('Invalid donor no-flag probabilities')
    zero = np.prod(q)
    one = sum((1 - q[i]) * np.prod(np.delete(q, i)) for i in range(len(q)))
    return {'any_donor_flagged': float(np.clip(1 - zero, 0, 1)),
            'two_or_more_donors_flagged': float(np.clip(1 - zero - one, 0, 1))}


def synthetic():
    config = json.loads((HERE / 'analysis-contract.json').read_text())['synthetic']
    rows, nulls, errors = [], [], []
    for allocation, p, rho, specificity in itertools.product(config['allocations'], config['prevalences'],
                                                            config['latent_donor_correlations'], config['specificities']):
        q = [no_flag_probability(n, p, rho, config['sensitivity'], 1 - specificity) for n in allocation]
        q2 = [no_flag_probability(n, p, rho, config['sensitivity'], 1 - specificity, nodes=512) for n in allocation]
        errors.append(float(np.max(np.abs(np.array(q) - q2))))
        rows.append({'allocation': allocation, 'prevalence': p, 'latent_donor_correlation': rho,
                     'specificity': specificity, 'sensitivity': config['sensitivity'], **confirmation(q)})
    for allocation, specificity, rho in itertools.product(config['allocations'], config['specificities'], [0, 0.01]):
        q = [no_flag_probability(n, 1 - specificity, rho, 1, 0) for n in allocation]
        q2 = [no_flag_probability(n, 1 - specificity, rho, 1, 0, nodes=512) for n in allocation]
        errors.append(float(np.max(np.abs(np.array(q) - q2))))
        nulls.append({'allocation': allocation, 'true_prevalence': 0, 'specificity': specificity,
                      'false_positive_donor_correlation': rho, **confirmation(q)})
    rng = np.random.default_rng(config['seed'])
    n_trials = 100000
    allocation = np.array([1000, 100, 100])
    p, rho, fpr, sensitivity = 0.01, 0.05, 0.001, 0.8
    a, b = p * (1 / rho - 1), (1 - p) * (1 / rho - 1)
    latent = rng.beta(a, b, size=(n_trials, len(allocation)))
    hits = rng.binomial(allocation, sensitivity * latent + fpr * (1 - latent)) > 0
    mc = {'any_donor_flagged': float((hits.sum(1) >= 1).mean()),
          'two_or_more_donors_flagged': float((hits.sum(1) >= 2).mean())}
    exact = confirmation([no_flag_probability(int(n), p, rho, sensitivity, fpr) for n in allocation])
    check = {k: {'analytic': exact[k], 'monte_carlo': mc[k],
                 'absolute_error': abs(exact[k] - mc[k]),
                 'tolerance': 5 * float(np.sqrt(exact[k] * (1 - exact[k]) / n_trials)) + 1 / n_trials}
             for k in exact}
    if max(errors) > 1e-6 or any(v['absolute_error'] > v['tolerance'] for v in check.values()):
        raise ValueError('Synthetic quadrature or Monte Carlo verification failed')
    save('synthetic-results.json', {'evidence_class': 'synthetic_only', 'claim_level': 'Heuristic',
                                   'contract_sha256': sha(HERE / 'analysis-contract.json'), 'assumptions': config,
                                   'scenarios': rows, 'all_null_scenarios': nulls,
                                   'quadrature_max_absolute_error': max(errors),
                                   'monte_carlo_trials': n_trials, 'monte_carlo_check': check,
                                   'authority': 'Hypothetical flags and design diagnostics; no empirical risk or power claim.'})
    print('Synthetic scenarios:', len(rows), '+', len(nulls), 'all-null; quadrature error', max(errors))


def plots():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    human_data = json.loads((HERE / 'human-results.json').read_text())
    names = ['fibroblast_identity', 'cycle_panel', 'stress_panel', 'reprogramming_without_OSK_overlap']
    labels = ['Fibroblast markers', 'Cell-cycle markers', 'Stress markers', 'Reprogramming markers\n(OSK overlap excluded)']
    fig, ax = plt.subplots(figsize=(9.5, 5.5), layout='constrained')
    for i, (construct, color) in enumerate([('OSK', '#216b9a'), ('O4YRSK', '#a94e2d')]):
        rows = [next(r for r in human_data['contrasts'] if r['construct'] == construct and r['panel'] == name) for name in names]
        ys = np.arange(len(names)) + (i - .5) * .22
        effects = np.array([r['methods']['log2_cpm']['mean_difference'] for r in rows])
        ranges = np.array([r['methods']['log2_cpm']['pairwise_range'] for r in rows])
        ax.errorbar(effects, ys, xerr=np.stack([effects - ranges[:, 0], ranges[:, 1] - effects]), fmt='o', color=color, capsize=3, label=construct)
        sensitivity = [r['methods']['log2_median_ratio_cpm_equivalent']['mean_difference'] for r in rows]
        ax.scatter(sensitivity, ys, facecolors='white', edgecolors=color, marker='D', s=40)
    ax.axvline(0, color='#777777', lw=1)
    ax.set(yticks=np.arange(len(names)), yticklabels=labels, xlabel='Treated minus control: mean log2(1 + normalized expression)',
           title='Human expression comparison: eight libraries from one donor')
    ax.invert_yaxis(); ax.legend(loc='lower left'); ax.spines[['top', 'right']].set_visible(False)
    fig.get_layout_engine().set(rect=(0, .15, 1, .85))
    fig.text(.02, .02, 'Circles: CPM. Open diamonds: median-ratio sensitivity. Bars: four library contrasts, not confidence intervals.\nHeuristic panels; no young reference, recovery sample or retinal outcome.', fontsize=9)
    fig.savefig(HERE / 'human-comparison.png', dpi=180, bbox_inches='tight'); fig.savefig(HERE / 'human-comparison.pdf', bbox_inches='tight'); plt.close(fig)
    data = json.loads((HERE / 'synthetic-results.json').read_text())
    rows = [r for r in data['scenarios'] if r['prevalence'] == .01 and r['latent_donor_correlation'] == .05 and r['specificity'] == 1]
    fig, ax = plt.subplots(figsize=(8.5, 4.8), layout='constrained')
    x = np.arange(len(rows))
    ax.bar(x - .17, [r['any_donor_flagged'] * 100 for r in rows], width=.34, color='#216b9a', label='At least one donor')
    ax.bar(x + .17, [r['two_or_more_donors_flagged'] * 100 for r in rows], width=.34, color='#647b38', label='At least two donors')
    ax.set(xticks=x, xticklabels=['3 balanced', '3 imbalanced', '6 balanced', '6 imbalanced'], ylim=(0, 100), ylabel='Probability of flags (%)',
           title='Synthetic sampling: donor balance at fixed 1,200 cells')
    ax.legend(); ax.spines[['top', 'right']].set_visible(False)
    fig.get_layout_engine().set(rect=(0, .15, 1, .85))
    fig.text(.02, .02, 'Hypothetical 1% prevalence, 80% sensitivity, perfect specificity and 0.05 donor correlation.\nThese probabilities are design scenarios, not observed biological risk.', fontsize=9)
    fig.savefig(HERE / 'synthetic-donor-balance.png', dpi=180, bbox_inches='tight'); fig.savefig(HERE / 'synthetic-donor-balance.pdf', bbox_inches='tight'); plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('task', choices=['human', 'synthetic', 'plots', 'all'])
    parser.add_argument('--cache', type=Path)
    args = parser.parse_args()
    if args.task in ['human', 'all']:
        if args.cache is None:
            parser.error('--cache is required for observed data')
        human(args.cache)
    if args.task in ['synthetic', 'all']:
        synthetic()
    if args.task in ['plots', 'all']:
        plots()

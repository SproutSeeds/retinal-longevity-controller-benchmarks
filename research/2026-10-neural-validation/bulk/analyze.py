#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["numpy==2.5.4"]
# ///
"""Frozen nine-donor analysis. Biological execution requires a committed receipt."""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
import numpy as np

HERE = Path(__file__).resolve().parent
CACHE = Path('/tmp/cx004-neural-validation-2026-10-18')
METHODS = ['log2_cpm', 'log2_median_ratio', 'within_library_rank']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


def save(name, data, output_dir=None):
    (Path(output_dir or HERE) / name).write_text(json.JSONEncoder(indent=2, sort_keys=True, allow_nan=False).encode(data) + '\n')


def validate_freeze(replay_frozen_hashes=False):
    receipt = load('FREEZE.json')
    if receipt.get('expression_execution_authorized') is not True:
        raise ValueError('Root has not authorized bulk expression execution')
    root = None
    if not replay_frozen_hashes:
        root = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=HERE, text=True).strip())
    for name, key in [('contract.json','contract_sha256'), ('admission.json','admission_sha256'),
                      ('panels.json','panels_sha256'), ('analyze.py','analysis_sha256')]:
        expected = receipt[key]
        if sha(HERE / name) != expected:
            raise ValueError('Current bytes differ from bulk freeze: ' + name)
        if not replay_frozen_hashes:
            data = subprocess.check_output(['git', 'show', receipt['commit'] + ':' + str((HERE / name).relative_to(root))], cwd=root)
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError('Committed bytes differ from bulk freeze: ' + name)
    validation = {'mode': 'archived_hash_replay' if replay_frozen_hashes else 'strict_committed_contract',
        'archived_contract_admission_panels_code_hashes_passed': True,
        'historical_git_proof_reexecuted': not replay_frozen_hashes, 'historical_commit': receipt['commit'],
        'scope': 'Archived artifact hash verification only; historical git proof was not rerun.' if replay_frozen_hashes
                 else 'Current and historical git bytes match the frozen hashes.'}
    return receipt, validation


def acquire_counts(contract, cache_dir, output_dir):
    cache_dir, output_dir = Path(cache_dir), Path(output_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / 'GSE245385_countTable.csv.gz'
    known_receipt = None
    for directory in [HERE, output_dir]:
        receipt_path = directory / 'count-source-receipt.json'
        if receipt_path.exists():
            candidate = json.loads(receipt_path.read_text())
            if known_receipt is not None and candidate['sha256'] != known_receipt['sha256']:
                raise ValueError('Archived and output count receipts disagree')
            known_receipt = candidate
    if path.exists():
        if known_receipt is None:
            raise ValueError('Existing raw counts have no acquisition receipt')
        if path.stat().st_size != contract['input']['expected_compressed_bytes'] or sha(path) != known_receipt['sha256']:
            raise ValueError('Cached count bytes differ from acquisition receipt')
        receipt = {**known_receipt, 'cache_path': str(path)}
        save('count-source-receipt.json', receipt, output_dir)
        return path, receipt
    if shutil.disk_usage(cache_dir).free < 8 * 1024**3:
        raise ValueError('Internal free space below 8 GiB')
    url = contract['input']['source_url']
    expected = contract['input']['expected_compressed_bytes']
    with urllib.request.urlopen(url, timeout=60) as response:
        if int(response.headers.get('Content-Length', expected)) != expected:
            raise ValueError('Remote count size changed')
        data = response.read(expected + 1)
    if len(data) != expected:
        raise ValueError('Raw count download has wrong byte count')
    if known_receipt is not None and hashlib.sha256(data).hexdigest() != known_receipt['sha256']:
        raise ValueError('Downloaded count hash differs from archived acquisition')
    decoded = gzip.decompress(data)  # Validates gzip CRC; no value inspection here.
    header = decoded.split(b'\n', 1)[0] + b'\n'
    if hashlib.sha256(header).hexdigest() != contract['input']['header_sha256']:
        raise ValueError('Full acquisition header differs from metadata freeze')
    path.write_bytes(data)
    receipt = {'source_url': url, 'cache_path': str(path), 'size_bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(), 'gzip_crc_valid': True,
        'header_sha256': contract['input']['header_sha256'], 'expression_values_analyzed_when_receipted': False}
    save('count-source-receipt.json', receipt, output_dir)
    return path, receipt


def canonical_gene(value):
    if not value:
        raise ValueError('Missing feature identifier')
    match = re.fullmatch(r'(ENSMUSG\d{11})(?:\.\d+)?', value)
    return match[1] if match else value


def read_counts(path, expected_header, header_sha256=None):
    original_ids, genes, lengths, matrix = [], [], [], []
    if header_sha256 is not None:
        with gzip.open(path, 'rb') as stream:
            if hashlib.sha256(stream.readline()).hexdigest() != header_sha256:
                raise ValueError('Frozen count header byte hash changed')
    with gzip.open(path, 'rt', newline='') as stream:
        reader = csv.reader(stream)
        header = next(reader)
        if header != expected_header or header[:2] != ['Geneid', 'Length'] or len(set(header)) != len(header):
            raise ValueError('Count header does not match admitted metadata')
        for row in reader:
            if len(row) != len(header):
                raise ValueError('Ragged count row')
            original_ids.append(row[0])
            genes.append(canonical_gene(row[0]))
            length = float(row[1])
            values = np.array(row[2:], dtype=float)
            if not math.isfinite(length) or length <= 0:
                raise ValueError('Invalid feature length')
            if not np.isfinite(values).all() or (values < 0).any() or (values % 1 != 0).any() or (values >= 2**53).any():
                raise ValueError('Counts must be finite nonnegative exact integers')
            lengths.append(length)
            matrix.append(values.astype(np.int64))
    if len(genes) < 2 or len(set(genes)) != len(genes):
        raise ValueError('Duplicate or insufficient canonical feature IDs')
    x = np.stack(matrix)
    if (x.sum(axis=0) <= 0).any():
        raise ValueError('Empty library')
    return genes, x, {'original_feature_ids': original_ids,
        'version_stripped_features': sum(a != b for a,b in zip(original_ids, genes)),
        'non_ensembl_features': [g for g in genes if not re.fullmatch(r'ENSMUSG\d{11}',g)],
        'feature_count': len(genes), 'library_count': x.shape[1], 'lengths_validated': True}


def average_ranks(values):
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError('Invalid rank input')
    order = np.argsort(values, kind='mergesort')
    sorted_values = values[order]
    bounds = np.r_[0, np.flatnonzero(np.diff(sorted_values)) + 1, len(values)]
    ranks = np.empty(len(values))
    for start, end in zip(bounds[:-1], bounds[1:]):
        ranks[order[start:end]] = (start + end - 1) / 2 + 1
    return ranks


def normalizations(x, minimum_positive=100):
    x = np.asarray(x, dtype=float)
    if x.ndim != 2 or not np.isfinite(x).all() or (x < 0).any() or (x.sum(axis=0) <= 0).any():
        raise ValueError('Invalid normalization input')
    totals = x.sum(axis=0)
    outputs = {'log2_cpm': np.log2(1 + 1e6 * x / totals)}
    outputs['within_library_rank'] = np.stack([(average_ranks(x[:,i])-1)/(x.shape[0]-1) for i in range(x.shape[1])], axis=1)
    positive = x[(x > 0).all(axis=1)]
    audit = {'raw_library_totals': totals.tolist(), 'all_positive_genes': len(positive),
             'median_ratio_status': 'unavailable_below_100_positive_genes',
             'median_ratio_size_factors': None, 'median_ratio_effective_depths': None}
    if len(positive) >= minimum_positive:
        gm = np.exp(np.log(positive).mean(axis=1))
        factors = np.median(positive / gm[:,None], axis=0)
        factors /= np.exp(np.log(factors).mean())
        depths = factors * np.exp(np.log(totals).mean())
        outputs['log2_median_ratio'] = np.log2(1 + 1e6 * x / depths)
        audit.update(median_ratio_status='available', median_ratio_size_factors=factors.tolist(),
                     median_ratio_effective_depths=depths.tolist())
    return outputs, audit


def age_difference(deltas, old):
    deltas, old = np.asarray(deltas, dtype=float), np.asarray(old, dtype=bool)
    if deltas.ndim != 1 or deltas.shape != old.shape or not np.isfinite(deltas).all() or old.all() or not old.any():
        raise ValueError('Invalid two-age contrast')
    return float(deltas[old].mean() - deltas[~old].mean())


def exact_age_permutation(deltas, old):
    deltas, old = np.asarray(deltas, dtype=float), np.asarray(old, dtype=bool)
    observed = age_difference(deltas, old)
    distribution = []
    for indices in itertools.combinations(range(len(deltas)), int(old.sum())):
        mask = np.zeros(len(deltas), dtype=bool)
        mask[list(indices)] = True
        distribution.append(abs(age_difference(deltas, mask)))
    tolerance = 1e-12 * max(1, abs(observed))
    numerator = sum(v >= abs(observed) - tolerance for v in distribution)
    return {'signed_effect': observed, 'absolute_statistic': abs(observed), 'numerator': numerator,
            'denominator': len(distribution), 'p': numerator/len(distribution),
            'null_absolute_statistics': distribution, 'tie_tolerance': tolerance}


def exact_sign_test(deltas):
    values = np.asarray(deltas, dtype=float)
    if values.ndim != 1 or not np.isfinite(values).all():
        raise ValueError('Invalid sign-test input')
    positive, negative = int((values > 1e-12).sum()), int((values < -1e-12).sum())
    n = positive + negative
    numerator = min(2**n, 2 * sum(math.comb(n,j) for j in range(min(positive,negative)+1)))
    return {'positive': positive, 'negative': negative, 'zero': len(values)-n,
            'nonzero_n': n, 'numerator': numerator, 'denominator': 2**n, 'p': numerator/2**n}


def holm(values):
    if any(v is not None and (not math.isfinite(v) or not 0 <= v <= 1) for v in values):
        raise ValueError('Invalid p-value')
    raw = [1.0 if v is None else v for v in values]
    order = sorted(range(len(raw)), key=lambda i: raw[i])
    out = [None] * len(raw)
    current = 0.0
    for rank, i in enumerate(order):
        current = max(current, min(1.0, (len(raw)-rank)*raw[i]))
        out[i] = current if values[i] is not None else None
    return out


def coverage(panel, genes):
    index = {g:i for i,g in enumerate(genes)}
    mapped = [g for g in panel['genes'] if g['status'] == 'mapped']
    present = [g for g in mapped if g['mouse_ensembl_gene'] in index]
    failures = []
    if len(present)/len(panel['source_human_genes']) < 0.8:
        failures.append('source_human_coverage_below_0.8')
    if not mapped or len(present)/len(mapped) < 0.8:
        failures.append('mapped_coverage_below_0.8')
    if len(present) < 3:
        failures.append('fewer_than_3_panel_genes')
    return {'source_genes': len(panel['source_human_genes']), 'mapped_genes': len(mapped),
            'present_genes': len(present), 'present': present, 'failures': failures,
            'missing': [g for g in panel['genes'] if g not in present]}, [index[g['mouse_ensembl_gene']] for g in present]


def run_analysis(genes, x, columns, admission, panels):
    if set(panels) != {'cycle_panel', 'stress_panel', 'reprogramming_state', 'reprogramming_without_OSKM_overlap'}:
        raise ValueError('Exactly the four frozen panels are required')
    pairs = admission['pairs']
    if len(pairs) != 9 or sum(p['age_group'] == 'old' for p in pairs) != 4:
        raise ValueError('Primary analysis requires exactly four old and five young donors')
    selected = [p[k + '_count_column'] for p in pairs for k in ['control','treated']]
    if len(set(selected)) != 18 or any(c not in columns for c in selected):
        raise ValueError('Pair-to-count join is not unique and complete')
    values = x[:, [columns.index(c) for c in selected]]
    old = np.array([p['age_group'] == 'old' for p in pairs])
    qc = [{'count_column': c, 'raw_library_total': int(values[:,i].sum()),
           'detected_features': int((values[:,i]>0).sum()), 'passes_500_detected_features': bool((values[:,i]>0).sum() >= 500)}
          for i,c in enumerate(selected)]
    if not all(r['passes_500_detected_features'] for r in qc):
        failures = []
        for method in METHODS:
            for name,panel in panels.items():
                row = {'method': method, 'panel': name, 'coverage': coverage(panel,genes)[0],
                    'status': 'unavailable', 'reason': 'primary_library_qc_failed_no_donor_dropped',
                    'age_test': None, 'overall_sign_test': None,
                    'age_test_holm_p': None, 'overall_sign_test_holm_p': None}
                for test in ['age_test','overall_sign_test']:
                    row[test + '_family'] = {'method': method, 'test': test, 'size': 4,
                        'primary': method == 'log2_cpm' and test == 'age_test'}
                failures.append(row)
        return {'status': 'primary_unavailable_library_qc', 'library_qc': qc, 'panel_results': failures}, []
    normalized, audit = normalizations(values)
    results, gene_rows = [], []
    for method in METHODS:
        for name, panel in panels.items():
            cov, indices = coverage(panel, genes)
            row = {'method': method, 'panel': name, 'coverage': cov,
                   'status': 'unavailable', 'age_test': None, 'overall_sign_test': None}
            if method not in normalized:
                row['reason'] = audit['median_ratio_status']
            elif cov['failures']:
                row['reason'] = 'panel_coverage_failed'
            else:
                gene_values = normalized[method][indices,:]
                scores = gene_values.mean(axis=0)
                delta = scores[1::2] - scores[::2]
                gene_deltas = gene_values[:,1::2] - gene_values[:,::2]
                row.update(status='available', scores=[{'donor_id': p['donor_id'], 'age_group': p['age_group'],
                    'sex': p['sex'], 'control': float(scores[2*i]), 'treated': float(scores[2*i+1]),
                    'delta': float(delta[i])} for i,p in enumerate(pairs)],
                    old_mean_delta=float(delta[old].mean()), young_mean_delta=float(delta[~old].mean()),
                    overall_mean_delta=float(delta.mean()), age_test=exact_age_permutation(delta,old),
                    overall_sign_test=exact_sign_test(delta))
                contributions = []
                for g, info in enumerate(cov['present']):
                    contribution = age_difference(gene_deltas[g],old)/len(indices)
                    contributions.append({**info, 'age_difference_contribution': contribution})
                    for i,p in enumerate(pairs):
                        gene_rows.append({'method': method, 'panel': name, **info, 'donor_id': p['donor_id'],
                            'age_group': p['age_group'], 'control_value': float(gene_values[g,2*i]),
                            'treated_value': float(gene_values[g,2*i+1]), 'delta': float(gene_deltas[g,i]),
                            'age_difference_contribution': contribution})
                if not math.isclose(sum(c['age_difference_contribution'] for c in contributions),
                                    row['age_test']['signed_effect'], abs_tol=1e-10, rel_tol=1e-10):
                    raise ValueError('Gene contributions fail panel reconstruction')
                row['gene_contributions'] = contributions
                row['gene_omissions'] = []
                for g,info in enumerate(cov['present']):
                    remaining = np.delete(gene_deltas,g,axis=0).mean(axis=0)
                    row['gene_omissions'].append({'omitted_mouse_gene': info['mouse_symbol'],
                        'donor_deltas': remaining.tolist(), 'age_difference': age_difference(remaining,old)})
                if method == 'log2_cpm':
                    row['donor_omissions'] = []
                    for i,p in enumerate(pairs):
                        kept = np.arange(len(pairs)) != i
                        row['donor_omissions'].append({'omitted_donor': p['donor_id'],
                            'old_n': int(old[kept].sum()), 'young_n': int((~old[kept]).sum()),
                            'age_difference': age_difference(delta[kept],old[kept])})
            results.append(row)
    for method in METHODS:
        family = [r for r in results if r['method'] == method]
        for test in ['age_test','overall_sign_test']:
            adjusted = holm([r[test]['p'] if r[test] else None for r in family])
            for r,p in zip(family,adjusted):
                r[test + '_holm_p'] = p
                r[test + '_family'] = {'method': method, 'test': test, 'size': 4,
                    'primary': method == 'log2_cpm' and test == 'age_test'}
    return {'status': 'completed', 'library_qc': qc, 'primary_columns_in_pair_order': selected,
            'normalization': audit, 'panel_results': results}, gene_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--acquire-only', action='store_true')
    parser.add_argument('--cache', type=Path, default=CACHE)
    parser.add_argument('--output', type=Path, default=HERE)
    parser.add_argument('--replay-frozen-hashes', action='store_true',
                        help='Verify archived frozen hashes without rerunning historical git proof.')
    args = parser.parse_args()
    started = time.monotonic()
    freeze, validation = validate_freeze(args.replay_frozen_hashes)
    contract, admission, panel_file = load('contract.json'), load('admission.json'), load('panels.json')
    path, source = acquire_counts(contract, args.cache, args.output)
    if args.acquire_only:
        save('execution-receipt.json', {'status': 'PASS', 'operation': 'acquisition_only',
            'freeze_validation': validation, 'source_sha256': source['sha256'],
            'expression_outcomes_computed': False}, args.output)
        print('PASS acquisition:', source['size_bytes'], 'bytes; SHA-256', source['sha256'])
        return
    expected_header = load('header-exposure.json')['header_columns']
    genes, counts, feature_audit = read_counts(path, expected_header, contract['input']['header_sha256'])
    result, gene_rows = run_analysis(genes, counts, expected_header[2:], admission, panel_file['panels'])
    result.update(claim_level='Heuristic', freeze=freeze, source=source, feature_audit=feature_audit,
        contract_sha256=sha(HERE/'contract.json'), readouts=contract['readouts'],
        inference_limits=contract['inference']['assumptions'], interpretation=contract['inference']['interpretation'])
    save('results.json', result, args.output)
    with (args.output/'gene-contributions.csv').open('w',newline='') as stream:
        names = ['method','panel','human_symbol','status','mouse_symbol','mouse_ensembl_gene','donor_id','age_group',
                 'control_value','treated_value','delta','age_difference_contribution']
        writer = csv.DictWriter(stream, fieldnames=names)
        writer.writeheader()
        writer.writerows(gene_rows)
    execution_status = 'PASS' if result['status'] == 'completed' else 'INCONCLUSIVE'
    save('execution-receipt.json', {'status': execution_status, 'operation': 'expression_analysis',
        'generated_at_utc': datetime.now(timezone.utc).isoformat(), 'elapsed_seconds': time.monotonic()-started,
        'freeze_validation': validation, 'source_sha256': source['sha256'],
        'results_sha256': sha(args.output/'results.json'), 'gene_contributions_sha256': sha(args.output/'gene-contributions.csv'),
        'cache': str(args.cache), 'output': str(args.output), 'numpy_version': np.__version__,
        'expression_outcomes_computed': result['status'] == 'completed'}, args.output)
    print(execution_status, 'bulk execution:', result['status'], '; nine independent donor pairs')


if __name__ == '__main__':
    main()

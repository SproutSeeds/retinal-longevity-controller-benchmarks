#!/usr/bin/env python3
"""Replay newly acquired file admission and compare it with the retained baseline."""
import argparse
import gzip
import importlib.util
from pathlib import Path

from recover import DEFAULT_CACHE, HERE, encode, read, sha, validate_payload

OLD = HERE.parent / 'gse350289-assignment-recheck-2026-11-01'
spec = importlib.util.spec_from_file_location('retained_census_reader', OLD / 'audit.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


def products(cache, retained_barcodes):
    plan = read(HERE / 'DOWNLOAD_PLAN.json')
    acquisition = read(cache / 'ACQUISITION.json')
    assert acquisition['all_files_acquired'] is True
    assert set(plan['files']) == set(acquisition['files'])
    sources = {}
    barcodes = set()
    counts = {}
    for name, original in plan['files'].items():
        record = acquisition['files'][name]
        body = (cache / name).read_bytes()
        assert record['accepted'] is True and record['curl_exit'] == 0
        assert record['sha256'] == sha(body) and record['bytes'] == len(body)
        assert validate_payload(record['http_status'], body, original['format']) == record['format_validation']
        identical = sha(body) == original['baseline_sha256'] and len(body) == original['baseline_bytes']
        assert identical == record['byte_identical_to_October_17']
        sources[name] = {'url': record['requested_url'], 'effective_url': record['effective_url'], 'received_at_utc': record['received_at_utc'], 'bytes': len(body), 'sha256': sha(body), 'format': original['format'], 'byte_identical_to_October_17': identical, 'baseline_sha256': original['baseline_sha256'], 'baseline_acquired_at_utc': original['baseline_acquired_at_utc']}
    prior_sources = read(OLD / 'SOURCE_MANIFEST.json')['files']
    retained = {}
    for name, pin in prior_sources.items():
        if not name.endswith('_barcodes.tsv.gz'):
            continue
        body = (retained_barcodes / name).read_bytes()
        assert len(body) == pin['bytes'] and sha(body) == pin['sha256']
        with gzip.open(retained_barcodes / name, 'rt', newline='') as stream:
            keys = [line.rstrip('\r\n') for line in stream]
        assert all(key and key == key.strip() for key in keys)
        assert len(keys) == len(set(keys))
        library = name.removeprefix('GSE350289_').removesuffix('_barcodes.tsv.gz')
        counts[library] = len(keys)
        barcodes.update(keys)
        retained[name] = pin
    metadata = 'GSE350289_metadata_individual_cells.xlsx'
    sheets = reader.census(cache / metadata, barcodes)
    matches = sum(s['exact_deposited_barcode_cells'] for s in sheets if s['sheet'] != 'README')
    result = {'schema': 'controller.current-workbook-comparison/1', 'claim_level': 'Verified newly retrieved source contents', 'current_acquisition': 'PASS', 'current_workbook_sha256': sources[metadata]['sha256'], 'current_workbook_bytes': sources[metadata]['bytes'], 'current_workbook_received_at_utc': sources[metadata]['received_at_utc'], 'current_workbook_byte_identical_to_October_17': sources[metadata]['byte_identical_to_October_17'], 'newly_acquired_source_file_count': len(sources), 'total_new_source_bytes': sum(s['bytes'] for s in sources.values()), 'retained_barcode_records_by_library': counts, 'retained_barcode_records': sum(counts.values()), 'retained_unique_full_barcodes': len(barcodes), 'retained_barcode_files_newly_downloaded': False, 'sheets': sheets, 'exact_retained_barcode_cells_in_current_workbook': matches, 'accepted_current_assignment_keys': 0, 'assignment_status': 'No exact retained barcode identity in the workbook; perturbation and donor/pool assignments are not admitted.' if matches == 0 else 'Candidate identity requires explicit context and QC verification before admission.', 'biological_outcome_analysis_unlocked': False, 'expression_matrices_downloaded': False, 'clock_or_model_training_performed': False, 'freshness_scope': 'Workbook served by the named public download route at the recorded time. Four barcode files remain explicitly retained October 17 reference inputs; no claim about files elsewhere or later updates.'}
    manifest = {'schema': 'controller.recovered-GEO-sources/1', 'files': sources, 'retained_barcode_reference_files': retained, 'source_terms': 'Investigator-deposited public GEO data. Raw source files remain outside this public packet.', 'acquisition': 'ACQUISITION.json'}
    return {'ACQUISITION.json': acquisition, 'SOURCE_MANIFEST.json': manifest, 'RESULTS.json': result}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=DEFAULT_CACHE)
    parser.add_argument('--retained-barcodes', type=Path, default=HERE.parents[1] / '.data/gse350289-assignment-recheck-2026-11-01')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    for name, result in products(args.cache, args.retained_barcodes).items():
        body = encode(result)
        if args.write:
            (HERE / name).write_text(body)
        elif (HERE / name).read_text() != body:
            raise AssertionError('Pinned source replay differs: ' + name)
    print('PASS source replay: newly acquired workbook verified; four retained barcode references remain explicitly dated; no assignment inference.')

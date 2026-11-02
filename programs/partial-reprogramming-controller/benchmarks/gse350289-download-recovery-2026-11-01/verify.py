#!/usr/bin/env python3
"""Offline evidence and source-freshness checks; no download or biological run."""
from pathlib import Path
import subprocess
import sys

from recover import HERE, read, sha


def main():
    for name, pin in read(HERE / 'ARTIFACT_MANIFEST.json')['files'].items():
        assert Path(name).name == name and sha((HERE / name).read_bytes()) == pin
    result = read(HERE / 'RESULTS.json')
    assert result['current_acquisition'] == 'PASS'
    assert result['current_workbook_bytes'] == 1725954
    assert result['current_workbook_sha256'] == 'f48a3eba3416110afae897a4df78796379d01211e0b9a436f65d7f4b1f44e76d'
    assert result['current_workbook_byte_identical_to_October_17'] is True
    assert result['newly_acquired_source_file_count'] == 1
    assert result['retained_barcode_files_newly_downloaded'] is False
    assert result['retained_barcode_records'] == result['retained_unique_full_barcodes'] == 546362
    assert result['exact_retained_barcode_cells_in_current_workbook'] == result['accepted_current_assignment_keys'] == 0
    assert result['biological_outcome_analysis_unlocked'] is False
    assert result['expression_matrices_downloaded'] is result['clock_or_model_training_performed'] is False
    assert {s['sheet'] for s in result['sheets']} == {'README', 'Ctrl', 'Sample 1', 'Sample 2', 'Sample 3'}
    expected = {'Ctrl': 139938, 'Sample 1': 161422, 'Sample 2': 0, 'Sample 3': 0}
    for sheet in result['sheets']:
        if sheet['sheet'] == 'README':
            continue
        n = expected[sheet['sheet']]
        assert sheet['nonempty_rows'] == n and sheet['nonempty_cells_by_column'] == ({'D': n} if n else {})
    independent = read(HERE / 'INDEPENDENT_CHECK.json')
    assert independent['status'] == 'PASS' and independent['current_workbook_reacquisition_verified'] is True
    assert independent['imports_primary_XML_reader'] is False and independent['source_sha256'] == result['current_workbook_sha256']
    assert independent['sheets_checked'] == 5 and independent['nonempty_nonREADME_cells'] == 301360
    acquisition = read(HERE / 'ACQUISITION.json')
    assert acquisition['all_files_acquired'] is True and len(acquisition['files']) == 1
    source = acquisition['files']['GSE350289_metadata_individual_cells.xlsx']
    assert source['accepted'] is True and source['http_status'] == 200 and source['curl_exit'] == 0
    assert source['bytes'] == result['current_workbook_bytes'] and source['sha256'] == independent['source_sha256']
    assert source['independent_repeat_payload_byte_identical'] is True
    diagnosis = read(HERE / 'TRANSPORT_DIAGNOSIS.json')
    assert diagnosis['successful_workbook_transfers'] == 2 and diagnosis['matching_workbook_payloads'] is True
    assert diagnosis['upstream_root_cause'].startswith('INCONCLUSIVE')
    assert diagnosis['later_attempts'] and not any(item['all_files_acquired'] for item in diagnosis['later_attempts'])
    tests = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(HERE), '-p', 'test_recovery.py'], text=True, capture_output=True)
    if tests.returncode:
        raise AssertionError(tests.stdout + tests.stderr)
    print(tests.stderr.strip())
    print('PASS recovered workbook: current bytes verified; retained barcode references dated; assignments remain unadmitted; future transport availability unestablished.')


if __name__ == '__main__':
    main()

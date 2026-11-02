#!/usr/bin/env python3
"""Offline released-artifact and source-freshness checks; no network request."""
from pathlib import Path
import subprocess
import sys

import audit as a

HERE=Path(__file__).resolve().parent


def main():
    for name,expected in a.read(HERE/'ARTIFACT_MANIFEST.json')['files'].items():
        if Path(name).name!=name or a.sha((HERE/name).read_bytes())!=expected:
            raise AssertionError('Released artifact differs: '+name)
    result=a.read(HERE/'RESULTS.json');source=a.read(HERE/'SOURCE_MANIFEST.json')
    assert result['current_workbook_reacquisition']=='INCONCLUSIVE'
    assert result['accepted_current_mapping_keys']==0 and result['perturbation_outcome_analysis_unlocked'] is False
    assert result['mapping_admission']==a.evidence_state(False,0)
    assert result['retained_barcode_records']==result['retained_unique_full_barcode_strings']==546362
    assert result['exact_barcode_cells_in_retained_metadata']==0
    workbook=source['files']['GSE350289_metadata_individual_cells.xlsx']
    assert workbook['sha256']==result['retained_workbook_sha256']
    assert workbook['freshness'].startswith('retained_original')
    expected={'Ctrl':139938,'Sample 1':161422,'Sample 2':0,'Sample 3':0}
    for sheet in result['sheets']:
        if sheet['sheet']=='README':continue
        n=expected[sheet['sheet']]
        assert sheet['nonempty_rows']==n and sheet['exact_deposited_barcode_cells']==0
        assert sheet['nonempty_cells_by_column']==({'D':n} if n else {})
    independent=a.read(HERE/'INDEPENDENT_CHECK.json')
    assert independent['status']=='PASS' and independent['sheets_checked']==5 and independent['nonempty_nonREADME_cells']==301360
    assert independent['current_workbook_reacquisition_verified'] is False and independent['imports_primary_XML_reader'] is False
    assert independent['source_sha256']==workbook['sha256']
    assert result['pool_description_disagreement']['GEO_donors_per_age_group']==3
    assert result['pool_description_disagreement']['preprint_implied_donors_per_age_group']==6
    assert result['expression_matrix_downloaded'] is False and result['new_training_or_biological_effect_computed'] is False
    acquisition=a.read(HERE/'ACQUISITION.json')
    assert acquisition['current_workbook_reacquisition']=='INCONCLUSIVE'
    tests=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(HERE),'-p','test_audit.py'],text=True,capture_output=True)
    if tests.returncode:raise AssertionError(tests.stdout+tests.stderr)
    print(tests.stderr.strip())
    print('PASS offline assignment recheck: dated retained source verified; current workbook INCONCLUSIVE; zero assignment admissions.')


if __name__=='__main__':main()

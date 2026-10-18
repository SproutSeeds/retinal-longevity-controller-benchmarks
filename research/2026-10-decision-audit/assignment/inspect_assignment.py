#!/usr/bin/env python3
"""Compare the current GEO assignment workbook with its audited source bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
PREVIOUS_WORKBOOK = 'f48a3eba3416110afae897a4df78796379d01211e0b9a436f65d7f4b1f44e76d'


def inspect(cache):
    receipt = json.loads((HERE / 'retrieval-2.json').read_text())
    for record in receipt['sources']:
        path = cache / record['id']
        if record['status'] != 'retrieved' or hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
            raise ValueError('Source hash/status failure: ' + record['id'])
    text = (cache / 'geo350289-series.txt').read_text()
    fields = {}
    for line in text.splitlines():
        if line.startswith('!Series_') and ' = ' in line:
            key, value = line[1:].split(' = ', 1)
            fields.setdefault(key, []).append(value)
    sha = hashlib.sha256((cache / 'geo350289-metadata.xlsx').read_bytes()).hexdigest()
    unchanged = sha == PREVIOUS_WORKBOOK
    return {
        'accession': 'GSE350289', 'claim_level': 'Verified',
        'workbook_sha256': sha, 'prior_workbook_sha256': PREVIOUS_WORKBOOK,
        'workbook_unchanged': unchanged,
        'series_last_updated': fields.get('Series_last_update_date', []),
        'series_sample_records': len(fields.get('Series_sample_id', [])),
        'series_supplementary_files': fields.get('Series_supplementary_file', []),
        'directory_entries': re.findall(r'href="([^"]+)"', (cache / 'geo350289-files.html').read_text()),
        'status': 'await_corrected_assignment' if unchanged else 'changed_workbook_requires_fresh_content_audit',
        'prior_content_findings_reused_only_if_identical': {
            'Ctrl_nonempty_rows': 139938, 'Sample_1_nonempty_rows': 161422,
            'Sample_2_nonempty_rows': 0, 'Sample_3_nonempty_rows': 0,
            'library_barcode_perturbation_donor_assignment_recovered': False,
        } if unchanged else None,
        'raw_expression_downloaded_this_pass': False,
        'outcome_analysis_unlocked': False,
        'reopen_trigger': 'Corrected library plus cell-barcode assignment file with treatment, donor/pool provenance and assignment QC; independently verify exact joins before outcome analysis.',
        'scope_limit': 'The inspected GEO records and workbook are a dated snapshot. No claim that an assignment file is absent from every repository or author-held source.',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    result = inspect(args.cache)
    rendered = json.dumps(result, indent=2, sort_keys=True) + '\n'
    if args.write:
        (HERE / 'results.json').write_text(rendered)
    else:
        if json.loads((HERE / 'results.json').read_text()) != result:
            raise SystemExit('FAIL: saved assignment comparison differs')
    print(json.dumps({'status': result['status'], 'workbook_unchanged': result['workbook_unchanged'], 'series_sample_records': result['series_sample_records']}))

#!/usr/bin/env python3
"""Record the missing join-input binding honestly as a post-inspection addendum."""
import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
source = HERE.parent.parent / 'cx004-public-evidence-resolution-2026-10-17/sample-metadata.json'
rows = [r for r in json.loads(source.read_text())['samples']
        if r['accession'] == 'GSE325735' and r['organism'] == 'Homo sapiens']
fields = ['accession', 'age_years', 'cell_type', 'construct_conflict', 'donor_or_line',
          'genotype', 'library', 'match_basis', 'matrix_column', 'matrix_column_present',
          'off_days_geo', 'on_days_geo', 'organism', 'passage', 'sample_id',
          'sequencing_batch', 'title', 'treatment']
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
out = {'schema_version': 1, 'source_manifest_sha256': source_hash,
       'samples': [{k: r.get(k) for k in fields} for r in rows]}
target = HERE / 'reference-join-manifest.json'
target.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
record = {
    'schema_version': 1,
    'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'stage': 'post_numeric_inspection_input_binding_correction',
    'reason': ('Original frozen reference-inputs.json pinned the 72-row raw withdrawal manifest. '
               'The extractor requires the larger normalized metadata manifest and had used it '
               'without a pinned binding. Preserve the original freeze; this addendum explicitly '
               'binds the prior published metadata and does not retroactively claim a pre-outcome '
               'freeze. The joined subset is selected by accession and organism only. No selection '
               'by reported age was made.'),
    'source_manifest': {'relative_path': '../../cx004-public-evidence-resolution-2026-10-17/sample-metadata.json',
                        'sha256': source_hash},
    'join_manifest': {'path': target.name, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'rows': len(rows)},
    'implementation_corrections': ['Accept literal construct equality before alias mapping.',
                                  'Require a verified count-matrix column for an accepted join.',
                                  'Reject use of a differently hashed manifest.'],
    'original_contract_sha256': hashlib.sha256((HERE / 'reference-audit-contract.json').read_bytes()).hexdigest(),
}
addendum = HERE / 'reference-input-addendum.json'
if addendum.exists():
    raise SystemExit('Binding already recorded; preserve the existing timestamp.')
addendum.write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
print(len(rows), record['join_manifest'])

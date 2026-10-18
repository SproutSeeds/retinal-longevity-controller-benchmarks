#!/usr/bin/env python3
"""Pin already acquired metadata without reading numeric workbook values."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
prior = HERE.parent.parent / 'cx004-metadata-recovery-2026-10-18'
receipt = json.loads((HERE / 'retrieval-1.json').read_text())
sources = [{k: v for k, v in row.items() if k in ['id', 'url', 'bytes', 'sha256']}
           for row in receipt['sources'] if row['id'].endswith('.xlsx')]
for name in ['srsf1-recovery-samples.json', 'srsf1-clock-parameters.json', 'clock-dependency-audit.json']:
    raw = (prior / name).read_bytes()
    sources.append({'id': 'prior-' + name,
                    'relative_path': '../../cx004-metadata-recovery-2026-10-18/' + name,
                    'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
(HERE / 'reference-inputs.json').write_text(json.dumps({'schema_version': 1, 'sources': sources}, indent=2) + '\n')
for name in ['reference-audit-contract.json', 'reference-inputs.json']:
    print(name, hashlib.sha256((HERE / name).read_bytes()).hexdigest())

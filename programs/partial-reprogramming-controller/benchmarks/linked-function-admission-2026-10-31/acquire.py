#!/usr/bin/env python3
"""Acquire compact public source records; never fetch sequencing reads."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
CONTROLLER = HERE.parents[1]
CACHE = CONTROLLER / '.data/linked-function-admission-2026-10-31/sources'
SPECS = []
for accession in ['GSE126633', 'GSE165180', 'GSE132828', 'GSE297557',
                  'GSE90889', 'GSE159435', 'GSE142439']:
    SPECS.append((accession + '.soft.gz',
                  f'https://ftp.ncbi.nlm.nih.gov/geo/series/{accession[:-3]}nnn/{accession}/soft/{accession}_family.soft.gz'))
for pmc in ['PMC6499805', 'PMC5851074', 'PMC9023058', 'PMC7093390',
            'PMC7724476', 'PMC13068956', 'PMC5419856', 'PMC8184696']:
    SPECS.append((pmc + '.xml',
                  f'https://www.ebi.ac.uk/europepmc/webservices/rest/{pmc}/fullTextXML'))
SPECS.append(('Gill2022.html', 'https://elifesciences.org/articles/71624'))
for accession in ['PRJNA598923', 'PRJNA589823']:
    SPECS.append((accession + '-ena.tsv',
                  'https://www.ebi.ac.uk/ena/portal/api/filereport?accession=' + accession
                  + '&result=read_run&fields=run_accession,experiment_accession,sample_accession,sample_title,experiment_title,scientific_name,library_strategy,fastq_bytes&format=tsv'))
SPECS.extend([
    ('GSE165180-series.soft.txt', 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE165180&targ=self&form=text&view=full'),
    ('GSE165180-metadata.soft.txt', 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE165180&targ=all&form=text&view=brief'),
    ('GSE142439-series.soft.txt', 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE142439&targ=self&form=text&view=full'),
    ('Saini2017-core.json', 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1016%2Fj.stem.2016.12.015&format=json&resultType=core'),
    ('Schiff2019-supplement.pdf', 'https://static-content.springer-cdn.com/esm/art%3A10.1038%2Fs42003-019-0406-6/MediaObjects/42003_2019_406_MOESM1_ESM.pdf'),
    ('Schiff2019-reporting.pdf', 'https://static-content.springer-cdn.com/esm/art%3A10.1038%2Fs42003-019-0406-6/MediaObjects/42003_2019_406_MOESM3_ESM.pdf'),
    ('Gill2022-supplement1.xlsx', 'https://cdn.elifesciences.org/articles/71624/elife-71624-supp1-v2.xlsx'),
    ('Schiff2019-supplement-media.pdf', 'https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs42003-019-0406-6/MediaObjects/42003_2019_406_MOESM1_ESM.pdf'),
    ('Schiff2019-reporting-media.pdf', 'https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs42003-019-0406-6/MediaObjects/42003_2019_406_MOESM3_ESM.pdf'),
    ('GSE165177.soft.gz', 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE165nnn/GSE165177/soft/GSE165177_family.soft.gz'),
    ('Schiff2019-supplement-full.pdf', 'https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs42003-019-0406-6/MediaObjects/42003_2019_406_MOESM1_ESM.pdf'),
    ('Gill2022-reporting.docx', 'https://cdn.elifesciences.org/articles/71624/elife-71624-transrepform1-v2.docx'),
])
for accession in ['GSE165176', 'GSE165177', 'GSE165178', 'GSE165179']:
    SPECS.append((accession + '-series.soft.txt',
                  'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=' + accession + '&targ=self&form=text&view=full'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def acquire(spec, expected_sha256=None):
    filename, url = spec
    row = {'file': filename, 'url': url,
           'checked_at_utc': datetime.now(timezone.utc).isoformat()}
    try:
        request = Request(url, headers={'User-Agent': 'LongevitySourceAudit/1.0 (public metadata only)'})
        # The named 12.5 MB Schiff supplement needs its complete PDF to inspect
        # donor tables; the earlier 8 MB failure remains in the manifest.
        limit = (16 if filename == 'Schiff2019-supplement-full.pdf' else 8) * 1024 * 1024
        with urlopen(request, timeout=35) as response:
            data = response.read(limit + 1)
            if len(data) > limit:
                raise ValueError('Compact-source byte cap exceeded')
            row.update(resolved_url=response.url, content_type=response.headers.get('Content-Type', ''))
        observed_sha256 = hashlib.sha256(data).hexdigest()
        if expected_sha256 is not None and observed_sha256 != expected_sha256:
            raise ValueError('Live source changed from the recorded digest; frozen evidence was not restored')
        target = CACHE / filename
        if target.exists() and target.read_bytes() != data:
            raise ValueError('Existing source bytes changed; preserve and review before a new acquisition')
        target.write_bytes(data)
        row.update(status='downloaded', bytes=len(data), sha256=observed_sha256,
                   path=str(target.relative_to(CONTROLLER)))
    except Exception as error:
        row.update(status='unavailable', error=str(error))
    return row


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    freeze = HERE / 'FREEZE.json'
    if freeze.exists():
        expected = {name: digest(HERE / name) for name in ['ADMISSION_CONTRACT.json', 'PLAN.md']}
        if json.loads(freeze.read_text())['frozen_files'] != expected:
            raise ValueError('Admission contract or initial plan changed after freeze')
    elif (HERE / 'CONTRACT_BINDING.json').is_file():
        binding = json.loads((HERE / 'CONTRACT_BINDING.json').read_text())
        if digest(HERE / 'ADMISSION_CONTRACT.json') != binding['contract_sha256']:
            raise ValueError('Portable frozen contract changed')
    else:
        expected = {name: digest(HERE / name) for name in ['ADMISSION_CONTRACT.json', 'PLAN.md']}
        freeze.write_text(json.dumps({'schema': 'linked-function.freeze/1',
                                     'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
                                     'known_outcome_selection': True,
                                     'frozen_files': expected}, indent=2) + '\n')
    manifest_path = HERE / 'SOURCE_MANIFEST.json'
    previous = json.loads(manifest_path.read_text())['sources'] if manifest_path.exists() else []
    preserved = {row['file']: row for row in previous}
    restore = []
    for row in previous:
        if row['status'] != 'downloaded':
            continue
        target = CONTROLLER / row['path']
        if not target.is_file():
            restore.append(row)
        elif digest(target) != row['sha256']:
            raise ValueError('Preserved source hash changed')
    # Restoring a public checkout retains the historical manifest and rejects
    # changed responses. A source download is never a new scientific result.
    with ThreadPoolExecutor(max_workers=4) as pool:
        restored = list(pool.map(lambda row: acquire((row['file'], row['url']), row['sha256']), restore))
    for row in restored:
        if row['status'] != 'downloaded':
            raise ValueError('Source restoration incomplete: ' + row['file'] + ': ' + row['error'])
    pending = [spec for spec in SPECS if spec[0] not in preserved]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for row in pool.map(acquire, pending):
            preserved[row['file']] = row
    rows = [preserved[filename] for filename, _ in SPECS]
    manifest = {'schema': 'linked-function.sources/1', 'sources': rows}
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    for row in rows:
        print(json.dumps({key: row[key] for key in ['file', 'status', 'bytes', 'error'] if key in row}), flush=True)


if __name__ == '__main__':
    main()

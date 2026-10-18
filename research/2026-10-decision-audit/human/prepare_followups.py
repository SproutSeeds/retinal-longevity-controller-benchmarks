#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from urllib.parse import urlencode

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--cache', type=Path, required=True)
args = parser.parse_args()
ids = json.loads((args.cache / 'geo-human-recovery.json').read_text())['esearchresult']['idlist']
sources = []
for i in range(0, len(ids), 100):
    sources.append({'id': f'geo-summary-{i//100+1}.json', 'url': 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?' + urlencode({'db': 'gds', 'id': ','.join(ids[i:i+100]), 'retmode': 'json'})})
for pmc in ['PMC13126874', 'PMC11641084', 'PMC12868028', 'PMC9023058']:
    sources.append({'id': pmc + '.xml', 'url': f'https://www.ebi.ac.uk/europepmc/webservices/rest/{pmc}/fullTextXML'})
sources.append({'id': 'srsf1-extended-fig6.html', 'url': 'https://www.nature.com/articles/s43587-026-01234-8/figures/12'})
for label, number in [('fig4',16), ('fig5',17), ('fig6',18)]:
    sources.append({'id': f'srsf1-source-{label}.xlsx', 'url': f'https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs43587-026-01234-8/MediaObjects/43587_2026_1234_MOESM{number}_ESM.xlsx'})
(HERE / 'source-plan-3.json').write_text(json.dumps({'sources': sources}, indent=2) + '\n')

#!/usr/bin/env python3
"""Record targeted remaining source checks; outcomes are not used for selection."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
base = 'https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs43587-026-01234-8/MediaObjects/43587_2026_1234_MOESM'
sources = [
    {'id': 'srsf1-figure4-caption.html', 'url': 'https://www.nature.com/articles/s43587-026-01234-8/figures/4'},
    {'id': 'srsf1-extended-figure5-caption.html', 'url': 'https://www.nature.com/articles/s43587-026-01234-8/figures/11'},
    {'id': 'GSM9612108.txt', 'url': 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM9612108&targ=self&form=text&view=full'},
    {'id': 'srsf1-source-fig2.xlsx', 'url': base + '14_ESM.xlsx'},
]
for table, moesm in [(1, 4), (2, 5), (3, 6), (5, 8), (6, 9), (7, 10), (8, 11), (9, 12)]:
    sources.append({'id': f'srsf1-supplement{table}.xlsx', 'url': base + f'{moesm}_ESM.xlsx'})
for filename in ['ApplyNewData.R', 'ProcessFibroblastData.R', 'TrainClock.R']:
    sources.append({'id': 'clock-' + filename,
                    'url': 'https://raw.githubusercontent.com/saschajung/Clock/7ae5f38b7ea74f76cb13076b64350d5930bb152f/' + filename})
sources.append({'id': 'msc-ena-first-run.tsv', 'url': 'https://www.ebi.ac.uk/ena/portal/api/filereport?accession=DRR726438&result=read_run&fields=run_accession,study_accession,sample_accession,sample_title,experiment_title,library_strategy,fastq_bytes&format=tsv'})
(HERE / 'source-plan-4.json').write_text(json.dumps({'sources': sources}, indent=2) + '\n')

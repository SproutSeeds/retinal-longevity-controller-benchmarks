#!/usr/bin/env python3
"""Record exact, bounded discovery queries before downloading their results."""
import json
from pathlib import Path
from urllib.parse import urlencode

HERE = Path(__file__).resolve().parent
queries = [
    ('epmc-human-transient', '(TITLE_ABS:"partial reprogramming" OR TITLE_ABS:"transient reprogramming") AND (TITLE_ABS:human OR TITLE_ABS:fibroblast) AND FIRST_PDATE:[1900-01-01 TO 2026-10-18]', 'europepmc'),
    ('epmc-human-withdrawal', '(TITLE_ABS:reprogramming) AND (TITLE_ABS:withdrawal OR TITLE_ABS:washout OR TITLE_ABS:recovery) AND (TITLE_ABS:human OR TITLE_ABS:fibroblast) AND FIRST_PDATE:[1900-01-01 TO 2026-10-18]', 'europepmc'),
    ('geo-human-recovery', '"Homo sapiens"[Organism] AND reprogramming AND (withdrawal OR transient OR partial OR rejuvenation) AND gse[Entry Type]', 'geo'),
]
sources = []
for name, query, engine in queries:
    if engine == 'europepmc':
        url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?' + urlencode({'query': query, 'format': 'json', 'resultType': 'core', 'pageSize': 1000})
    else:
        url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?' + urlencode({'db': 'gds', 'term': query, 'retmode': 'json', 'retmax': 1000})
    sources.append({'id': name + '.json', 'url': url, 'query': query, 'engine': engine, 'max_bytes': 20_000_000})
sources.extend([
    {'id': 'stampscreen-tree-main.json', 'url': 'https://api.github.com/repos/pranamanam/STAMPScreen/git/trees/main?recursive=1'},
    {'id': 'clock-readme.txt', 'url': 'https://raw.githubusercontent.com/saschajung/Clock/7ae5f38b7ea74f76cb13076b64350d5930bb152f/README.md'},
    {'id': 'clock-filter.R', 'url': 'https://raw.githubusercontent.com/saschajung/Clock/7ae5f38b7ea74f76cb13076b64350d5930bb152f/GetGenesForRemoval.R'},
    {'id': 'srsf1-geo-files.html', 'url': 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE325nnn/GSE325735/suppl/'},
    {'id': 'gse326022-files.html', 'url': 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE326nnn/GSE326022/suppl/'},
    {'id': 'gse165177-files.html', 'url': 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE165nnn/GSE165177/suppl/'},
    {'id': 'gse165179-files.html', 'url': 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE165nnn/GSE165179/suppl/'},
])
(HERE / 'source-plan-2.json').write_text(json.dumps({'sources': sources}, indent=2) + '\n')

#!/usr/bin/env python3
"""Freeze source-panel orthology from a pinned HCOP snapshot, without expression."""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'source-panels.json'
HCOP_SHA256 = '0cfb78e4eb273751e0557e8230445a60e844bfaf958e32740d4a266fb41cdb35'
HCOP_URL = 'https://storage.googleapis.com/public-download-files/hcop/human_mouse_hcop_fifteen_column.txt.gz'
TRANS_GENES = ['POU5F1', 'SOX2', 'KLF4', 'MYC']


def mapping_from_rows(rows, symbols):
    result = {}
    for symbol in sorted(symbols):
        candidates = [r for r in rows if r['human_symbol'] == symbol]
        eligible = [r for r in candidates if 'HGNC' in r['support'].split(',')]
        if len(eligible) > 1:
            raise ValueError('Ambiguous HGNC-supported orthology: ' + symbol)
        if eligible and (not eligible[0]['mouse_ensembl_gene'].startswith('ENSMUSG')
                         or not eligible[0]['mgi_id'].startswith('MGI:')):
            raise ValueError('Incomplete mouse identifier: ' + symbol)
        result[symbol] = {
            'status': 'mapped' if eligible else 'no_HGNC_supported_mouse_ortholog',
            'mouse_symbol': eligible[0]['mouse_symbol'] if eligible else None,
            'selected': eligible[0] if eligible else None,
            'all_candidates': candidates,
        }
    selected_symbols = [v['mouse_symbol'] for v in result.values() if v['status'] == 'mapped']
    if len(set(selected_symbols)) != len(selected_symbols):
        raise ValueError('Many source genes would be double counted as one mouse gene')
    return result


def main(path):
    if hashlib.sha256(path.read_bytes()).hexdigest() != HCOP_SHA256:
        raise ValueError('HCOP source snapshot changed')
    panels = json.loads(SOURCE.read_text())
    selected_panels = {key: panels[key] for key in ['cycle_panel', 'stress_panel', 'reprogramming_state']}
    selected_panels['reprogramming_without_OSKM_overlap'] = [
        g for g in panels['reprogramming_state'] if g not in TRANS_GENES]
    symbols = set(sum(selected_panels.values(), [])) | set(TRANS_GENES)
    with gzip.open(path, 'rt') as stream:
        rows = list(csv.DictReader(stream, delimiter='\t'))
    result = {
        'claim_level': 'Verified',
        'scope': 'Pinned symbol mapping; orthology does not establish conserved function or panel validity.',
        'source_url': HCOP_URL,
        'source_sha256': HCOP_SHA256,
        'source_bytes': path.stat().st_size,
        'source_help': 'https://www.genenames.org/help/hcop/',
        'source_reference': 'https://doi.org/10.1093/bib/bbab155',
        'panel_source': '../cx004-independent-comparator-2026-10-18/panels.json',
        'panel_source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'rule': 'Use exactly one HGNC-supported HCOP human-to-mouse candidate. Record all alternative assertions. No expression-based selection, case conversion, paralog substitution or imputation.',
        'transgene_human_symbols': TRANS_GENES,
        'transgene_mouse_symbols': ['Pou5f1', 'Sox2', 'Klf4', 'Myc'],
        'panels': selected_panels,
        'mapping': mapping_from_rows(rows, symbols),
        'exceptions': {
            'CXCL8': 'HCOP reports a Cxcl15 assertion from Treefam and OrthoDB only; it has no HGNC support and is excluded by the fixed rule.',
            'CDKN2A': 'Cdkn2a has HGNC support; the Cdkn2b alternative lacks it. Retain both assertions in the audit.',
            'CD24': 'HGNC-supported mouse symbol is Cd24a; do not use case conversion.',
            'TP53': 'HGNC-supported mouse symbol is Trp53; do not use case conversion.',
            'POU5F1': 'Pou5f1 has HGNC support; the Pou5f2 alternative does not. The full panel remains transgene-confounded.',
        },
        'failed_source_paths': [
            {'url': 'https://storage.googleapis.com/public-download-files/hgnc/hcop/human_mouse_hcop_fifteen_column.txt.gz', 'reason': 'HTTP 404; corrected by inspecting the official HCOP download link.'},
            {'url': 'https://ftp.ebi.ac.uk/pub/databases/genenames/hcop/human_mouse_hcop_fifteen_column.txt.gz', 'reason': 'HTTP 404; corrected by inspecting the official HCOP download link.'},
        ],
        'mgi_crosscheck': {
            'url': 'https://www.informatics.jax.org/downloads/reports/HOM_MouseHumanSequence.rpt',
            'sha256': '5139ab9cf54d1b48cdae3d1034ba0cf4a8e794a0e24074bcfe5354346ff309f8',
            'use': 'Inspected before expression. Group-level CDKN2A/CDKN2B ambiguity led to explicit HCOP assertions; MGI homology groups are not used to select expression features.'
        },
        'expression_outcomes_examined': False,
    }
    (HERE / 'orthology.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print('Frozen orthology:', len(result['mapping']), 'source symbols;',
          sum(v['status'] == 'mapped' for v in result['mapping'].values()), 'mapped')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--hcop', type=Path, required=True)
    main(parser.parse_args().hcop)

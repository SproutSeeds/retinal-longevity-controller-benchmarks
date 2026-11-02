#!/usr/bin/env python3
"""Recheck source content with dated freshness, without inferring cell labels."""
from collections import Counter
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[1]/'.data/gse350289-assignment-recheck-2026-11-01'
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RID='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
LIBRARIES=['Ctrl','Sample1','Sample2','Sample3']


def sha(data):return hashlib.sha256(data).hexdigest()
def read(path):return json.loads(path.read_text())
def rendered(value):return json.JSONEncoder(indent=2,sort_keys=True,allow_nan=False).encode(value)+'\n'


def require_xlsx(data):
    """A successful request or .xlsx name is insufficient evidence of a workbook."""
    if not zipfile.is_zipfile(io.BytesIO(data)):
        raise ValueError('Not a workbook ZIP')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if not {'xl/workbook.xml','xl/_rels/workbook.xml.rels'}.issubset(archive.namelist()):
            raise ValueError('ZIP lacks XLSX workbook structure')


def census(path,barcodes):
    data=path.read_bytes();require_xlsx(data)
    output=[]
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        strings=[]
        if 'xl/sharedStrings.xml' in archive.namelist():
            strings=[''.join(n.itertext()) for n in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
        relations={n.attrib['Id']:n.attrib['Target'] for n in ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
        for sheet in ET.fromstring(archive.read('xl/workbook.xml')).find('s:sheets',NS):
            target=relations[sheet.attrib[RID]]
            target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
            counts=Counter();ages=Counter();rows=set();matched=0
            with archive.open(target) as stream:
                for event,cell in ET.iterparse(stream,events=['end']):
                    if cell.tag!='{'+NS['s']+'}c':continue
                    if cell.find('s:f',NS) is not None:raise ValueError('Formula requires separate source review')
                    value=cell.findtext('s:v','',NS)
                    if cell.get('t')=='s':value=strings[int(value)]
                    elif cell.get('t')=='inlineStr':value=''.join(cell.find('s:is',NS).itertext())
                    if value!='':
                        address=cell.attrib['r'];column=re.match(r'[A-Z]+',address).group()
                        counts[column]+=1;rows.add(int(re.search(r'\d+',address).group()))
                        matched+=value in barcodes
                        if column=='D':ages[value]+=1
                    cell.clear()
            output.append({'sheet':sheet.attrib['name'],'nonempty_rows':len(rows),
                'nonempty_cells_by_column':dict(sorted(counts.items())),
                'column_D_value_counts':dict(sorted(ages.items())) if sheet.attrib['name']!='README' else {},
                'exact_deposited_barcode_cells':matched})
    return output


def evidence_state(current_workbook_accepted,exact_mapping_keys):
    if not current_workbook_accepted:return 'INCONCLUSIVE_current_workbook; no_mapping_admission'
    if exact_mapping_keys==0:return 'no_usable_assignment_keys; no_mapping_admission'
    return 'candidate_requires_explicit_context_and_QC_join_verification'


def products(cache=SOURCE):
    manifest=read(HERE/'SOURCE_MANIFEST.json')
    for name,pin in manifest['files'].items():
        body=(cache/name).read_bytes()
        if sha(body)!=pin['sha256'] or len(body)!=pin['bytes']:
            raise ValueError('Source changed; fresh audit required: '+name)
    barcodes=set();barcode_counts={}
    for library in LIBRARIES:
        filename='GSE350289_'+library+'_barcodes.tsv.gz'
        with gzip.open(cache/filename,'rt',newline='') as stream:
            keys=[line.rstrip('\r\n') for line in stream]
        if any(not key or key!=key.strip() for key in keys) or len(set(keys))!=len(keys):
            raise ValueError('Blank/duplicate/whitespace-altered barcode in '+filename)
        barcode_counts[library]={'records':len(keys),'unique':len(set(keys))}
        barcodes.update(keys)
    workbook='GSE350289_metadata_individual_cells.xlsx'
    sheets=census(cache/workbook,barcodes)
    baseline=read(HERE/'BASELINE.json')
    assert sha((cache/workbook).read_bytes())==baseline['file_sha256']
    for old,new in zip(baseline['sheets'],sheets):
        assert old['name']==new['sheet']
        expected={chr(64+int(k)):v for k,v in old['nonempty_by_column'].items()}
        assert expected==new['nonempty_cells_by_column']
    root=ET.fromstring((cache/'preprint-source.xml').read_bytes())
    if root.tag!='article':raise ValueError('Not article XML')
    details=read(cache/'biorxiv-details.json')['collection']
    assert len(details)==1 and details[0]['doi']=='10.64898/2026.10.21.760791' and details[0]['version']=='1'
    all_text=' '.join(' '.join(root.itertext()).split())
    title=' '.join(root.find('.//article-title').itertext())
    assert title==details[0]['title']
    assert '3 male donors and 3 female donors' in all_text
    visible=read(HERE/'GEO_VISIBLE_FACTS.json')
    assert len(visible['listed_supplementary_files'])==14 and visible['pool_description_donors_per_age_group']==3
    appendix=next(s for s in root.findall('.//sec') if s.find('title') is not None and 'Appendix B' in ''.join(s.find('title').itertext()))
    hrefs=[v for n in root.iter() for k,v in n.attrib.items() if k.endswith('href')]
    paper={'doi':details[0]['doi'],'version':1,'date':details[0]['date'],'license':details[0]['license'],
        'data_availability_points_to_GSE350289':'Raw and processed scRNA data is hosted on Geo as GSE350289.' in all_text,
        'supplementary_material_download_elements':len(root.findall('.//supplementary-material')),
        'appendix_B_figures':len(appendix.findall('.//fig')),'appendix_B_tables':len(appendix.findall('.//table-wrap')),
        'explicit_github_href_found':any('github.com' in u.lower() for u in hrefs),
        'pool_description':{'male_donors_per_age_group':3,'female_donors_per_age_group':3,'total_implied':6},
        'scope':'Inspected v1 article XML and browser-visible article. No global absence claim for supplements or code stored elsewhere.'}
    exact_keys=sum(s['exact_deposited_barcode_cells'] for s in sheets if s['sheet']!='README')
    result={'schema':'controller.assignment-recheck-results/1','historical_content_claim_level':'Verified','current_workbook_reacquisition':'INCONCLUSIVE',
        'retained_workbook_acquired_at':manifest['files'][workbook]['acquired_at_utc'],'retained_workbook_sha256':manifest['files'][workbook]['sha256'],
        'retained_workbook_matches_prior_audit':True,'sheets':sheets,'retained_barcode_files':barcode_counts,
        'retained_barcode_records':sum(v['records'] for v in barcode_counts.values()),'retained_unique_full_barcode_strings':len(barcodes),
        'exact_barcode_cells_in_retained_metadata':exact_keys,'accepted_current_mapping_keys':0,
        'mapping_admission':evidence_state(False,exact_keys),'perturbation_outcome_analysis_unlocked':False,
        'preprint_review':paper,'pool_description_disagreement':{'GEO_donors_per_age_group':3,'preprint_implied_donors_per_age_group':6,'resolution':'Unresolved source descriptions; no donor identities or independent-unit counts inferred.'},
        'expression_matrix_downloaded':False,'new_training_or_biological_effect_computed':False,
        'interpretation':'Retained originals verify their dated content only. Current workbook bytes were not acquired. The pointer is useful discovery evidence; complete sample assignment remains unverified.'}
    return {'RESULTS.json':rendered(result)}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--cache',type=Path,default=SOURCE);parser.add_argument('--write',action='store_true');args=parser.parse_args()
    output=products(args.cache)
    for name,value in output.items():
        if args.write:(HERE/name).write_text(value)
        elif (HERE/name).read_text()!=value:raise ValueError('Replay differs: '+name)
    print('PASS dated source audit: retained content verified; current workbook INCONCLUSIVE; zero current assignment admissions.')

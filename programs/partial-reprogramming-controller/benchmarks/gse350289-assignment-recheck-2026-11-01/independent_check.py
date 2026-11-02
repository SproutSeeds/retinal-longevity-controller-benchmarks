#!/usr/bin/env python3
"""Independent read-only workbook census with openpyxl, not the XML reader."""
from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path

import openpyxl

HERE=Path(__file__).resolve().parent


def main(cache):
    source=cache/'GSE350289_metadata_individual_cells.xlsx'
    expected=json.loads((HERE/'RESULTS.json').read_text())
    assert hashlib.sha256(source.read_bytes()).hexdigest()==expected['retained_workbook_sha256']
    workbook=openpyxl.load_workbook(source,read_only=True,data_only=False)
    observed=[]
    for sheet in workbook:
        columns=Counter();rows=0;ages=Counter()
        for cells in sheet.iter_rows():
            populated=False
            for i,cell in enumerate(cells):
                if cell.data_type=='f':raise ValueError('Unexpected formula')
                value=cell.value
                if value is not None and value!='':
                    columns[openpyxl.utils.get_column_letter(i+1)]+=1;populated=True
                    if i==3:ages[str(value)]+=1
            rows+=populated
        observed.append({'sheet':sheet.title,'nonempty_rows':rows,'nonempty_cells_by_column':dict(columns),'column_D_value_counts':dict(ages)})
    workbook.close()
    for actual,pinned in zip(observed,expected['sheets']):
        for key in actual:assert actual[key]==pinned[key],(actual['sheet'],key)
    assert len(observed)==len(expected['sheets'])==5
    return {'schema':'controller.independent-workbook-census/1','status':'PASS','claim_level':'Verified retained-source contents only','reader':'openpyxl '+openpyxl.__version__,'source_sha256':expected['retained_workbook_sha256'],'sheets_checked':5,'nonempty_nonREADME_cells':sum(sum(s['nonempty_cells_by_column'].values()) for s in observed if s['sheet']!='README'),'imports_primary_XML_reader':False,'current_workbook_reacquisition_verified':False,'scope':'Independent scalar-cell census of the dated retained workbook. Current workbook bytes were not acquired; no cell assignment or biological outcome is admitted.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--cache',type=Path,default=HERE.parents[1]/'.data/gse350289-assignment-recheck-2026-11-01');parser.add_argument('--emit',type=Path);args=parser.parse_args()
    result=main(args.cache);value=json.JSONEncoder(indent=2,sort_keys=True).encode(result)+'\n'
    if args.emit:args.emit.write_text(value)
    print(value.strip())

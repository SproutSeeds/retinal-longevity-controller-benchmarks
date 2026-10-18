#!/usr/bin/env python3
"""Run public saved-artifact checks in isolation; no biological downloads."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--receipt',type=Path)
    args=parser.parse_args()
    if shutil.which('uv') is None:
        parser.error('Install uv for the pinned local numerical dependencies')
    files=json.loads((HERE/'public-files.json').read_text())['files']
    rows=[]
    with tempfile.TemporaryDirectory(prefix='cx004-decision-checks-') as td:
        temp=Path(td)
        for name in files:
            rel=Path(name)
            if rel.is_absolute() or '..' in rel.parts or (HERE/rel).is_symlink():
                raise ValueError('Unsafe publication path')
            (temp/rel).parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(HERE/rel,temp/rel)
        commands=[
            [sys.executable,'build_decision.py'],
            [sys.executable,'human/verify.py'],
            [sys.executable,'human/audit_replicate_labels.py'],
            [sys.executable,'-m','unittest','discover','-s','human','-p','test_*.py'],
            [sys.executable,'recovery/verify.py'],
            [sys.executable,'-m','unittest','discover','-s','recovery','-p','test_*.py'],
            ['uv','run','--python','3.12','--with','numpy==2.5.4','--with','h5py==3.15.1','python','ocular/test_analysis.py'],
            ['uv','run','--python','3.12','--with','numpy==2.5.4','--with','h5py==3.15.1','python','ocular/verify.py','--receipt',str(temp/'saved-check.json')],
        ]
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
        for command in commands:
            result=subprocess.run(command,cwd=temp,env=env,capture_output=True,text=True,timeout=600)
            row={'command':['python3' if x==sys.executable else '<temporary-receipt>' if x==str(temp/'saved-check.json') else x for x in command],
                 'status':'PASS' if result.returncode==0 else 'FAIL','exit_code':result.returncode,
                 'stdout':result.stdout.strip(),'stderr':result.stderr.strip()}
            rows.append(row)
            print(row['status'],' '.join(row['command']),flush=True)
            if result.returncode:
                print(result.stdout,result.stderr)
                break
    report={'schema':'cx004-portable-checks/v1','status':'PASS' if len(rows)==8 and all(r['exit_code']==0 for r in rows) else 'FAIL',
            'checks':rows,'biological_downloads':False,'published_artifacts_modified':False,
            'scope':'Saved-artifact arithmetic and 28 synthetic regression/failure-control tests. No biological claim promotion.'}
    if args.receipt:
        args.receipt.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(report['status'],len(rows),'portable commands')
    raise SystemExit(report['status']!='PASS')


if __name__=='__main__':
    main()

#!/usr/bin/env python3
"""Fetch only declared public inputs with byte/hash verification and bounded storage."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request

HERE=Path(__file__).resolve().parent
CAP=2_000_000_000
FLOOR=8_000_000_000

def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def main():
 p=argparse.ArgumentParser();p.add_argument('--group',choices=['small','perturbation'],default='small');p.add_argument('--cache',type=Path,default=HERE/'.cache');p.add_argument('--allow-large',action='store_true');a=p.parse_args()
 if a.group=='perturbation' and not a.allow_large:p.error('The 1.427 GB file requires --allow-large.')
 rows=json.loads((HERE/'input-files.json').read_text())['files']
 sources=json.loads((HERE/'source-manifest.json').read_text())['files']
 rows += [dict(id=r['name'],url=r['url'],bytes=r['bytes'],sha256=r['sha256']) for r in sources if r['name'] in ['liver-minus.h5','liver-plus.h5']]
 selected=[r for r in rows if (r['id']=='exp3_merged_not_normalized.h5ad')==(a.group=='perturbation')]
 a.cache.mkdir(parents=True,exist_ok=True)
 for r in selected:
  if Path(r['id']).name!=r['id'] or not r['url'].startswith('https://'):raise ValueError('Unsafe manifest entry')
  out=a.cache/r['id'];partial=out.with_name(out.name+'.part')
  if out.exists():
   if out.stat().st_size!=r['bytes'] or digest(out)!=r['sha256']:raise ValueError('Existing input mismatch: '+str(out))
   print('verified',out.name);continue
  used=sum(x.stat().st_size for x in a.cache.rglob('*') if x.is_file())
  if used+r['bytes']>CAP or shutil.disk_usage(a.cache).free-r['bytes']<FLOOR:raise RuntimeError('Cache cap or free-space floor reached')
  h=hashlib.sha256();count=0
  try:
   request=urllib.request.Request(r['url'],headers={'User-Agent':'retinal-public-research/2026-10'})
   with urllib.request.urlopen(request,timeout=60) as response,partial.open('wb') as f:
    while True:
     chunk=response.read(1024*1024)
     if not chunk:break
     count+=len(chunk)
     if count>r['bytes']:raise ValueError('Response exceeds declared size')
     h.update(chunk);f.write(chunk)
   if count!=r['bytes'] or h.hexdigest()!=r['sha256']:raise ValueError('Source bytes or hash changed: '+r['id'])
   partial.replace(out);print('downloaded and verified',out.name,count)
  except Exception:
   partial.unlink(missing_ok=True)
   raise

if __name__=='__main__':main()

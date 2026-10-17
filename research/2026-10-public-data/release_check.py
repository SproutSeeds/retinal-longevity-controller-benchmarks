#!/usr/bin/env python3
"""Check the curated public research package, links, quantities and released bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');args=parser.parse_args()
 manifest=json.loads((ROOT/'research-release.json').read_text());checks=[]
 def check(name,ok):checks.append({'name':name,'status':'PASS' if ok else 'FAIL'})
 for name,wanted in manifest['files'].items():
  p=ROOT/name;check('sha256:'+name,p.is_file() and sha(p)==wanted)
  if p.suffix in ['.md','.txt','.json','.py','.mjs','.yml']:
   text=p.read_text();check('public_scope:'+name,not re.search(r'/(?:Users|Volumes)/|github[.]com/SproutSeeds/longevity-research[/\s]|PRIVATE KEY[-]{5}',text))
   check('credential_patterns:'+name,not re.search(r'gh[pousr]_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9]{32,}',text))
   if p.suffix=='.md':
    for link in re.findall(r'\]\(([^)]+)\)',text):
     target=link.split('#')[0]
     if target and not re.match(r'[a-z]+:',target):check('relative_link:'+name+':'+target,(p.parent/target).exists())
 b=json.loads((HERE/'budget-quantities.json').read_text())
 per=sum(sum(row[k] for k in ['reference','induced_or_continued','withdrawal']) for row in b['pilot_rows'])
 check('pilot_arithmetic',per==b['pilot_libraries_per_donor']==11 and per*b['donors']==b['pilot_libraries']==33)
 extra=len(b['full_ladder_extra_days'])*b['full_ladder_extra_conditions_per_day']*b['donors']
 check('full_ladder_arithmetic',extra==b['full_ladder_extra_libraries']==24 and extra+b['pilot_libraries']==b['full_ladder_libraries']==57)
 check('optional_extension_arithmetic',b['optional_day49_extra_conditions']*b['donors']==b['optional_day49_extra_libraries']==6)
 check('no_invented_cost',b['unit_costs'] is None and b['total_cost'] is None)
 with zipfile.ZipFile(ROOT/'presentation/retinal-public-data.pptx') as z:
  names=z.namelist();check('eleven_slides',len([n for n in names if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)])==11)
  check('three_native_charts',len([n for n in names if re.search(r'/charts/chart\d+\.xml$',n)])==3)
  check('eleven_notes',len([n for n in names if re.fullmatch(r'ppt/notesSlides/notesSlide\d+\.xml',n)])==11)
 check('spoken_txt_matches_md',(ROOT/'presentation/spoken-notes.txt').read_bytes()==(ROOT/'presentation/spoken-notes.md').read_bytes())
 result={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'FAIL','scope':'Release hashes, relative links, public-path/credential pattern checks, budget arithmetic and presentation structure; no biological validation.','checks':checks,'passed':sum(c['status']=='PASS' for c in checks),'total':len(checks)}
 if args.write:(ROOT/'research-release-checks.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(result['status'],str(result['passed'])+'/'+str(result['total']))
 for c in checks:
  if c['status']=='FAIL':print(c['name'])
 raise SystemExit(0 if result['status']=='PASS' else 1)

if __name__=='__main__':main()

#!/usr/bin/env python3
"""Fetch explicitly selected, hash-pinned public inputs into a user-chosen cache."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import urllib.request

HERE=Path(__file__).resolve().parent


def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            digest.update(block)
    return digest.hexdigest()


def fetch(row, cache):
    name=row['id']
    if Path(name).name!=name or not row['url'].startswith('https://'):
        raise ValueError('Manifest must use a basename and HTTPS source')
    out=cache/name
    if out.is_symlink():
        raise ValueError('Cache output must not be a symlink')
    if out.exists():
        if sha(out)!=row['sha256'] or ('bytes' in row and out.stat().st_size!=row['bytes']):
            raise ValueError('Existing cache differs from pinned source: '+name)
        return {'id':name,'status':'verified_cached','sha256':row['sha256']}
    limit=row.get('bytes',row.get('max_bytes'))
    if not limit or limit>1_000_000_000:
        raise ValueError('Missing or excessive download bound')
    if shutil.disk_usage(cache).free < 8*1024**3+limit:
        raise ValueError('Keep at least 8 GiB free after this bounded download')
    with tempfile.NamedTemporaryFile(prefix='cx004-source-',dir=cache,delete=False) as stream:
        temporary=Path(stream.name)
        try:
            with urllib.request.urlopen(row['url'],timeout=60) as response:
                if not response.url.startswith('https://'):
                    raise ValueError('Unexpected non-HTTPS redirect')
                total=0
                while True:
                    block=response.read(min(1024*1024,limit+1-total))
                    if not block:
                        break
                    total+=len(block)
                    if total>limit:
                        raise ValueError('Source exceeds pinned size bound')
                    stream.write(block)
            stream.flush()
            if 'bytes' in row and total!=row['bytes']:
                raise ValueError('Source byte count changed')
            if sha(temporary)!=row['sha256']:
                raise ValueError('Source hash changed; review new version separately')
            temporary.replace(out)
        finally:
            temporary.unlink(missing_ok=True)
    return {'id':name,'status':'downloaded_verified','sha256':row['sha256']}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--group',action='append',choices=['neural','human-bulk','human-timecourse','neural-bulk'])
    parser.add_argument('--cache',type=Path)
    parser.add_argument('--list',action='store_true')
    args=parser.parse_args()
    manifest=json.loads((HERE/'inputs.json').read_text())
    rows=[x for x in manifest['sources'] if not args.group or x['group'] in args.group]
    if args.list:
        for row in rows:
            print(row['group'],row['id'],row.get('bytes',row.get('max_bytes')))
        return
    if not args.group or args.cache is None:
        parser.error('Choose at least one --group and an explicit --cache')
    args.cache.mkdir(parents=True,exist_ok=True)
    for row in rows:
        print(json.JSONEncoder(sort_keys=True).encode(fetch(row,args.cache)))


if __name__=='__main__':
    main()

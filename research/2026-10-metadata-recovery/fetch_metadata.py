#!/usr/bin/env python3
"""Fetch a bounded, explicit public metadata plan; retain hashes and failures."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
from urllib.request import Request, urlopen


def fetch_one(item, cache):
    name = item['id']
    if Path(name).name != name:
        raise ValueError('Metadata IDs must be plain filenames')
    limit = item.get('max_bytes', 20_000_000)
    record = dict(item, checked_at_utc=datetime.now(timezone.utc).isoformat())
    try:
        if shutil.disk_usage(cache).free < 8_000_000_000:
            raise RuntimeError('8 GB free-space floor')
        request = Request(item['url'], headers={'User-Agent': 'PublicMetadataRecovery/1.0'})
        with urlopen(request, timeout=40) as response:
            body = response.read(limit + 1)
            record['http_status'] = response.status
            record['content_type'] = response.headers.get('Content-Type', '')
        if len(body) > limit:
            raise ValueError('Explicit per-file byte limit exceeded')
        if name.endswith('.json'):
            json.loads(body)
        if name.endswith('.xlsx') and not body.startswith(b'PK'):
            raise ValueError('Expected XLSX archive')
        (cache / name).write_bytes(body)
        record.update(status='retrieved', bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    except Exception as error:
        record.update(status='access_failure', error=str(error))
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('plan', type=Path)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    items = json.loads(args.plan.read_text())['sources']
    if len({x['id'] for x in items}) != len(items):
        raise ValueError('Duplicate metadata IDs')
    args.cache.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(lambda item: fetch_one(item, args.cache), items))
    args.receipt.write_text(json.dumps({'schema_version': 1, 'sources': rows}, indent=2) + '\n')
    for row in rows:
        print(row['id'], row['status'], row.get('bytes', ''), row.get('error', ''))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Fetch bounded public research sources and preserve byte-level receipts."""
from __future__ import annotations
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
from pathlib import Path
import urllib.request


def fetch(source, cache):
    row = dict(source)
    row['checked_at_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        req = urllib.request.Request(source['url'], headers={'User-Agent': 'CX004-public-research-source-audit/1.0'})
        with urllib.request.urlopen(req, timeout=45) as response:
            cap = source.get('max_bytes', 20_000_000)
            raw = response.read(cap + 1)
            if len(raw) > cap:
                raise ValueError(f'Source exceeds {cap} byte cap')
            row.update(status='retrieved', http_status=response.status,
                       final_url=response.url, content_type=response.headers.get('Content-Type'),
                       bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        (cache / source['id']).write_bytes(raw)
    except Exception as exc:
        row.update(status='failed', error=f'{type(exc).__name__}: {exc}')
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('plan', type=Path)
    parser.add_argument('--cache', required=True, type=Path)
    parser.add_argument('--receipt', required=True, type=Path)
    args = parser.parse_args()
    sources = json.loads(args.plan.read_text())['sources']
    ids = [r['id'] for r in sources]
    if len(set(ids)) != len(ids) or any(Path(s).name != s for s in ids):
        raise ValueError('Source IDs must be unique basenames')
    args.cache.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(lambda s: fetch(s, args.cache), sources))
    args.receipt.write_text(json.dumps({'schema_version': 1, 'sources': rows}, indent=2) + '\n')
    for row in rows:
        print(row['id'], row['status'], row.get('bytes', row.get('error')))


if __name__ == '__main__':
    main()

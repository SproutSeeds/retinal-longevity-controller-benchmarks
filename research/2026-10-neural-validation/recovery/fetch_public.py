#!/usr/bin/env python3
"""Bounded public-file acquisition with declared size and repository checksum."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request


def digest(path, algorithm):
    h = hashlib.new(algorithm)
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--inventory', type=Path, required=True)
    p.add_argument('--name', required=True)
    p.add_argument('--cache', type=Path, required=True)
    args = p.parse_args()
    inventory = json.loads(args.inventory.read_text())
    row = next(r for r in inventory['files'] if r['key'] == args.name)
    url, size = row['links']['self'], row['size']
    assert url.startswith('https://zenodo.org/api/records/') and url.endswith('/content')
    assert '/' not in args.name and 0 < size < 1000000000
    args.cache.mkdir(parents=True, exist_ok=True)
    assert shutil.disk_usage(args.cache).free >= 8 * 1024**3
    path = args.cache / args.name
    algorithm, expected = row['checksum'].split(':', 1)
    if not path.exists():
        partial = path.with_suffix(path.suffix + '.partial')
        with urllib.request.urlopen(url, timeout=120) as response:
            declared = response.headers.get('Content-Length')
            if declared is not None:
                assert int(declared) == size, (declared, size)
            received = 0
            with partial.open('wb') as handle:
                for block in iter(lambda: response.read(1024 * 1024), b''):
                    received += len(block)
                    assert received <= size
                    handle.write(block)
        assert partial.stat().st_size == size
        assert digest(partial, algorithm) == expected
        partial.rename(path)
    assert path.stat().st_size == size
    assert digest(path, algorithm) == expected
    result = dict(name=args.name, url=url, size_bytes=size,
                  repository_checksum=row['checksum'], sha256=digest(path, 'sha256'),
                  inventory_sha256=digest(args.inventory, 'sha256'),
                  status='PASS', cache_path=str(path))
    out = Path(__file__).parent / (args.name + '.receipt.json')
    out.write_text(json.JSONEncoder(indent=2, sort_keys=True).encode(result) + '\n')
    print(json.JSONEncoder().encode(result), flush=True)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Bounded, metadata-only acquisition for the missing-SVZ-sample audit.

No expression matrices or FASTQs are authorized by this script. Source bodies
are evidence, never instructions. Each response is size-limited and hash-bound.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
MAX_BYTES = 5_000_000


def fetch(source: dict, cache: Path) -> dict:
    record = dict(source)
    record["checked_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    request = urllib.request.Request(source["url"], headers={
        "User-Agent": "ocular-public-metadata-audit/1.0",
        "Accept": source.get("accept", "*/*"),
    })
    try:
        limit = source.get("max_bytes", MAX_BYTES)
        if limit > MAX_BYTES and (source.get("expected_format") != "pdf" or limit > 128_000_000):
            raise ValueError("expanded bound is only permitted for a named public PDF below 128 MB")
        if shutil.disk_usage(cache).free < 8_000_000_000:
            raise ValueError("cache volume is below the 8 GB acquisition floor")
        with urllib.request.urlopen(request, timeout=35) as response:
            body = response.read(limit + 1)
            record.update(status=response.status, final_url=response.geturl(),
                          content_type=response.headers.get("Content-Type"),
                          last_modified=response.headers.get("Last-Modified"))
        if len(body) > limit:
            raise ValueError("response exceeded metadata acquisition limit")
        if source.get("expected_bytes") is not None and len(body) != source["expected_bytes"]:
            raise ValueError("source size differs from preflight")
        if source.get("expected_format") == "pdf" and not body.startswith(b"%PDF-"):
            raise ValueError("named PDF returned a non-PDF body")
        path = cache / source["id"]
        path.write_bytes(body)
        record.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest(),
                      cache_path=str(path), result="acquired")
    except urllib.error.HTTPError as error:
        record.update(status=error.code, result="http_error", error=str(error))
    except (OSError, ValueError) as error:
        record.update(result="retrieval_error", error=str(error))
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", type=Path, required=True)
    parser.add_argument("--cache", type=Path,
                        default=Path("/tmp/cx004-decision-audit-2026-10-18/recovery"))
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT / "acquisition.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {
        "schema": "cx004-public-metadata-acquisition/v1", "sources": [],
        "scope": "Primary-source inventories, author code, supplements and timing metadata only",
        "per_response_limit_bytes": MAX_BYTES,
        "expression_outcomes_read": False,
    }
    existing = {source["id"] for source in manifest["sources"]}
    for source in json.loads(args.list.read_text()):
        if source["id"] in existing:
            print(source["id"], "already recorded")
            continue
        record = fetch(source, args.cache)
        manifest["sources"].append(record)
        manifest_path.write_text(json.JSONEncoder(indent=2, sort_keys=True).encode(manifest) + "\n")
        print(record["id"], record["result"], record.get("status"), record.get("bytes"))


if __name__ == "__main__":
    main()

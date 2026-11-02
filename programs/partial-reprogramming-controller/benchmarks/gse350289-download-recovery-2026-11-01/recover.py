#!/usr/bin/env python3
"""Retrieve the named GEO workbook using the observed working download route."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import time
from urllib.parse import urlparse
import zipfile

HERE = Path(__file__).resolve().parent
DEFAULT_CACHE = HERE.parents[1] / '.data/gse350289-download-recovery-2026-11-01/admitted-workbook'
MAX_EXPANDED = 128 * 1024 * 1024


def read(path):
    return json.loads(path.read_text())


def encode(value):
    return json.JSONEncoder(indent=2, sort_keys=True, allow_nan=False).encode(value) + '\n'


def sha(body):
    return hashlib.sha256(body).hexdigest()


def validate_payload(status, body, kind, expanded_limit=MAX_EXPANDED):
    if status != 200:
        raise ValueError('HTTP status does not admit a complete file: ' + str(status))
    if not body:
        raise ValueError('Empty response body')
    if kind == 'xlsx':
        if not zipfile.is_zipfile(io.BytesIO(body)):
            raise ValueError('Response is not an XLSX ZIP')
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            required = {'[Content_Types].xml', 'xl/workbook.xml', 'xl/_rels/workbook.xml.rels'}
            if not required.issubset(archive.namelist()):
                raise ValueError('ZIP lacks required XLSX parts')
            if sum(item.file_size for item in archive.infolist()) > expanded_limit:
                raise ValueError('Expanded workbook exceeds the bounded budget')
            if any(item.flag_bits & 1 for item in archive.infolist()):
                raise ValueError('Encrypted source is not admitted')
            if archive.testzip() is not None:
                raise ValueError('Workbook ZIP CRC check failed')
        return {'kind': kind, 'required_parts': 'PASS', 'full_CRC': 'PASS'}
    raise ValueError('Unsupported source kind')


def recover(cache):
    plan = read(HERE / 'DOWNLOAD_PLAN.json')
    limits = plan['limits']
    if limits['max_files'] != 1 or set(plan['files']) != {'GSE350289_metadata_individual_cells.xlsx'}:
        raise ValueError('Download plan must retain its exact one-workbook scope')
    cache.mkdir(parents=True, exist_ok=True)
    if any(cache.iterdir()):
        raise ValueError('Use a new empty cache; existing source receipts will not be overwritten')
    if shutil.disk_usage(cache).free < limits['min_free_bytes']:
        raise ValueError('Free-space reserve not met')
    receipt = {'schema': 'controller.GEO-download-recovery/1', 'client': subprocess.check_output(['curl', '--version'], text=True).splitlines()[0], 'started_at_utc': datetime.now(timezone.utc).isoformat(), 'files': {}, 'all_files_acquired': False}
    total = 0
    for name, spec in plan['files'].items():
        if Path(name).name != name or urlparse(spec['url']).hostname != 'www.ncbi.nlm.nih.gov':
            raise ValueError('Unapproved filename or source host')
        target = cache / name
        temporary = cache / (name + '.part')
        started = datetime.now(timezone.utc).isoformat()
        header_path = cache / 'response.headers'
        command = ['curl', '--silent', '--show-error', '--location', '--proto', '=https', '--proto-redir', '=https', '--max-redirs', '3', '--connect-timeout', '10', '--max-time', str(limits['per_request_timeout_seconds']), '--max-filesize', str(limits['max_file_bytes']), '-D', str(header_path), '--output', str(temporary), '--write-out', '%{http_code}\n%{content_type}\n%{url_effective}\n', spec['url']]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=limits['per_request_timeout_seconds'] + 5)
        except subprocess.TimeoutExpired:
            result = subprocess.CompletedProcess(command, 124, stdout='', stderr='Bounded process timeout')
        response = result.stdout.splitlines()
        body = temporary.read_bytes() if temporary.exists() else b''
        record = {'requested_url': spec['url'], 'started_at_utc': started, 'received_at_utc': datetime.now(timezone.utc).isoformat(), 'curl_exit': result.returncode, 'curl_error': result.stderr.strip(), 'bytes': len(body), 'sha256': sha(body), 'accepted': False}
        try:
            if len(response) == 3:
                record.update(http_status=int(response[0]), content_type=response[1], effective_url=response[2])
            if result.returncode != 0 or len(response) != 3:
                raise ValueError('Incomplete curl transfer')
            if urlparse(record['effective_url']).hostname not in {'www.ncbi.nlm.nih.gov', 'ftp.ncbi.nlm.nih.gov'}:
                raise ValueError('Unexpected final host')
            total += len(body)
            if len(body) > limits['max_file_bytes'] or total > limits['max_total_bytes']:
                raise ValueError('Download byte budget exceeded')
            record['format_validation'] = validate_payload(record['http_status'], body, spec['format'], limits['max_expanded_file_bytes'])
            record['byte_identical_to_October_17'] = record['sha256'] == spec['baseline_sha256'] and len(body) == spec['baseline_bytes']
            record['accepted'] = True
            temporary.rename(target)
        except (ValueError, OSError, EOFError, zipfile.BadZipFile) as exc:
            record['error'] = str(exc)
        receipt['files'][name] = record
        (cache / 'ACQUISITION.json').write_text(encode(receipt))
        print(name, 'ACCEPTED' if record['accepted'] else 'REJECTED', record['bytes'], flush=True)
        if not record['accepted']:
            raise ValueError('Source not admitted; preserve this receipt and use a new cache for a deliberate retry')
        time.sleep(0.4)
    receipt['all_files_acquired'] = True
    receipt['completed_at_utc'] = datetime.now(timezone.utc).isoformat()
    receipt['total_source_bytes'] = total
    (cache / 'ACQUISITION.json').write_text(encode(receipt))
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=DEFAULT_CACHE)
    args = parser.parse_args()
    result = recover(args.cache)
    print('PASS bounded workbook download:', result['total_source_bytes'], 'bytes; source assignments still require content review.')

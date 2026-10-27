#!/usr/bin/env python3
"""Push a clean research checkpoint and publish an explicitly reviewed file set.

Configuration stays local. Public exports contain committed allowlisted files,
replay tests and provenance, never an automatic mirror of the source repository.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys


CONTROLLER = 'programs/partial-reprogramming-controller'
PACKAGE = 'research/2026-10-rpe-controller'
V2 = CONTROLLER + '/benchmarks/rpe-uncertainty-controller-v2-2026-10-26'


def run(args, cwd, capture=True):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=capture)
    if result.returncode:
        raise RuntimeError('Command failed: ' + ' '.join(args) + '\n' + (result.stderr or result.stdout or ''))
    return result.stdout.strip() if capture else ''


def encode(value):
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(value):
    path = PurePosixPath(value)
    if not value or path.is_absolute() or '..' in path.parts or str(path) != value or '\\' in value:
        raise ValueError('Unsafe relative path: ' + value)
    if any(part in {'.git', '.data', 'correspondence', 'cloud', 'tmp'} for part in path.parts):
        raise ValueError('Private or temporary source path: ' + value)
    return value


def require_clean(root):
    if run(['git', 'status', '--porcelain'], root):
        raise RuntimeError('Worktree has uncommitted changes; preserve and checkpoint them first.')


def origin(root):
    value = run(['git', 'remote', 'get-url', 'origin'], root)
    if value.startswith('git@github.com:'):
        value = 'https://github.com/' + value.split(':', 1)[1]
    return value.removesuffix('.git').rstrip('/')


def check_repo(root, name, private, branch):
    if origin(root) != 'https://github.com/' + name:
        raise RuntimeError('Origin differs from the explicitly configured repository.')
    if run(['git', 'branch', '--show-current'], root) != branch:
        raise RuntimeError('Branch is outside this checkpoint configuration.')
    record = json.loads(run(['gh', 'repo', 'view', name, '--json', 'isPrivate'], root))
    if record['isPrivate'] is not private:
        raise RuntimeError('Repository visibility differs from the approved configuration.')
    require_clean(root)


def remote_head(root, branch):
    result = run(['git', 'ls-remote', '--heads', 'origin', 'refs/heads/' + branch], root)
    return result.split()[0] if result else None


def push_checkpoint(root, branch):
    head = run(['git', 'rev-parse', 'HEAD'], root)
    if remote_head(root, branch) != head:
        run(['git', 'push', 'origin', 'HEAD:refs/heads/' + branch], root, capture=False)
    if remote_head(root, branch) != head:
        raise RuntimeError('Remote checkpoint read-back differs from local HEAD.')
    return head


def committed(root, head, path):
    safe_path(path)
    result = subprocess.run(['git', 'show', head + ':' + path], cwd=root, capture_output=True)
    if result.returncode:
        raise RuntimeError('Allowlisted file is not committed: ' + path)
    return result.stdout


def content_id(files):
    return digest(encode({name: digest(data) for name, data in sorted(files.items())}).encode())


def build_inputs(root, head, config):
    manifest_path = config['export_manifest']
    manifest = json.loads(committed(root, head, manifest_path))
    files = {}
    for destination, source in manifest['files'].items():
        safe_path(destination)
        files[destination] = committed(root, head, source)
    return manifest, files


def require_owned_outputs(public, previous, initial_commit, managed):
    if previous is None:
        if run(['git', 'rev-parse', 'HEAD'], public) != initial_commit:
            raise RuntimeError('First public export requires the reviewed starting commit.')
    else:
        for name, expected in previous['files'].items():
            path = public / safe_path(name)
            if not path.is_file() or digest(path.read_bytes()) != expected:
                raise RuntimeError('An owned public file was independently changed: ' + name)
        removed = set(previous['files']) - set(managed)
        if removed:
            raise RuntimeError('Review removed public paths explicitly: ' + ', '.join(sorted(removed)))


def prepare(root, head, config, publish):
    public = (root / config['public_checkout']).resolve()
    check_repo(public, config['public_repository'], False, config['public_branch'])
    if remote_head(public, config['public_branch']) != run(['git', 'rev-parse', 'HEAD'], public):
        raise RuntimeError('Public checkout and origin differ; reconcile without automatic merging.')
    manifest, files = build_inputs(root, head, config)
    fingerprint = content_id(files)
    package_path = public / PACKAGE / 'public-package.json'
    previous = json.loads(package_path.read_text()) if package_path.exists() else None
    if previous and previous['content_fingerprint'] == fingerprint:
        require_owned_outputs(public, previous, config['initial_public_commit'], previous['files'])
        return {'status': 'unchanged', 'content_fingerprint': fingerprint,
                'public_commit': run(['git', 'rev-parse', 'HEAD'], public)}

    run([sys.executable, CONTROLLER + '/scripts/controller_checkpoint_integrity_pass.py',
         '--emit', str(root / CONTROLLER / 'tmp/research-sync/checkpoint-integrity.json')], root, capture=False)

    # These are public administrative ledgers. Original source schemas, tables,
    # executable code and golden outputs below are copied byte-for-byte.
    source_freeze = json.loads(files[V2 + '/FREEZE.json'])
    original_freeze_sha = digest(files[V2 + '/FREEZE.json'])
    source_freeze['inputs'] = {name: sha for name, sha in source_freeze['inputs'].items()
                               if V2 + '/' + name in files and name != 'FREEZE.json'}
    source_freeze['export_note'] = ('Excerpt of the historical source freeze, exported after execution. '
                                   'This is not a new prospective or held-out public benchmark.')
    source_freeze['original_full_freeze_sha256'] = original_freeze_sha
    files[V2 + '/FREEZE.json'] = encode(source_freeze).encode()
    original_baseline = json.loads(committed(root, head, manifest['source_baseline']))
    protection = {name: sha for name, sha in original_baseline['protected_files'].items()
                  if name in files and digest(files[name]) == sha
                  and name not in original_baseline['allowed_later_changes']}
    if not protection:
        raise RuntimeError('Public protection ledger would be empty.')
    files[V2 + '/BASELINE.json'] = encode({
        'head': original_baseline['head'], 'protected_files': protection,
        'allowed_later_changes': [],
        'export_note': 'Derived public subset of protected source artifacts; private administrative history is omitted.'}).encode()
    verification_name = V2 + '/VERIFICATION.json'
    managed = set(files) | {verification_name}
    require_owned_outputs(public, previous, config['initial_public_commit'], managed)

    receipt = root / config['receipt_path']
    receipt.parent.mkdir(parents=True, exist_ok=True)
    owned = sorted(managed | {PACKAGE + '/public-package.json', 'research-release.json', 'research-release-checks.json'})
    receipt.write_text(encode({'status': 'preparing_public', 'source_commit': head,
                               'owned_public_paths': owned, 'next_action': 'Inspect these paths and rerun checks before a scoped commit.'}))
    for name, data in files.items():
        destination = public / safe_path(name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    run([sys.executable, str(public / V2 / 'verify.py')], public, capture=False)
    files[verification_name] = (public / verification_name).read_bytes()
    metadata = {'schema': 'public.research-checkpoint/1', 'claim_level': 'Verified',
                'source_commit': head, 'scientific_checkpoint': manifest['scientific_checkpoint'],
                'content_fingerprint': fingerprint,
                'scope': 'Committed allowlist export, exact CLI replay and same-agent source-table verification; biological interpretation remains Heuristic.',
                'files': {name: digest(data) for name, data in sorted(files.items())},
                'excluded': ['private correspondence', 'author-only attachments', 'credentials', 'model weights', 'raw biological objects']}
    package_path.write_text(encode(metadata))
    outer_path = public / 'research-release.json'
    outer = json.loads(outer_path.read_text())
    outer['date'] = manifest['scientific_checkpoint']
    outer['current_checkpoint'] = PACKAGE + '/public-package.json'
    for name in sorted(set(files) | {PACKAGE + '/public-package.json'}):
        outer['files'][name] = digest((public / name).read_bytes())
    outer_path.write_text(encode(outer))
    run([sys.executable, str(public / PACKAGE / 'verify_public.py')], public, capture=False)
    run([sys.executable, 'research/2026-10-public-data/release_check.py', '--write'], public, capture=False)
    run(['git', 'diff', '--check'], public)
    changed = set(run(['git', 'ls-files', '--modified'], public).splitlines()) | set(run(['git', 'ls-files', '--others', '--exclude-standard'], public).splitlines())
    if not changed <= set(owned):
        raise RuntimeError('Unexpected public dirt; preserve and classify: ' + ', '.join(sorted(changed - set(owned))))
    result = {'status': 'prepared', 'source_commit': head, 'content_fingerprint': fingerprint,
              'owned_public_paths': owned, 'local_verification': 'PASS', 'hosted_ci': 'pending',
              'next_action': 'Commit the audited paths and push, then verify hosted CI and anonymous bytes.'}
    receipt.write_text(encode(result))
    if publish:
        run(['git', 'add', '--', *sorted(changed)], public)
        run(['git', 'commit', '-m', 'Publish RPE controller source replay and evidence limits'], public, capture=False)
        result['public_commit'] = push_checkpoint(public, config['public_branch'])
        result.update(status='published', next_action='Verify hosted CI and anonymous public read-back.')
        require_clean(public)
        receipt.write_text(encode(result))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--config', type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--checkpoint', action='store_true', help='Push the clean configured branch; export only if enabled.')
    mode.add_argument('--prepare-public', action='store_true', help='Prepare and verify an uncommitted public update.')
    mode.add_argument('--publish-public', action='store_true', help='Verify, commit and push the curated public update.')
    args = parser.parse_args()
    root = Path(run(['git', 'rev-parse', '--show-toplevel'], args.root))
    config_path = args.config or root / CONTROLLER / 'ops/research-sync/config.json'
    config = json.loads(config_path.read_text())
    receipt = root / config['receipt_path']
    try:
        check_repo(root, config['private_repository'], True, config['private_branch'])
        hygiene = json.loads(run(['orp', 'hygiene', '--json'], root))
        if not hygiene['safe_to_expand'] or hygiene['unclassified_count']:
            raise RuntimeError('ORP hygiene has an unclassified blocker.')
        head = run(['git', 'rev-parse', 'HEAD'], root)
        result = {'status': 'private_checkpoint_synced', 'source_commit': head}
        if args.checkpoint:
            push_checkpoint(root, config['private_branch'])
        elif remote_head(root, config['private_branch']) != head:
            raise RuntimeError('Source must be pushed before public export.')
        if not args.checkpoint or config['public_auto_export_enabled']:
            result['public'] = prepare(root, head, config, publish=not args.prepare_public)
        result['updated_at_utc'] = datetime.now(timezone.utc).isoformat()
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(encode(result))
        print(encode(result))
    except Exception as error:
        prior = json.loads(receipt.read_text()) if receipt.exists() else {}
        prior.update(status='blocked', error=str(error), updated_at_utc=datetime.now(timezone.utc).isoformat(),
                     next_action='Preserve existing changes; inspect the recorded cause and owned paths, then resume explicitly.')
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(encode(prior))
        print('Research checkpoint sync blocked: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

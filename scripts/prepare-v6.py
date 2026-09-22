#!/usr/bin/env python3
"""Prepare the published v6 launch stack in an existing, dedicated BF workspace.

No dependency download, game launch, save edit, or global Wine change.
"""
from pathlib import Path
import argparse
import datetime
import fcntl
import hashlib
import json
import os
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'platform/packages/black-flag/experiments/v6-performance'
PREFIX = ROOT / 'platform/environments/black-flag-resynced'
ENGINE = ROOT / 'platform/engines/wineforge-0.6.0.4'
GAMEPOLICY_CTL = Path('/Applications/Xcode.app/Contents/Developer/usr/bin/gamepolicyctl')
sys.path.insert(0, str(ROOT / 'GornHub/Runtime'))
import session


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked(path, expected):
    if not path.is_file() or sha(path) != expected:
        raise RuntimeError('Missing or mismatched dependency: ' + str(path))


def atomic_copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(dst.name + '.v6-tmp')
    try:
        shutil.copy2(src, tmp)
        if sha(tmp) != sha(src):
            raise RuntimeError('Copy verification failed: ' + str(dst))
        os.replace(tmp, dst)
    finally:
        tmp.unlink(missing_ok=True)


def transaction(pairs, history):
    """Back up every destination before any replacement; roll back on failure."""
    for src, dst in pairs:
        if not src.is_file() or dst.is_symlink() or (dst.exists() and not dst.is_file()):
            raise RuntimeError('Invalid source or destination: ' + str(dst))
    history.mkdir(parents=True)
    entries = []
    for i, (src, dst) in enumerate(pairs):
        entry = {'destination': str(dst.relative_to(ROOT)), 'existed': dst.exists(),
                 'installed_sha256': sha(src), 'backup': str(i)}
        if dst.exists():
            shutil.copy2(dst, history / str(i))
            entry['previous_sha256'] = sha(dst)
            checked(history / str(i), entry['previous_sha256'])
        entries.append(entry)
    record = {'status': 'prepared', 'files': entries}
    (history / 'transaction.json').write_text(json.dumps(record, indent=2))
    done = []
    try:
        for i, (src, dst) in enumerate(pairs):
            done.append(i)
            atomic_copy(src, dst)
        record['status'] = 'installed'
    except Exception:
        for i in reversed(done):
            dst = pairs[i][1]
            if entries[i]['existed']:
                atomic_copy(history / str(i), dst)
            else:
                dst.unlink(missing_ok=True)
        record['status'] = 'rolled-back'
        raise
    finally:
        (history / 'transaction.json').write_text(json.dumps(record, indent=2))


def ensure_idle():
    # Refuse all live processes in this prefix, not just the main EXE.
    if session.snapshot(PREFIX):
        raise RuntimeError('Close Black Flag and its prefix-owned processes first.')


def prepare(renderer, settings):
    deps = json.loads((BASE / 'dependencies.json').read_text())
    pkg = ROOT / 'platform/packages/black-flag/compatibility/v6'
    module = json.loads((pkg / 'manifest.json').read_text())
    checked(pkg / 'BlackFlagCompatibility.dylib', module['module_sha256'])
    for name, digest in module['source_hashes'].items():
        checked(pkg / name, digest)
    renderer = renderer.resolve()
    for name, digest in deps['renderer_files'].items():
        checked(renderer / name, digest)
    version = ENGINE / 'lib/wine/x86_64-windows/version.dll'
    checked(version, deps['wine_version_dll_sha256'])
    proxy = BASE / 'framegen-hws/version-hws.dll'
    checked(proxy, deps['proxy_sha256'])
    game = PREFIX / 'drive_c/Games/BlackFlagResynced'
    for p in [ENGINE / 'bin/wine', ENGINE / 'bin/wineserver', game / 'ACBlackFlag.exe',
              GAMEPOLICY_CTL]:
        if not p.is_file():
            raise RuntimeError('Required existing setup is missing: ' + str(p))
    # Prefix creation and user selection are deliberately not guessed.
    ini = list((PREFIX / 'drive_c/users').glob('*/Documents/Assassin*/ACBlackFlag.ini'))
    if settings and len(ini) != 1:
        raise RuntimeError('Expected exactly one existing Black Flag INI.')
    if settings:
        captured = ROOT / 'settings/2026-09-19'
        checked(captured / 'ACBlackFlag.ini', json.loads((captured / 'snapshot.json').read_text())['sha256'])
    target = BASE / 'd3dmetal'
    if target.exists():
        for name, digest in deps['renderer_files'].items():
            checked(target / name, digest)
    else:
        # Copy only to BF's isolated path; never replace the shared engine renderer.
        stage = BASE / 'd3dmetal.v6-tmp'
        if stage.exists():
            raise RuntimeError('Remove or inspect leftover renderer staging directory: ' + str(stage))
        try:
            shutil.copytree(renderer, stage, symlinks=True)
            for name, digest in deps['renderer_files'].items():
                checked(stage / name, digest)
            stage.rename(target)
        finally:
            if stage.exists():
                shutil.rmtree(stage)
    unix = target / 'wine/x86_64-unix'
    windows = target / 'wine/x86_64-windows'
    unix.mkdir(parents=True, exist_ok=True)
    # Existing aliases must resolve to this exact renderer, not another installation.
    alias = unix / 'nvngx.so'
    expected = target / 'external/libd3dshared.dylib'
    if alias.exists() or alias.is_symlink():
        if alias.resolve() != expected.resolve():
            raise RuntimeError('Unexpected nvngx.so alias: ' + str(alias))
    else:
        alias.symlink_to('../../external/libd3dshared.dylib')
    pairs = [(windows / 'nvngx-on-metalfx.dll', windows / 'nvngx.dll'),
             (windows / 'nvngx-on-metalfx.dll', PREFIX / 'drive_c/windows/system32/nvngx.dll'),
             (windows / 'nvapi64.dll', PREFIX / 'drive_c/windows/system32/nvapi64.dll'),
             (proxy, game / 'version.dll'), (version, game / 'version_orig.dll')]
    if settings:
        pairs.append((ROOT / 'settings/2026-09-19/ACBlackFlag.ini', ini[0]))
    history = BASE / 'install-history' / datetime.datetime.now().strftime('%Y%m%dT%H%M%S%f')
    transaction(pairs, history)
    print('v6 prepared; previous files saved at ' + str(history))
    print('No game launched. Check Ray Tracing in the game menu; saves were not copied.')


def restore(history):
    history = history.resolve()
    history.relative_to((BASE / 'install-history').resolve())
    record = json.loads((history / 'transaction.json').read_text())
    if record['status'] != 'installed':
        raise RuntimeError('Only an installed transaction can be restored.')
    for entry in record['files']:
        dest = ROOT / entry['destination']
        dest.resolve().relative_to(ROOT.resolve())
        checked(dest, entry['installed_sha256'])
        if entry['existed']:
            checked(history / entry['backup'], entry['previous_sha256'])
    for entry in reversed(record['files']):
        dest = ROOT / entry['destination']
        if entry['existed']:
            atomic_copy(history / entry['backup'], dest)
        else:
            dest.unlink()
    record['status'] = 'restored'
    (history / 'transaction.json').write_text(json.dumps(record, indent=2))
    print('Prepared files restored. Isolated renderer retained. Restore your previous launcher to use v4.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--renderer', type=Path, help='Existing D3DMetal 4.0b2 folder containing external/ and wine/')
    group.add_argument('--restore', type=Path, help='Installation history directory to revert')
    parser.add_argument('--keep-settings', action='store_true', help='Do not apply the published complete INI')
    args = parser.parse_args()
    state = ROOT / 'platform/packages/black-flag/launch-state'
    state.mkdir(parents=True, exist_ok=True)
    with (state / 'launch.lock').open('a') as launch_lock, (BASE / 'session.lock').open('a') as game_lock:
        for lock in (launch_lock, game_lock):
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ensure_idle()
        if args.restore:
            restore(args.restore)
        else:
            prepare(args.renderer, not args.keep_settings)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

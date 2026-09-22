"""Detached Black Flag launcher; uses its own prefix and pinned compatibility module."""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import time
import black_flag_runtime as runtime

PACKAGE = runtime.ROOT / 'packages/black-flag/compatibility/v6'
GAME = runtime.PREFIX / 'drive_c/Games/BlackFlagResynced'
STATE = runtime.ROOT / 'packages/black-flag/launch-state'
METAL = runtime.ROOT / 'packages/black-flag/experiments/v6-performance/d3dmetal/external/D3DMetal.framework/Versions/A/D3DMetal'
MODULE = PACKAGE / 'BlackFlagCompatibility.dylib'
sys.path.insert(0, str(runtime.ROOT.parent / 'GornHub/Runtime'))
import session


def check():
    base = runtime.ROOT / 'packages/black-flag/experiments/v6-performance'
    renderer = base / 'd3dmetal'
    required = [GAME / 'ACBlackFlag.exe', runtime.ENGINE / 'bin/wine',
                runtime.ENGINE / 'bin/wineserver', MODULE, PACKAGE / 'manifest.json',
                base / 'dependencies.json', base / 'supervisor.py',
                Path('/Applications/Xcode.app/Contents/Developer/usr/bin/gamepolicyctl')]
    if not all(p.is_file() for p in required):
        return {'ready': False, 'reason': 'Missing v6 setup files; follow docs/INSTALLATION.md.'}
    manifest = json.loads((PACKAGE / 'manifest.json').read_text())
    deps = json.loads((base / 'dependencies.json').read_text())
    checks = {MODULE: manifest['module_sha256'], METAL: manifest['d3dmetal_sha256']}
    checks.update({renderer / name: digest for name, digest in deps['renderer_files'].items()})
    checks.update({GAME / 'version.dll': deps['proxy_sha256'],
                   GAME / 'version_orig.dll': deps['wine_version_dll_sha256']})
    for name, source in [('nvngx.dll', 'nvngx-on-metalfx.dll'), ('nvapi64.dll', 'nvapi64.dll')]:
        digest = deps['renderer_files']['wine/x86_64-windows/' + source]
        checks[runtime.PREFIX / 'drive_c/windows/system32' / name] = digest
        checks[renderer / 'wine/x86_64-windows' / name] = digest
    if any(not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest
           for path, digest in checks.items()):
        return {'ready': False, 'reason': 'v6 dependency mismatch; run scripts/prepare-v6.py with the pinned renderer.'}
    if (renderer / 'wine/x86_64-unix/nvngx.so').resolve() != (renderer / 'external/libd3dshared.dylib').resolve():
        return {'ready': False, 'reason': 'The MetalFX Unix bridge alias is missing or incorrect.'}
    return {'ready': True}


def launch():
    ready = check()
    if not ready['ready']:
        return ready, 1
    STATE.mkdir(parents=True, exist_ok=True)
    with (STATE / 'launch.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        current = session.snapshot(runtime.PREFIX)
        if any(p['path'].replace('\\\\', '\\').lower() == r'c:\games\blackflagresynced\acblackflag.exe' for p in current):
            return {'reason': 'Black Flag zaten açık.'}, 1
        record = STATE / 'last-launch.json'
        if record.exists() and time.time() - record.stat().st_mtime < 15:
            return {'reason': 'Black Flag başlatılıyor; biraz bekle.'}, 1
        env = runtime.environment()
        for key in list(env):
            if key.startswith(('MTL_', 'BF_')):
                env.pop(key)
        # The Python supervisor is native; inject the x86_64 module only into Wine.
        env.pop('DYLD_INSERT_LIBRARIES', None)
        logpath = STATE / 'game.log'
        if logpath.exists():
            logpath.replace(STATE / 'game.previous.log')
        with logpath.open('w') as log:
            proc = subprocess.Popen([sys.executable, str(runtime.ROOT / 'packages/black-flag/experiments/v6-performance/supervisor.py'), str(MODULE), str(runtime.ENGINE / 'bin/wine'), r'C:\Games\BlackFlagResynced\ACBlackFlag.exe'],
                                    cwd=GAME, env=env, stdin=subprocess.DEVNULL, stdout=log,
                                    stderr=subprocess.STDOUT, start_new_session=True)
        record.write_text(json.dumps({'pid': proc.pid, 'time': time.time(), 'module': str(MODULE)}))
        return {'stage': 'launch_requested', 'pid': proc.pid}, 0


if __name__ == '__main__':
    try:
        if '--check' in sys.argv:
            result = check()
            status = 0 if result['ready'] else 1
        else:
            result, status = launch()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        result, status = {'ready': False, 'reason': 'Black Flag başlatılamadı veya süreç kontrolü yapılamadı.'}, 1
        print(str(exc), file=sys.stderr)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(status)

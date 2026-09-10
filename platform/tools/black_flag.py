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

PACKAGE = runtime.ROOT / 'packages/black-flag/compatibility/v4'
GAME = runtime.PREFIX / 'drive_c/Games/BlackFlagResynced'
STATE = runtime.ROOT / 'packages/black-flag/launch-state'
METAL = runtime.ROOT / 'packages/black-flag/d3dmetal-4.0b2/external/D3DMetal.framework/Versions/A/D3DMetal'
MODULE = PACKAGE / 'BlackFlagCompatibility.dylib'
sys.path.insert(0, str(runtime.ROOT.parent / 'GornHub/Runtime'))
import session


def check():
    required = [GAME / 'ACBlackFlag.exe', runtime.ENGINE / 'bin/wine', MODULE, METAL, PACKAGE / 'manifest.json']
    if not all(p.is_file() for p in required):
        return {'ready': False, 'reason': 'Black Flag kurulum dosyalarından biri bulunamadı.'}
    manifest = json.loads((PACKAGE / 'manifest.json').read_text())
    for path, name in [(MODULE, 'module_sha256'), (METAL, 'd3dmetal_sha256')]:
        if hashlib.sha256(path.read_bytes()).hexdigest() != manifest[name]:
            return {'ready': False, 'reason': 'Black Flag çalışma sürümü değişmiş; uyumluluk kontrolü gerekiyor.'}
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
        env['DYLD_INSERT_LIBRARIES'] = str(MODULE)
        logpath = STATE / 'game.log'
        if logpath.exists():
            logpath.replace(STATE / 'game.previous.log')
        with logpath.open('w') as log:
            proc = subprocess.Popen([str(runtime.ENGINE / 'bin/wine'), r'C:\Games\BlackFlagResynced\ACBlackFlag.exe'],
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

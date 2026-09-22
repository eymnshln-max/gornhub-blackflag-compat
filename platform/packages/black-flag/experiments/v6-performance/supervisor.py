"""Game-scoped Game Mode lease. This file is invoked only by an explicit game launch."""
from pathlib import Path
import fcntl
import json
import os
import re
import signal
import subprocess
import sys
import time

BASE = Path(__file__).resolve().parent
PLATFORM = BASE.parents[3]
CTL = '/Applications/Xcode.app/Contents/Developer/usr/bin/gamepolicyctl'
sys.path.insert(0, str(PLATFORM.parent / 'GornHub/Runtime'))
import session


def policy():
    text = subprocess.check_output([CTL, 'game-mode', 'status'], text=True, timeout=10)
    text = re.sub(r'\x1b\[[0-9;]*m', '', text)
    if 'forced always on' in text:
        return 'on'
    if 'automatic' in text:
        return 'auto'
    if 'forced always off' in text:
        return 'off'
    raise RuntimeError('Unrecognized Game Mode policy; refusing to overwrite it: ' + text)


def set_policy(value):
    subprocess.run([CTL, 'game-mode', 'set', value], check=True, timeout=10)


def main():
    module, wine, game = sys.argv[1:]
    with (BASE / 'session.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        journal = BASE / 'game-mode-lease.json'
        if journal.exists():
            # Recover a lease left by a killed supervisor before taking another.
            set_policy(json.loads(journal.read_text())['previous'])
            journal.unlink()
        previous = policy()
        journal.write_text(json.dumps({'previous': previous, 'supervisor': os.getpid()}))
        child = None
        def stop(signum, frame):
            if child is not None and child.poll() is None:
                child.send_signal(signum)
            raise SystemExit(128 + signum)
        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        try:
            set_policy('on')
            print(subprocess.check_output([CTL, 'game-mode', 'status'], text=True, timeout=10), flush=True)
            env = os.environ.copy()
            env['DYLD_INSERT_LIBRARIES'] = module
            env['BF_HWS_LOG'] = r'C:\Games\BlackFlagResynced\framegen-hws.log'
            print('Black Flag experimental v6: Game Mode, MetalFX and frame-generation compatibility enabled.', flush=True)
            child = subprocess.Popen([wine, game], env=env)
            result = child.wait()
            # Handle Wine handing off to another game PID; never scan/stop other prefixes.
            empty = 0
            while empty < 2:
                try:
                    running = any(p['path'].lower().endswith('acblackflag.exe')
                                  for p in session.snapshot(Path(env['WINEPREFIX'])))
                    empty = 0 if running else empty + 1
                except (OSError, RuntimeError, subprocess.SubprocessError):
                    empty = 0
                if empty < 2:
                    time.sleep(2)
            return result
        finally:
            set_policy(previous)
            journal.unlink(missing_ok=True)


if __name__ == '__main__':
    sys.exit(main())

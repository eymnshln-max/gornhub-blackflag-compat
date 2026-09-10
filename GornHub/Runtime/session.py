"""Per-environment launch ownership and cleanup; independent of the hub window.

No global process-name kills, Wine-server shutdown, or credentials in state files.
The cwd backend is for tested Wine profiles; unknown processes prevent cleanup.
"""
from pathlib import Path
import fcntl
import hashlib
import json
import ntpath
import os
import signal
import subprocess
import sys
import time
import uuid

STATE = Path.home() / 'Library/Application Support/GornHub/Sessions'
INFRASTRUCTURE = {'services.exe', 'winedevice.exe', 'explorer.exe', 'rpcss.exe',
                  'svchost.exe', 'plugplay.exe', 'conhost.exe', 'wineboot.exe', 'lsass.exe'}


def snapshot(root):
    result = subprocess.run(['/bin/ps', '-axo', 'pid=,lstart=,comm='],
                            capture_output=True, text=True, check=True, timeout=5)
    candidates = []
    for line in result.stdout.splitlines():
        fields = line.strip().split(None, 6)
        if len(fields) == 7 and (fields[6].lower().startswith('c:\\') or (fields[6].lower().endswith('.exe') and '/' not in fields[6] and '\\' not in fields[6])):
            candidates.append({'pid': int(fields[0]), 'born': ' '.join(fields[1:6]),
                               'path': fields[6].lower()})
    if not candidates:
        return []
    result = subprocess.run(['/usr/sbin/lsof', '-a', '-p',
                             ','.join(str(p['pid']) for p in candidates), '-d', 'cwd', '-Fn'],
                            capture_output=True, text=True, timeout=8)
    if result.returncode not in (0, 1):
        raise RuntimeError('Process scope unavailable')
    directories = {}
    pid = None
    for line in result.stdout.splitlines():
        if line.startswith('p'):
            pid = int(line[1:])
        elif line.startswith('n') and pid is not None:
            directories[pid] = line[1:]
    # A process may disappear between ps and lsof. Never infer game exit from
    # an incomplete scope scan; the next observation retries normally.
    if any(p['pid'] not in directories for p in candidates):
        raise RuntimeError('Incomplete process scope')
    root = str(Path(root).resolve()).rstrip('/')
    scoped = []
    drive_c = Path(root) / 'drive_c'
    for p in candidates:
        cwd = str(Path(directories[p['pid']]).resolve())
        if cwd != root and not cwd.startswith(root + '/'):
            continue
        if not p['path'].startswith('c:\\'):
            # Wine can re-exec the game with only a basename. Require its cwd
            # to resolve inside this prefix's C drive and the named file to exist.
            try:
                relative = Path(cwd).resolve().relative_to(drive_c.resolve())
            except ValueError:
                continue
            if not any(f.name.lower() == p['path'] and f.is_file() for f in Path(cwd).iterdir()):
                continue
            p = dict(p, path=ntpath.join('c:\\', *relative.parts, p['path']).lower())
        scoped.append(p)
    return scoped


def identity(p):
    return p['pid'], p['born'], p['path']


def scope_key(root):
    return hashlib.sha256(str(Path(root).resolve()).encode()).hexdigest()[:20]


def active_session(root):
    """A saved JSON record alone never proves a session is still alive."""
    try:
        fd = os.open(str(STATE / (scope_key(root) + '.lock')), os.O_RDWR)
    except FileNotFoundError:
        return None
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return None
        except BlockingIOError:
            pass
        for path in sorted(STATE.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True):
            record = json.loads(path.read_text())
            candidate = record.get('profile', {}).get('lifecycle', {}).get('processRoot')
            if candidate and Path(candidate).resolve() == Path(root).resolve():
                return record
        return {}  # Locked, but startup has not published a record yet.
    finally:
        os.close(fd)


def classify(profile, current, active):
    config = profile['lifecycle']
    if any(is_game(p, config) for p in current):
        return 'running'
    if active is None:
        return 'idle'
    if active.get('profile', {}).get('id') != profile.get('id'):
        return 'busy'
    return 'starting' if active.get('stage') == 'launch_requested' else 'closing'


def statuses(profiles):
    """One process observation per environment, including games opened elsewhere."""
    environments, states = {}, {}
    for profile in profiles:
        config = profile.get('lifecycle')
        if not config:
            states[profile['id']] = 'unsupported'
            continue
        root = config['processRoot']
        if root not in environments:
            try:
                environments[root] = (snapshot(root), active_session(root))
            except (OSError, RuntimeError, ValueError, subprocess.SubprocessError):
                environments[root] = None
        observation = environments[root]
        states[profile['id']] = classify(profile, *observation) if observation is not None else 'unknown'
    return {'states': states}


def stop(profile):
    """User-requested stop of this exact game only; cleanup watcher stays alive."""
    config = profile['lifecycle']
    targets = [p for p in snapshot(config['processRoot']) if is_game(p, config)]
    signalled = []
    for target in targets:
        latest = snapshot(config['processRoot'])
        if identity(target) not in {identity(p) for p in latest if is_game(p, config)}:
            continue
        try:
            os.kill(target['pid'], signal.SIGTERM)
            signalled.append(target['pid'])
        except ProcessLookupError:
            pass
    return {'stage': 'stop_requested', 'signalled_count': len(signalled)}, 0


def is_game(p, config):
    return p['path'] in [s.lower() for s in config['gameProcesses']]


def group(p, config):
    for item in config['companions']:
        if any(p['path'] == s.lower() for s in item['processes']):
            return item['id']
    return None


def cleanup_candidates(current, baseline, config):
    protected = {group(p, config) for p in baseline}
    previous = {identity(p) for p in baseline}
    # Another game/tool in this shared environment makes ownership uncertain.
    if any(is_game(p, config) or (not group(p, config)
            and ntpath.basename(p['path']) not in INFRASTRUCTURE) for p in current):
        return []
    return [p for p in current if group(p, config) not in protected
            and group(p, config) is not None and identity(p) not in previous]


def write_state(path, record):
    temp = path.with_suffix('.tmp')
    with temp.open('w') as stream:
        os.chmod(temp, 0o600)
        json.dump(record, stream, ensure_ascii=False, indent=2)
    temp.replace(path)


def invoke(command, timeout=15):
    return subprocess.run([command['executable'], *command['arguments']],
                          stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, timeout=timeout)


def cleanup(record, path):
    config, baseline = record['profile']['lifecycle'], record['baseline']
    observed = {identity(p) for p in record.get('owned', [])}
    def eligible(current):
        return [p for p in cleanup_candidates(current, baseline, config) if identity(p) in observed]
    # Give launchers their graceful shutdown command first (e.g. Steam sync).
    for companion in config['companions']:
        current = snapshot(config['processRoot'])
        owned = eligible(current)
        if companion.get('shutdown') and any(group(p, config) == companion['id'] for p in owned):
            try:
                invoke(companion['shutdown'])
            except (OSError, subprocess.TimeoutExpired):
                pass
    time.sleep(config.get('shutdownGraceSeconds', 30))
    current = snapshot(config['processRoot'])
    targets = eligible(current)
    closed = []
    for target in targets:
        # Recheck game/other-app absence and PID birth identity before EACH signal.
        latest = eligible(snapshot(config['processRoot']))
        if identity(target) not in {identity(p) for p in latest}:
            continue
        try:
            os.kill(target['pid'], signal.SIGTERM)
            closed.append(target['pid'])
        except ProcessLookupError:
            pass
    time.sleep(2)
    remaining = eligible(snapshot(config['processRoot']))
    record.update(stage='cleanup_requested', signalled=closed,
                  remaining_owned=[p['pid'] for p in remaining])
    write_state(path, record)


def watch(path, lock_fd):
    # The inherited descriptor holds the environment lock after --start exits.
    record = json.loads(path.read_text())
    config = record['profile']['lifecycle']
    deadline = time.monotonic() + config.get('startupTimeoutSeconds', 1200)
    seen = False
    absent_since = None
    failures = 0
    owned = {}
    protected = {group(p, config) for p in record['baseline']}
    try:
        while True:
            try:
                current = snapshot(config['processRoot'])
                failures = 0
            except (OSError, RuntimeError, subprocess.SubprocessError):
                failures += 1
                absent_since = None
                if failures >= 10:
                    record['stage'] = 'observation_failed_no_cleanup'
                    break
                time.sleep(3)
                continue
            now = time.monotonic()
            game_running = any(is_game(p, config) for p in current)
            # Freeze ownership at game exit; a manually reopened launcher during
            # the grace period is not this session's process to terminate.
            if not seen or game_running:
                for p in current:
                    if group(p, config) is not None and group(p, config) not in protected:
                        owned[identity(p)] = p
                record['owned'] = list(owned.values())
            if game_running:
                if not seen:
                    record['stage'] = 'game_observed'
                    write_state(path, record)
                seen = True
                absent_since = None
            elif seen:
                absent_since = absent_since or now
                if now - absent_since >= config.get('exitGraceSeconds', 30):
                    cleanup(record, path)
                    return
            elif now >= deadline:
                record['stage'] = 'startup_expired_no_cleanup'
                break
            time.sleep(3)
    except Exception:
        record['stage'] = 'watch_failed_no_further_cleanup'
    finally:
        write_state(path, record)
        os.close(lock_fd)


def start(profile):
    config = profile['lifecycle']
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    scope = scope_key(config['processRoot'])
    lock = os.open(str(STATE / (scope + '.lock')), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(lock)
        return {'reason': 'Bu oyun ortamında bir oturum zaten açık veya kapanıyor.'}, 1
    try:
        before = snapshot(config['processRoot'])
        if any(is_game(p, config) for p in before):
            return {'reason': 'Oyun zaten açık.'}, 1
        result = invoke(profile['launch'])
        if result.returncode:
            return {'reason': 'Oyun başlatılamadı.'}, 1
        path = STATE / (str(uuid.uuid4()) + '.json')
        record = {'profile': profile, 'baseline': before, 'stage': 'launch_requested'}
        write_state(path, record)
        watcher = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--watch', str(path), str(lock)],
                                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, start_new_session=True, pass_fds=(lock,))
        return {'stage': 'launch_requested', 'cleanup_watcher': watcher.pid}, 0
    finally:
        os.close(lock)


if __name__ == '__main__':
    if sys.argv[1] == '--watch':
        watch(Path(sys.argv[2]), int(sys.argv[3]))
    else:
        try:
            value = json.loads(Path(sys.argv[2]).read_text())
            if sys.argv[1] == '--status':
                result, status = statuses(value), 0
            elif sys.argv[1] == '--stop':
                result, status = stop(value)
            elif sys.argv[1] == '--start':
                result, status = start(value)
            else:
                raise ValueError('Unknown action')
        except Exception:
            result, status = {'reason': 'Oyun oturumu kontrol edilemedi. Tekrar dene.'}, 1
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(status)

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location('session', Path(__file__).resolve().parents[1] / 'Runtime/session.py')
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)

def proc(pid, name, born='first'):
    return {'pid': pid, 'born': born, 'path': 'c:\\apps\\' + name + '.exe'}

GAME, STEAM, ROCKSTAR, OTHER = [proc(i + 1, name) for i, name in enumerate(['game', 'steam', 'rockstar', 'another-game'])]
CONFIG = {'processRoot': '/test', 'gameProcesses': [GAME['path']], 'exitGraceSeconds': 0,
          'shutdownGraceSeconds': 0, 'startupTimeoutSeconds': 0,
          'companions': [{'id': 'steam', 'processes': [STEAM['path']]},
                         {'id': 'rockstar', 'processes': [ROCKSTAR['path']]}]}

class OwnershipTests(unittest.TestCase):
    def test_reexecuted_basename_requires_local_executable_and_scoped_cwd(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'prefix'
            game = root / 'drive_c/Games/BlackFlagResynced'
            game.mkdir(parents=True)
            (game / 'ACBlackFlag.exe').touch()
            outside = Path(folder) / 'outside'
            outside.mkdir()
            (outside / 'ACBlackFlag.exe').touch()
            missing = root / 'drive_c/Missing'
            missing.mkdir()
            link = root / 'drive_c/Escape'
            link.symlink_to(outside, target_is_directory=True)
            ps = SimpleNamespace(stdout='42 Thu Sep 10 02:00:00 2026 ACBlackFlag.exe\n')
            for cwd, expected in [(game, True), (outside, False), (missing, False), (link, False)]:
                scope = SimpleNamespace(stdout=f'p42\nn{cwd}\n', returncode=0)
                with patch.object(s.subprocess, 'run', side_effect=[ps, scope]):
                    result = s.snapshot(root)
                self.assertEqual(bool(result), expected)
                if expected:
                    self.assertEqual(result[0]['path'], r'c:\games\blackflagresynced\acblackflag.exe')
                    self.assertEqual(result[0]['pid'], 42)

    def test_original_windows_process_path_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            ps = SimpleNamespace(stdout='42 Thu Sep 10 02:00:00 2026 C:\\Apps\\game.exe\n')
            scope = SimpleNamespace(stdout=f'p42\nn{folder}\n', returncode=0)
            with patch.object(s.subprocess, 'run', side_effect=[ps, scope]):
                result = s.snapshot(folder)
            self.assertEqual(result[0]['path'], GAME['path'])

    def test_running_game_is_detected_without_a_hub_session(self):
        self.assertEqual(s.classify({'id': 'game', 'lifecycle': CONFIG}, [GAME, STEAM], None), 'running')

    def test_launcher_is_not_game_and_cleanup_blocks_relaunch(self):
        profile = {'id': 'game', 'lifecycle': CONFIG}
        self.assertEqual(s.classify(profile, [STEAM], None), 'idle')
        self.assertEqual(s.classify(profile, [STEAM], {'profile': profile, 'stage': 'launch_requested'}), 'starting')
        self.assertEqual(s.classify(profile, [], {'profile': profile, 'stage': 'game_observed'}), 'closing')
        self.assertEqual(s.classify(profile, [], {'profile': {'id': 'other'}}), 'busy')

    def test_stale_state_without_live_lock_does_not_claim_running(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(s, 'STATE', Path(folder)):
            (Path(folder) / 'old.json').write_text(json.dumps({'profile': {'lifecycle': CONFIG}, 'stage': 'game_observed'}))
            (Path(folder) / (s.scope_key('/test') + '.lock')).touch()
            self.assertIsNone(s.active_session('/test'))

    def test_status_failure_is_unknown_not_stopped(self):
        with patch.object(s, 'snapshot', side_effect=RuntimeError('scope unavailable')):
            self.assertEqual(s.statuses([{'id': 'game', 'lifecycle': CONFIG}])['states']['game'], 'unknown')

    def test_statuses_keep_environments_separate(self):
        other = dict(CONFIG, processRoot='/other')
        with patch.object(s, 'snapshot', side_effect=[[GAME], []]), patch.object(s, 'active_session', return_value=None):
            self.assertEqual(s.statuses([{'id': 'a', 'lifecycle': CONFIG}, {'id': 'b', 'lifecycle': other}])['states'],
                             {'a': 'running', 'b': 'idle'})

    def test_stop_only_signals_exact_game_and_preserves_companions(self):
        with patch.object(s, 'snapshot', return_value=[GAME, STEAM, ROCKSTAR, OTHER]), patch.object(s.os, 'kill') as kill:
            result, code = s.stop({'lifecycle': CONFIG})
            kill.assert_called_once_with(GAME['pid'], s.signal.SIGTERM)
            self.assertEqual((code, result['signalled_count']), (0, 1))

    def test_stop_refuses_reused_pid_or_changed_scope(self):
        for latest in [[dict(GAME, born='new')], [], [dict(GAME, path=OTHER['path'])]]:
            with patch.object(s, 'snapshot', side_effect=[[GAME], latest]), patch.object(s.os, 'kill') as kill:
                s.stop({'lifecycle': CONFIG})
                kill.assert_not_called()

    def test_stop_does_not_signal_on_incomplete_recheck(self):
        with patch.object(s, 'snapshot', side_effect=[[GAME], RuntimeError('scope unavailable')]), patch.object(s.os, 'kill') as kill:
            with self.assertRaises(RuntimeError): s.stop({'lifecycle': CONFIG})
            kill.assert_not_called()

    def test_only_new_launcher_groups_close(self):
        self.assertEqual(s.cleanup_candidates([STEAM, ROCKSTAR], [STEAM], CONFIG), [ROCKSTAR])

    def test_restarted_preexisting_group_is_preserved(self):
        new_steam = dict(STEAM, pid=99, born='new')
        self.assertEqual(s.cleanup_candidates([new_steam], [STEAM], CONFIG), [])

    def test_active_game_or_other_game_prevents_cleanup(self):
        for active in [GAME, OTHER]:
            self.assertEqual(s.cleanup_candidates([STEAM, active], [], CONFIG), [])

    def test_pid_reuse_is_not_signalled(self):
        replacement = dict(STEAM, born='reused')
        # Initial target disappears and its PID is recycled before signalling.
        with tempfile.TemporaryDirectory() as folder, patch.object(s.time, 'sleep'), \
             patch.object(s, 'snapshot', side_effect=[[STEAM], [STEAM], [STEAM], [replacement], []]), \
             patch.object(s.os, 'kill') as kill:
            s.cleanup({'profile': {'lifecycle': CONFIG}, 'baseline': [], 'owned': [STEAM]}, Path(folder) / 'state.json')
            kill.assert_not_called()

    def test_game_restarts_before_signal(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(s.time, 'sleep'), \
             patch.object(s, 'snapshot', side_effect=[[STEAM], [STEAM], [STEAM], [STEAM, GAME], [STEAM, GAME]]), \
             patch.object(s.os, 'kill') as kill:
            s.cleanup({'profile': {'lifecycle': CONFIG}, 'baseline': [], 'owned': [STEAM]}, Path(folder) / 'state.json')
            kill.assert_not_called()

    def test_only_observed_session_process_is_signalled(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(s.time, 'sleep'), \
             patch.object(s, 'snapshot', return_value=[STEAM, ROCKSTAR]), patch.object(s.os, 'kill') as kill:
            s.cleanup({'profile': {'lifecycle': CONFIG}, 'baseline': [], 'owned': [STEAM]}, Path(folder) / 'state.json')
            kill.assert_called_once_with(STEAM['pid'], s.signal.SIGTERM)

    def test_observed_exit_cleans_up_but_never_started_does_not(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'state.json'
            s.write_state(path, {'profile': {'lifecycle': CONFIG}, 'baseline': []})
            with patch.object(s, 'snapshot', return_value=[]), patch.object(s, 'cleanup') as cleanup, \
                 patch.object(s.os, 'close'):
                s.watch(path, 999)
                cleanup.assert_not_called()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'state.json'
            s.write_state(path, {'profile': {'lifecycle': CONFIG}, 'baseline': []})
            with patch.object(s, 'snapshot', side_effect=[[GAME], [STEAM]]), patch.object(s, 'cleanup') as cleanup, \
                 patch.object(s.time, 'sleep'), patch.object(s.os, 'close'):
                s.watch(path, 999)
                cleanup.assert_called_once()

if __name__ == '__main__':
    unittest.main()

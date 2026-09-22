"""Isolated preparation/restore tests; no Wine, game, or production writes."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('prepare_v6', Path(__file__).parents[1] / 'prepare-v6.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.base = self.root / 'performance'
        self.prefix = self.root / 'prefix'
        self.engine = self.root / 'engine'
        self.ctl = self.root / 'gamepolicyctl'
        self.patch = patch.multiple(m, ROOT=self.root, BASE=self.base, PREFIX=self.prefix,
                                    ENGINE=self.engine, GAMEPOLICY_CTL=self.ctl)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def put(self, path, data=b'fixture'):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def setup_runtime(self):
        pkg = self.root / 'platform/packages/black-flag/compatibility/v6'
        module = self.put(pkg / 'BlackFlagCompatibility.dylib')
        self.put(pkg / 'manifest.json', json.dumps({'module_sha256': m.sha(module), 'source_hashes': {}}).encode())
        renderer = self.root / 'supplied'
        names = ['external/D3DMetal.framework/Versions/A/D3DMetal', 'external/libd3dshared.dylib',
                 'wine/x86_64-windows/nvngx-on-metalfx.dll', 'wine/x86_64-windows/nvapi64.dll']
        hashes = {name: m.sha(self.put(renderer / name, name.encode())) for name in names}
        version = self.put(self.engine / 'lib/wine/x86_64-windows/version.dll', b'original wine')
        proxy = self.put(self.base / 'framegen-hws/version-hws.dll', b'proxy')
        self.put(self.base / 'dependencies.json', json.dumps({'renderer_files': hashes,
            'wine_version_dll_sha256': m.sha(version), 'proxy_sha256': m.sha(proxy)}).encode())
        for file in [self.engine / 'bin/wine', self.engine / 'bin/wineserver', self.ctl,
                     self.prefix / 'drive_c/Games/BlackFlagResynced/ACBlackFlag.exe']:
            self.put(file)
        self.ini = self.put(self.prefix / "drive_c/users/player/Documents/Assassin's Creed Black Flag Resynced/ACBlackFlag.ini", b'old ini')
        captured = self.root / 'settings/2026-09-19'
        ini = self.put(captured / 'ACBlackFlag.ini', b'new ini\r\n')
        self.put(captured / 'snapshot.json', json.dumps({'sha256': m.sha(ini)}).encode())
        return renderer

    def test_complete_prepare_and_restore(self):
        renderer = self.setup_runtime()
        m.prepare(renderer, True)
        self.assertEqual(self.ini.read_bytes(), b'new ini\r\n')
        game = self.prefix / 'drive_c/Games/BlackFlagResynced'
        self.assertEqual((game / 'version.dll').read_bytes(), b'proxy')
        self.assertEqual((game / 'version_orig.dll').read_bytes(), b'original wine')
        self.assertEqual((self.prefix / 'drive_c/windows/system32/nvngx.dll').read_bytes(),
                         (renderer / 'wine/x86_64-windows/nvngx-on-metalfx.dll').read_bytes())
        self.assertEqual((self.base / 'd3dmetal/wine/x86_64-unix/nvngx.so').resolve(),
                         (self.base / 'd3dmetal/external/libd3dshared.dylib').resolve())
        history = next((self.base / 'install-history').iterdir())
        m.restore(history)
        self.assertEqual(self.ini.read_bytes(), b'old ini')
        self.assertFalse((game / 'version.dll').exists())
        self.assertTrue((game / 'ACBlackFlag.exe').exists())

    def test_wrong_dependency_changes_no_installed_file(self):
        renderer = self.setup_runtime()
        (renderer / 'external/libd3dshared.dylib').write_bytes(b'wrong')
        with self.assertRaises(RuntimeError):
            m.prepare(renderer, True)
        self.assertEqual(self.ini.read_bytes(), b'old ini')
        self.assertFalse((self.base / 'd3dmetal').exists())

    def test_failed_replacement_restores_previous_files(self):
        a = self.put(self.root / 'src/a', b'new a')
        b = self.put(self.root / 'src/b', b'new b')
        dst = self.put(self.root / 'dst/a', b'old a')
        dst2 = self.root / 'dst/b'
        real = m.atomic_copy
        def fail(src, dest):
            if src == b:
                raise OSError('simulated write failure')
            real(src, dest)
        with patch.object(m, 'atomic_copy', side_effect=fail), self.assertRaises(OSError):
            m.transaction([(a, dst), (b, dst2)], self.base / 'install-history/test')
        self.assertEqual(dst.read_bytes(), b'old a')
        self.assertFalse(dst2.exists())

    def test_restore_refuses_later_user_changes(self):
        renderer = self.setup_runtime()
        m.prepare(renderer, True)
        self.ini.write_bytes(b'changed by game')
        with self.assertRaises(RuntimeError):
            m.restore(next((self.base / 'install-history').iterdir()))
        self.assertEqual(self.ini.read_bytes(), b'changed by game')
        self.assertTrue((self.prefix / 'drive_c/Games/BlackFlagResynced/version.dll').exists())

    def test_live_prefix_is_refused(self):
        with patch.object(m.session, 'snapshot', return_value=[{'pid': 123}]), self.assertRaises(RuntimeError):
            m.ensure_idle()

    def test_keep_settings(self):
        renderer = self.setup_runtime()
        m.prepare(renderer, False)
        self.assertEqual(self.ini.read_bytes(), b'old ini')

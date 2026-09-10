"""Black Flag runtime configuration; separate prefix from the working GTA setup."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / 'engines/wineforge-0.6.0.4'
PREFIX = ROOT / 'environments/black-flag-resynced'


def environment():
    env = os.environ.copy()
    for name in list(env):
        if name.startswith(('WINE', 'DXVK', 'DXMT', 'D3DM', 'WFDX', 'CX_', 'DYLD_')):
            env.pop(name)
    # Black Flag'e ozel D3DMetal 4.0b2 (Apple Evaluation environment 4.0 beta 2).
    # Paylasilan motor 4.0b1 olarak kalir; GTA etkilenmez.
    metal = ROOT / 'packages/black-flag/d3dmetal-4.0b2'
    if not (metal / 'external/D3DMetal.framework').exists():
        metal = ENGINE / 'lib/d3dmetal'
    env.update({
        'TZ': 'Europe/Istanbul',
        'ROSETTA_ADVERTISE_AVX': '1',
        'WINEPREFIX': str(PREFIX),
        'WINESERVER': str(ENGINE / 'bin/wineserver'),
        'WINELOADER': str(ENGINE / 'bin/wine'),
        'PATH': str(ENGINE / 'bin') + os.pathsep + env.get('PATH', ''),
        'DYLD_LIBRARY_PATH': ':'.join(map(str, [ENGINE / 'lib', metal / 'external'])),
        'DYLD_FRAMEWORK_PATH': str(metal / 'external'),
        'D3DMETAL_RUNTIME_DIR': str(metal),
        'DXMT_RUNTIME_DIR': str(ENGINE / 'lib/dxmt'),
        'WFDXCOMPAT_RUNTIME_DIR': str(ENGINE / 'lib/wfdxcompat'),
        'GRAPHICS_BACKEND': 'd3dmetal',
        'WINEDLLOVERRIDES': 'dxgi,d3d10,d3d10core,d3d11,d3d12=b;winemenubuilder.exe,mscoree,mshtml=d',
        'WINEDEBUG': 'err+all,warn+module',
    })
    return env


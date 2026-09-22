# Install the current v6 play setup

This is the setup used for the one-week, 14-hour gameplay run. It includes our v6 Mac graphics repair, 4% presentation zoom, DLSS-to-MetalFX launch configuration, game-local frame-generation capability proxy, Game Mode supervisor and full captured INI. It is a compatibility package for an existing installation, not a game or a complete Wine distribution.

## Required existing environment

- Apple Silicon with Rosetta capable of running the game's x86-64/AVX workload.
- The tested WineForge **0.6.0.4** engine and a working, dedicated Black Flag prefix.
- Your installed Windows game; the tested package was identified as **1.0.6** in the original installation records. Other game builds need verification.
- Your own D3DMetal **4.0 beta 2** directory, including `external/` and `wine/`. Obtain Apple components from Apple's distribution. The installer checks the renderer, shared library, MetalFX/NVAPI bridge and Wine forwarding DLL against [dependency hashes](../platform/packages/black-flag/experiments/v6-performance/dependencies.json).
- Xcode's `/Applications/Xcode.app/Contents/Developer/usr/bin/gamepolicyctl` for the current Game Mode supervisor.
- A working Python 3. Use `/opt/homebrew/bin/python3` on the tested machine; its `/usr/bin/python3` Xcode shim currently fails before executing scripts.

The tested prefix has Wine Mac Driver `RetinaMode=y`. Preserve that setting when migrating an existing setup; this installer does not modify registry/display modes. The full INI contains the captured adapter/display preferences, which may need adjustment on another machine. Hardware, operating system and game versions can affect results.

The repository does **not** contain the Apple binaries, Wine engine, game, prefix, personal Options/progression saves, account data or the full GornHub app.

## Directory layout

Use this checkout as `<WORKSPACE>`, supplying the existing dependencies at these locations. When updating another workspace, first back up its launch scripts; copy this repository's `platform/tools`, `platform/packages/black-flag/compatibility/v6`, `platform/packages/black-flag/experiments/v6-performance`, `GornHub/Runtime/session.py`, `scripts/prepare-v6.py` and `settings/2026-09-19` to their matching paths. Do not replace a whole prefix or the whole hub.

```text
<WORKSPACE>/
  GornHub/Runtime/session.py
  scripts/prepare-v6.py
  settings/2026-09-19/{ACBlackFlag.ini,snapshot.json}
  platform/
    tools/{black_flag.py,black_flag_runtime.py}
    packages/black-flag/
      compatibility/v6/{BlackFlagCompatibility.dylib,manifest.json,...}
      experiments/v6-performance/
        supervisor.py
        dependencies.json
        framegen-hws/{version-hws.dll,version_proxy.c,version_proxy.spec}
        d3dmetal/                         [prepared from your renderer]
    engines/wineforge-0.6.0.4/            [supply separately]
      bin/{wine,wineserver}
      lib/...
    environments/black-flag-resynced/    [existing, dedicated prefix]
      drive_c/Games/BlackFlagResynced/ACBlackFlag.exe
      drive_c/users/<user>/Documents/Assassin's Creed Black Flag Resynced/ACBlackFlag.ini
```

## Prepare once, then launch

Close Black Flag and processes belonging to its prefix. From `<WORKSPACE>` run:

```sh
/opt/homebrew/bin/python3 scripts/prepare-v6.py --renderer '/absolute/path/to/your/d3dmetal-4.0b2'
```

The renderer argument must contain `external/` and `wine/`, not just the framework. Do not substitute a different binary by changing the expected hashes.

Preparation performs these steps:

1. Checks the packaged module/source and separately supplied dependency hashes, game/engine paths and exactly one existing game INI.
2. Copies the renderer to Black Flag's isolated `v6-performance/d3dmetal` directory, without replacing any shared renderer.
3. Exposes `nvngx-on-metalfx.dll` under the `nvngx.dll` name and creates its Unix bridge alias. Installs the matching NVAPI/NGX DLLs in this prefix's `System32`.
4. Installs our `version-hws.dll` beside the game as `version.dll`, with the matching Wine DLL as `version_orig.dll` for forwarding.
5. Applies **the complete captured INI** by default. `--keep-settings` skips only that step. Every replaced file is backed up to a timestamped `install-history` directory; failed file replacement rolls back that transaction. A staged isolated renderer may remain after a preparation failure.

No save, trainer or resource modification is included. Ray tracing was enabled in-game; some settings live outside the INI in the personal Options save. Set/check ray tracing in the game menu rather than assuming the INI alone restores every menu option. Language files/localization mods are also not distributed.

Check readiness without launching:

```sh
/opt/homebrew/bin/python3 platform/tools/black_flag.py --check
```

`"ready": true` verifies required files, pinned module/renderer/bridge/proxy hashes and the Unix bridge alias. It does not certify gameplay, successful Game Mode permission or frame-generation gain.

Launch the prepared stack:

```sh
/opt/homebrew/bin/python3 platform/tools/black_flag.py
```

The launcher selects v6 and starts the supervisor, which requests Game Mode and injects the x86-64 Mac dylib into Wine for this game. Do not put the Mac dylib in Windows `System32` or globally set `DYLD_INSERT_LIBRARIES`. The setup uses the dedicated Black Flag prefix and leaves other game environments intact. Existing GornHub profiles can call this adapter; app/profile registration is not included here.

The supervisor restores the previous Game Mode policy on normal exit. Game Mode policy affects the system while leased; if the supervisor is killed abruptly, its journal restores the recorded policy on the next launch. Logs are under `platform/packages/black-flag/launch-state/`; the proxy's small log is in the game directory. There is no timed game shutdown or GPU capture.

## What DLSS means here

The game sees a DLSS interface backed by Apple's `nvngx-on-metalfx` bridge. Our VERSION proxy satisfies the game's hardware-scheduling capability query, enabling the 2× frame-generation menu selection. It does not supply NVIDIA hardware, implement a Windows GPU scheduler or prove a doubling in displayed frames. The player reports 40–45 FPS overall; an isolated frame-generation benefit has not been established. See [code details](CODE.md) and [current settings](RECOMMENDED-SETTINGS.md).

## Restore the previous files

Close the game and use the exact history directory printed by preparation:

```sh
/opt/homebrew/bin/python3 scripts/prepare-v6.py --restore 'platform/packages/black-flag/experiments/v6-performance/install-history/<timestamp>'
```

Restore checks all installed file hashes before replacing anything; it refuses if a file changed afterward, including game-edited settings. Preserve those changes and review the transaction/backups instead of forcing a restore. The command restores overwritten DLLs/INI and removes newly created ones. It retains the isolated renderer and does not roll back your copied launch scripts; restore those from your pre-update backup or the earlier repository revision to return to the older runtime.

v2/v3/v4 remain historical source checkpoints. Simply selecting an old dylib does not revert the new MetalFX/proxy/supervisor stack. Do not change shared GTA files or terminate all Wine prefixes.

# Installation and use

## What goes where?

`BlackFlagCompatibility.dylib` is the ready-to-load **Mac mod**. The `.m` and `.h` files are its editable source; Wine does not load those source files. **Do not rename the dylib to a DLL or place it in Windows `System32`.** Putting it beside `ACBlackFlag.exe` alone does not activate it.

The included launcher injects the dylib into the x86-64 Wine process through the per-launch `DYLD_INSERT_LIBRARIES` environment variable. The module activates for command lines containing `ACBlackFlag.exe`; it is not a system-wide installation.

## Required setup

Use the exact tested renderer build. `manifest.json` pins its SHA-256 to:

```
f5b56df1b8fe8b364dd9530651a3769c8aed948bd343be3b4510604d503e2bad
```

The included compiled module SHA-256 is:

```
50a2e7cf2a58f2f07a09662ffad8a44991fbf9a2d4bbd8ff4d9d5d99cd0b8acb
```

You need a working x86-64 WineForge 0.6.0.4 environment, Rosetta with the required instruction support, and your installed Windows game. Obtain Apple's evaluation environment through Apple's own distribution. The repository neither downloads these dependencies nor provisions a Wine prefix or installs the game.

The existing test configuration already had these prerequisites working. Other installations must prepare them separately; copying this repository alone is insufficient.

## Option A: existing GornHub platform layout

Close Black Flag before replacing its compatibility module. Preserve a copy of the current module, manifest and launcher so you can restore that version.

The repository mirrors the relevant part of our workspace:

```
<WORKSPACE>/
  GornHub/Runtime/session.py
  platform/
    tools/black_flag.py
    tools/black_flag_runtime.py
    packages/black-flag/compatibility/v2/
      BlackFlagCompatibility.dylib
      manifest.json
      ...source files...
    packages/black-flag/d3dmetal-4.0b2/       [supply separately]
      external/D3DMetal.framework/Versions/A/D3DMetal
    engines/wineforge-0.6.0.4/               [supply separately]
      bin/wine
      bin/wineserver
      lib/...
    environments/black-flag-resynced/       [existing prefix]
      drive_c/Games/BlackFlagResynced/ACBlackFlag.exe
```

Copy the compatibility directory and the two launcher files to the corresponding locations in your existing workspace. Ensure the matching `GornHub/Runtime/session.py` helper is present. Do not replace your whole GornHub directory or an existing prefix. The repository does not include the hub's app/profile installation.

From `<WORKSPACE>`, check prerequisites without starting the game:

```sh
python3 platform/tools/black_flag.py --check
```

`"ready": true` means the required files and pinned module/renderer hashes passed. It is **not** a gameplay test.

Then launch:

```sh
python3 platform/tools/black_flag.py
```

The launcher preserves game settings and saves, rejects duplicate launches in the dedicated prefix, and leaves the game running independently of the terminal. It does not take diagnostic captures or close the game after a timer. Existing installed GornHub profiles can call this same adapter.

Logs are written to `platform/packages/black-flag/launch-state/game.log` and one previous log. Successful module loading prints `Black Flag compatibility v2 loaded.`. A successful launch request only confirms process creation; verify the actual menu and gameplay.

## Option B: another Wine folder layout

This is a developer adaptation, not a tested universal installer. First establish that the chosen x86-64 Wine process uses the exact pinned D3DMetal binary. Then adapt `ROOT`, `ENGINE`, `PREFIX`, `GAME` and renderer locations in the two Python files to your own installation. Preserve the hash checks and source-state repair prerequisites.

The essential injection mechanism is:

```sh
DYLD_INSERT_LIBRARIES="/absolute/path/BlackFlagCompatibility.dylib"   "/absolute/path/to/wine" 'C:\Games\BlackFlagResynced\ACBlackFlag.exe'
```

That line shows **only injection**. It assumes the prefix, working directory and renderer environment are already configured. The complete tested environment is defined in `platform/tools/black_flag_runtime.py`; generic Wine defaults are not an equivalent configuration. Set injection only for this game invocation, not globally in a shell profile.

The dylib itself does not enforce the manifest's renderer hash. The supplied launcher does. Bypassing it requires performing that check yourself. Do not substitute another D3DMetal build just because it has the same product version label.

## Checking the result

Check text in the opening screen and hub, enter actual gameplay, then pause. Test SDR and HDR separately if you intend to use both. Recorded video intros are not proof that live 3D rendering is correct. Higher resolutions and other machines require their own validation.

If `--check` fails, verify the layout and hashes rather than disabling the checks. If text/world surfaces disappear again, confirm that the new process loaded v2 and the intended renderer; do not stack old diagnostic injection modules. A pink pause background can indicate an unmatched overlay configuration; avoid broad shader suppression.

## Remove or revert

Close Black Flag. Restore your previously saved launcher/module/manifest, or remove this mod's per-launch injection from a manually adapted setup. Removing the mod restores the previous rendering behavior and may restore the original graphics defects. No save restoration or game reinstall is required by this module. This repository includes v2 only; the older local v1 snapshot is not supplied as a rollback package.

Do not replace the shared GTA renderer or shut down all Wine environments to update this Black Flag-specific mod.

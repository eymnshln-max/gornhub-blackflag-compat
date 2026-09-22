# Current v6 packaging validation — 19 September 2026

## 22 September 2026 — publication cleanup

- Reworked the documentation into a direct technical account of the symptoms, measurements, corrections and implementation. Condensed the operational investigation notes while retaining the key measurements and links to primary evidence.
- Normalized the v6 module install name to `@rpath/BlackFlagCompatibility.dylib` and renewed its ad-hoc signature. All 18 file-backed Mach-O sections match the previous binary exactly; only packaging metadata changed. The manifest now pins the repackaged binary. The build script uses the same portable install name.
- All six isolated installer/rollback tests passed. Code-signature verification and package source/module hash checks passed. No game, installed runtime, settings or saves were changed.

- All 20 v6 `.m`/`.h` files and the committed dylib match the active installation and manifest hashes. The runtime environment, supervisor, session helper and compiled VERSION proxy also match the active files byte-for-byte. Publishing adds stricter launcher checks; it does not alter the installed game.
- Verified the dependency manifest against the active D3DMetal/shared library/MetalFX/NVAPI files, both NGX aliases, prefix DLLs, game-local proxy and original VERSION forwarding DLL.
- Six isolated preparation tests passed: complete preparation/restore, wrong-dependency refusal before installed-file changes, rollback after a simulated write failure, refusal to overwrite later user changes, live-prefix refusal and optional settings preservation. Tests used temporary fixture trees, not the actual prefix.
- All 19 session tests passed.
- The v6 dylib rebuilt and ad-hoc signed with the Command Line Tools SDK. Hook inheritance/cross-thread invalidation, SDR/HDR overlays with negative controls, mesh/raster/offscreen restoration and resolution controls at 1512×945, 2560×1600 and 3024×1964 all passed. The rebuild remains in ignored `build/`; the committed binary is the active player-used binary.
- The incomplete checkout refuses launch. The Windows proxy is the previously active compiled binary and was not rebuilt for this publication.
- No game was launched, no live settings or saves were changed, and no separate FPS benchmark was run for packaging. The one-week / 14-hour / 40–45 FPS report describes regular gameplay, not a controlled benchmark.

# Earlier repository packaging validation — 10 September 2026

## v4 update

- Preserved the original v2 package and added curated v3/v4 source, compiled modules and manifests. Module and all source hashes match the corresponding local packages.
- At that release, the launcher and build script selected v4. The documented build compiled and signed successfully in this repository without modifying the player-tested binary.
- Added the production-activation offscreen and resolution controls to the script. Their v4 GPU results and the player terrain confirmation were obtained during the preceding implementation work; no additional gameplay was run for this upload.
- Updated installation hash, code guide, current scope and release history. Local Markdown links pass. No game payloads, renderer, translation installer, settings backups, saves or prefixes added.

## Original v2 packaging validation

This check validated the repository packaging without starting or modifying the installed game.

- The committed prebuilt dylib matches the tested module hash in `manifest.json`.
- All 16 `.m`/`.h` entries match the manifest source hashes.
- The documented build script successfully compiled and ad-hoc signed an isolated x86-64 dylib. It did not replace the player-tested package binary.
- Standalone SDR and HDR overlay controls passed their matching and nonmatching cases (256 pixels each).
- The mesh control passed original-state restoration and two-layer blending; its standard raster fallback also passed (256 pixels each).
- All 17 existing session ownership tests passed.
- Markdown file/image links were checked for local targets. No full game, renderer, prefix or large movie is included.

These checks validate the supplied source/build instructions and packaging. They are distinct from the earlier real-game confirmations recorded in the case study and do not certify other hardware, renderer builds or a full campaign.

# Repository packaging validation — 10 September 2026

## v4 update

- Preserved the original v2 package and added curated v3/v4 source, compiled modules and manifests. Module and all source hashes match the corresponding local packages.
- Current launcher and build script select v4. The documented build compiled and signed successfully in this repository without modifying the player-tested binary.
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

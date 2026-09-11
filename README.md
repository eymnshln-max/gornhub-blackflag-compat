# GornHub Black Flag Compatibility

## Current state of the game

A targeted macOS runtime repair that took **Assassin’s Creed Black Flag Resynced** from audio behind a black screen to user-confirmed local gameplay on Apple Silicon, with readable menus/subtitles and working SDR/HDR pause screens.

Developed for GornHub on 7–10 September 2026. This repository contains our Objective-C/Metal source, the **tested compiled mod**, launch adapters, selected measurements and an illustrated English engineering report.

## What it does

The observed D3DMetal path skipped color attachment setup for some pipelines. Missing target formats, blending and channel write masks produced black output, broken text and missing scene surfaces. The mod observes the original state and restores it when binding raster and mesh pipelines against their actual render targets. A separate, narrowly matched workaround suppresses the corrupt pause overlay in SDR and HDR.

This is a **macOS `.dylib` loaded into the Wine process**, not a Windows DLL to drop beside the game executable. It does not turn the game into a native ARM build. It depends on the existing Wine/Rosetta/D3DMetal stack.

## Start here

- **[Install and use the mod](docs/INSTALLATION.md)** — prerequisites, exact locations, loading, checks and removal.
- **[Build and understand the code](docs/CODE.md)** — file map, build command and controlled tests.
- **[Full engineering case study](docs/CASE_STUDY.md)** — problem, investigation, mistakes, solution, screenshots and dated public compatibility comparison.
- **[Recommended settings](docs/RECOMMENDED-SETTINGS.md)** — the measured configuration that holds a locked 30 fps, why 60 is not reachable on this stack, and which settings actually matter.
- **[Evidence index](docs/EVIDENCE.md)** — what was measured and what the result does not establish.
- **[Compiled mod and source](platform/packages/black-flag/compatibility/v4/)** — `BlackFlagCompatibility.dylib` and its manifest.

## Tested configuration and scope

Apple M5, 16 GiB RAM; macOS 26.6.2 (25G83); x86-64 WineForge 0.6.0.4 under Rosetta; the Black Flag-specific **D3DMetal 4.0 beta 2 binary pinned in the manifest**. The tested game installation was v1.0.6. Opening gameplay, menus, subtitles and pause were confirmed by the player, including HDR. Full-campaign stability and performance across machines are unverified.

Internal offsets make the module renderer-build-specific. Current version: **v4**. Exact original-state restoration covers color targets of any size; inferred fallbacks and pause suppression retain a 400–4096 by 200–2160 size gate. The owner confirmed the island terrain fix after using 2560×1600 High settings. See [release history](docs/CHANGELOG.md). This is not a general compatibility guarantee for other builds, resolutions, wrappers or games.

## Included and required separately

Included: our mod source and compiled module, Python adapters, session helper/tests, screenshots and selected diagnostic evidence.

Obtain separately: the game, WineForge and its dependencies, Rosetta, Apple’s evaluation environment/D3DMetal, and any required accounts. No game executables/assets, Apple renderer binaries, account credentials, saves or full Wine prefixes are included. This repository is not a complete GornHub app installer.

## Credits

Project owner and hands-on tester: **eymnshln-max**, the GornHub creator. The owner directed the goal, challenged unsupported diagnoses, distinguished video playback from live rendering, identified the actual menu/gameplay stages and repeatedly validated visual changes. These observations materially changed the investigation.

Implementation and investigation: Codex, with earlier diagnostic work from Claude. The corrected readback tools, controls and accumulated evidence contributed to the final investigation; discarded hypotheses are preserved as history rather than presented as established facts.

Built on work by Wine/WineForge and Apple's Rosetta, Metal and D3DMetal teams. No affiliation or endorsement is implied. The report compares dated public evidence; it cannot establish unpublished work by other teams. No open-source license is granted in this private snapshot.

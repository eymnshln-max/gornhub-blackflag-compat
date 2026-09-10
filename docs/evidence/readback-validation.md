# Bounded reader correction — 2026-09-08

User authorized fixing the measurement errors and one short check, not an open-ended game-port project.

## Completed

- `pixels.py` explicitly decodes RGBA8/BGRA8, RGB10A2, RG11B10Float (92), and RGBA16Float (115). Handles subnormals, NaN/Inf and negatives; unknown formats fail instead of pretending bytes are RGB. Nonfinite float previews are magenta BY THE PREVIEW TOOL, not evidence of missing game textures. HDR display clips/gamma-transforms values; use decoded floats/raw bytes for numeric conclusions.
- Corrected Claude scratchpad `raw2png.py`, `prev.py`, `sheet.py` to share this decoder (`pixels_checked.py`). Original converters are preserved here in `converter-backups/`. Corrected contact sheet is `sheet-checked.png` beside Claude's original sheet; historical `.png` thumbnails are not silently regenerated. Old source captures retain their timing/aliasing defect.
- `paired.m` is a new bounded Metal 4 buffer-to-texture operation reader, not a broad late texture scan. It copies source bytes on GPU before the real upload, then destination bytes after it, in the original encoder. Explicit intra-pass and queue-stage barriers include resource-alias visibility. Adds staging buffers to a residency set on the command buffer. Accepts data only after the original submitting queue signals completion. Caps staging memory and takes one supported operation per process.
- Supports plain/options buffer-to-texture entry points on the concrete Metal 4 encoder instantiated at startup. Only uncompressed supported 2D formats, depth 1, no special options. Does NOT cover all classes, custom compute copies, texture-to-texture copies, Metal 3, compressed assets or other rendering operations. Barriers perturb scheduling, so even an equal pair cannot rule out an original synchronization bug.

## Validation actually performed

Compiled x86_64 and ran under Rosetta on this Mac, matching the game process architecture.

1. Core GPU selftest with Metal API Validation enabled: formats 70, 92, 115 all PASS, zero source/target byte mismatches. 31x17 patterned content, padded rows, nonzero source offset and destination origin, explicit untracked placement heap, two texture objects at identical heap offset 0. After snapshot, alias texture overwrites the region. Late read sees zeros while snapshot preserves the original bytes. No Metal validation error reported.
2. Same test with actual Objective-C copy-method hooks installed, without debug-layer classes: all three formats PASS, zero mismatches. This verifies hooked copy path, not every game API path or asynchronous file writer.
3. CPU decoder checks PASS: packed HDR known values, half floats, subnormal, NaN/Inf, negative values and 8-bit RGB.

These are targeted measurement tests, not evidence the game renders correctly.

## One game run

`game/launch.json`: owned PID 39965. Canonical Black Flag runtime, scoped diagnostic injection only; no ini or D3DMetal setting experiment. Inherited `MTL_` diagnostic environment is stripped by `run_once.py`.

`game/pair.log`: constructor installed hooks for AGXG17GFamilyComputeContext_mtlnext and its queue. **No CALL/ENCODED/COMPLETE events in the 60-second window. No source/target result obtained.** The native objects constructed by the diagnostic itself produce the class names; their existence does not prove the game uses that backend. Do not infer absence of copies from absence of hook hits.

`game/finished.json`: 60-second boundary, owned process terminated, settings restored byte-for-byte to pre-run snapshot. Post-run process check found no ACBlackFlag.exe. No automatic repeat; runner refuses if launch.json exists. GTA and canonical runtime code unchanged. No gameplay success.

## Next-agent boundary

Do not return to the old `scan.m` or treat its colored output as corrupt game data. Identify the actual invoked copy path in this exact runtime before adding further hooks. This turn stopped at the agreed single-game-run boundary. Source-vs-target failure and its root cause remain unproven.

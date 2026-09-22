# Code, build and controls

## How the repair works

1. Observe original color attachment state at known D3DMetal descriptor creation call sites. The read-only decoder uses build-specific caller-stack and internal-structure layouts.
2. Associate that state with raster and mesh pipeline objects.
3. When the pipeline is bound, inspect the actual render-pass attachment formats and reconstruct the missing state using the pipeline's own original records. Cache repaired pipelines.
4. Where applicable, fall back to a unique matching function-state template, then a format-only repair.
5. Apply exact original-state restoration to offscreen targets regardless of size. Keep inferred fallbacks and overlay suppression within the established display-size gate. Clear stale associated source records if a matched decode fails.
6. Separately recognize the measured faulty pause overlay and disable its color writes. This avoids covering the good image with the corrupt effect; it does not fix the underlying overlay shader.

## Source map

All C/Objective-C sources below are in `platform/packages/black-flag/compatibility/v6/`.

| File | Purpose |
| --- | --- |
| `compatibility.m` | Entry point, process filter, hook installation, render-pass tracking and repair order |
| `hooks.h`, `hooks-control.m` | Bounded thread-local method caches, epoch invalidation and inheritance control |
| `presentation_zoom.h` | Existing 4% presentation zoom |
| `source_state.h`, `source_state_decode.h` | Observe and decode the original D3DMetal attachment records |
| `pipeline_info.h`, `pipeline_info_chain.h` | Describe and retain pipeline metadata |
| `pipeline_creation.h`, `mesh_source_create.h` | Capture raster and mesh pipeline creation |
| `source_restore_mesh.h` | Restore original per-pipeline state for raster and mesh paths |
| `scene_template_restore.h` | Scoped template-based fallback |
| `attachment_repair.h`, `target_format.h` | Actual render-target format handling |
| `pause_overlay.h` | Scoped SDR/HDR pause overlay workaround |
| `pause-control.m`, `hdr-control.m`, `mesh-control.m`, `offscreen-control.m`, `resolution-control.m` | Standalone GPU controls, not game launchers |
| `manifest.json` | Tested module, renderer and source hashes |

`platform/tools/black_flag.py` performs preflight and detached launch. `black_flag_runtime.py` defines the dedicated environment. `GornHub/Runtime/session.py` scopes process ownership; its existing tests are included in their original relative layout.

## Build the dylib

Use macOS with Xcode command-line tools and a Metal SDK supporting the mesh APIs used here:

```sh
./scripts/build-compatibility.sh
```

Output: `build/BlackFlagCompatibility.dylib`. The script compiles for **x86_64**, matching the Wine/D3DMetal process rather than the host CPU architecture. `-fno-omit-frame-pointer` is required by the caller-stack observation. Source uses manual Objective-C ownership; do not enable ARC without porting it.

The build does not replace the committed, player-tested binary or alter the manifest. A local rebuild may have a different hash. After controlled validation, installing a rebuild requires copying it into the package and updating only `module_sha256` to its actual SHA-256; changes to source also require refreshing the relevant source hashes. Do not change `d3dmetal_sha256` to bypass a renderer mismatch: offsets must be re-established for any new build.

## Isolated checks

```sh
python3 -m unittest discover -s GornHub/tests -p 'test_session.py'
./scripts/build-compatibility.sh controls
```

The second command builds and runs SDR/HDR/mesh controls with `BF_COMPAT_TEST=1`, then offscreen and resolution controls with normal game-name activation and no test override; it does not start Black Flag. It needs a usable Metal device. SDR/HDR controls test a matched overlay and a nonmatching negative case; the mesh control checks restored attachment behavior. These controls do not simulate the entire game or validate all private ABI offsets. Full source-comparison evidence and real-game confirmations are documented separately.

The test environment switch bypasses the game-only activation filter and the normal target-size filter. **Never enable `BF_COMPAT_TEST` in normal play.**

## Maintenance limits

This is a captured, working engineering snapshot rather than a general renderer library. Return offsets and struct offsets are private ABI details of the pinned binary. Keep hash gates, positive controls and real-game validation when changing it. Do not infer a root cause merely from non-black pixels, a missing hook event or a successfully compiled pipeline; those mistakes are recorded in the case study.

## MetalFX and frame-generation selection

`platform/tools/black_flag_runtime.py` enables `D3DM_ENABLE_METALFX=1` and selects the isolated renderer. The installer exposes Apple’s existing `nvngx-on-metalfx.dll` as `nvngx.dll` in both the renderer and prefix, with the Unix alias to `libd3dshared.dylib`. This routes the game’s DLSS interface to the Apple bridge; it is not native NVIDIA DLSS running on an RTX GPU.

`platform/packages/black-flag/experiments/v6-performance/framegen-hws/version_proxy.c` is our game-local VERSION proxy. Its 17 exports forward to the supplied Wine `version.dll`, installed as `version_orig.dll`. It intercepts `D3DKMTQueryAdapterInfo` imports and dynamic lookup, reporting the WDDM 2.7 hardware-scheduling bits required by the game menu. It does not implement a Windows GPU scheduler, interpolation, or DLSS 5. Making the 2× option selectable does not independently prove additional displayed frames.

`supervisor.py` requests Game Mode while the game runs and restores the prior policy on normal exit. The policy is system-wide while leased; the supervisor only tracks Black Flag’s prefix. A journal supports recovery at the next launch after an abrupt supervisor termination.

The prebuilt `version-hws.dll` is the exact active binary. Its `.c` and Wine `.spec` export source are included. Rebuilding requires a Windows x86-64 C toolchain with the D3DKMT headers and an export definition preserving all 17 `version_orig` forwarders; the Mac dylib build script does not rebuild this DLL.

The preparation script has isolated filesystem tests:

```sh
python3 -m unittest discover -s scripts/tests
```

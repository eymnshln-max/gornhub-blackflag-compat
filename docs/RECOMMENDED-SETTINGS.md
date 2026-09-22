# One Week of Play — Current Settings, RTX On, 40–45 FPS

Updated 19 September 2026. **One week of play, 14 hours played, approximately 40–45 FPS average, with ray tracing enabled.** These results come from regular gameplay on the Apple M5 / 16 GB MacBook Pro, not a new automated benchmark. The current frame-rate target is 45 FPS.

## Current configuration

| Setting | Current state |
| --- | --- |
| Resolution selector / saved fullscreen dimensions | 1920×1200 |
| Display mode | Borderless (`WindowMode=2`) |
| Saved window dimensions | 3024×1964 |
| Graphics preset | Custom; all exact values below |
| Ray tracing / RTX option | On in the game menu |
| HDR | Off (`HDREnabled=0`) |
| VSync | Off |
| Frame-rate limiter | On, 45 FPS target |
| Upscaler | In-game NVIDIA DLSS selection, Quality; Apple MetalFX bridge enabled in the local runtime |
| Frame generation | In-game NVIDIA DLSS 2× selection enabled |
| Saved dynamic-resolution bounds | 0.44–1.00 |
| Sharpness | 0.20 |
| Field-of-view scale | 1.15 |

Both fullscreen and window dimensions are retained exactly as saved. The actual internal render resolution and presentation dimensions were not measured in this documentation update. The saved dynamic-resolution bounds do not prove that every upscaler mode uses that entire range.

“RTX on” refers to the game's ray-tracing option running on the Apple GPU, not NVIDIA hardware. The local runtime exposes the DLSS interface through Apple's `nvngx-on-metalfx` bridge (`D3DM_ENABLE_METALFX=1`). The game-local VERSION proxy makes the hardware-scheduling capability check pass so the frame-generation setting can be selected. **The 2× menu setting is recorded here; it is not proof of a measured doubling in displayed frames or an isolated frame-generation performance gain.** The 40–45 FPS figure is the overall gameplay result with this setup.

## Exact active settings

[Download the complete ACBlackFlag.ini](../settings/2026-09-19/ACBlackFlag.ini). This is a byte-for-byte copy of the active file, including every section, rather than a selected graphics preset. [Snapshot metadata and SHA-256](../settings/2026-09-19/snapshot.json).

To reuse it, close the game, back up your current INI, then place this file at `Documents/Assassin's Creed Black Flag Resynced/ACBlackFlag.ini` **inside the game's Wine prefix**. This replaces language, input and display preferences too. It does not install the compatibility runtime. Ray tracing should also be checked in the game menu: the INI's `raytracing_*` values alone do not establish that mode, and the separate Options save is not distributed.

```ini
[Metadata]
StorageVersion=1
[Language]
Text=en-US
Sound=en-US
Subtitles=en-US
[Startup]
StickyKeys=0
ToggleKeys=0
FilterKeys=0
[Display]
AdapterVendorID=4318
AdapterDeviceID=0
MonitorDesc=
DisplayIndex=0
WindowPosX=0
WindowPosY=0
FullscreenWidth=1920
FullscreenHeight=1200
WindowedWidth=3024
WindowedHeight=1964
WindowMaximised=0
RefreshRate=0
WindowMode=2
VSyncMode=0
LastUsedFullscreenMode=1
LastUsedWindowedMode=0
HDREnabled=0
Freesync2Enabled=0
[Feature]
frame_generation_type=1
frame_generation_interpolation_count=1
framerate_limiter=1
framerate_target=45.00000
sharpness_factor=0.20000
upscaler_mode=2
upscaler_type=2
dynamic_resolution_min=0.44000
dynamic_resolution_max=1.00000
[Scalability]
Profile=pc_custom
[Input]
InputSourcesSelectorMode=1
[Options]
Controller Feedback=-1
WideAspectStretchedHUDMode=1
KeyboardHighlightingMode=dynamic
FOVScale=1.15000
AutoFOV=0
LockCursorToTheWindow=0
[Scalability_Custom]
character_hairstrands=6
character_quality=5
effects_particlequality=4
effects_physicsimulation=2
effects_posteffects=2
effects_waterquality=4
geometry_drawingdistance=3
geometry_loadingdistance=3
geometry_micropolygon=0
lighting_lightquality=2
lighting_screenspaceeffects=3
lighting_shadowquality=3
raytracing_bvhquality=1
raytracing_gi=1
raytracing_giquality=1
terrain_deformation=0
terrain_quality=2
terrain_scatterdensity=2
terrain_virtualtexture=2
textures_texturequality=4
volumetriceffects_fogquality=1
volumetriceffects_cloudquality=0
```

## Runtime used for this play report

The active local launcher uses compatibility **v6**, which adds bounded hook-lookup caches to the earlier repairs, with the existing 4% presentation zoom. It runs through the **v6-performance** configuration: isolated D3DMetal 4.0 beta 2, WineForge 0.6.0.4 / Rosetta, the MetalFX bridge, the game-local hardware-scheduling capability proxy and a supervisor that requests Game Mode during play and restores the prior policy on exit.

The repository now packages this **v6 source/binary and launch stack**, including our compiled VERSION proxy. Follow [Installation](INSTALLATION.md) to prepare the MetalFX aliases, proxy forwarding DLL and exact INI. Apple renderer files, the Wine engine/prefix and saves must be supplied separately. Ray tracing was enabled in-game; the INI alone does not capture every setting held in the game’s Options save. No personal Options save is distributed.

## Scope of the result

This setup reached 14 hours of playtime over one week. The result covers gameplay on this machine; it does not establish full-campaign completion, a minimum FPS guarantee, frame-time percentiles, or results on other hardware. The current settings were captured today; the report does not claim that all 14 hours used precisely the same values.

This replaces the older low-resolution / 30-FPS recommendation. Earlier claims of an immutable performance ceiling, zero compatibility-module cost, or guaranteed gains from frame generation are not carried forward. Historical rendering investigations remain in the case study and release history.

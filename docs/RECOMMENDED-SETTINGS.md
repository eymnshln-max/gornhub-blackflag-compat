# Recommended settings — 11 September 2026

Measured on the tested configuration: Apple M5 (10-core GPU), 16 GiB unified memory,
macOS 26.6.2, 3024×1964 built-in display, x86-64 WineForge 0.6.0.4 under Rosetta,
D3DMetal 4.0 beta 2 pinned by manifest, compatibility module v4.

**Result: a locked 30 fps in dense town and combat, 40+ in open terrain and at sea,
with high texture and character quality retained.** These values are what the player
settled on after measurement, not a theoretical preset. Other machines, other builds
and other scenes are unverified.

## Why 30 and not 60

Three player-reported benchmark results, converted to frame times, separate the
fixed cost from the part that scales with settings:

| Configuration | fps | frame time |
| --- | ---: | ---: |
| High quality, 100% resolution scale | 23 | 43.5 ms |
| Everything minimum, 100% resolution scale | 35 | 28.6 ms |
| Everything minimum, lowest resolution | 45 | 22.2 ms |

Shading every pixel of the full 3024×1964 frame costs about 6.4 ms. Quality settings
account for roughly 14.9 ms. The remaining **22.2 ms is fixed** — it does not respond
to resolution or to any graphics option.

A 60 fps frame budget is 16.7 ms. The fixed cost alone exceeds it, so 60 fps is not
reachable on this stack at any settings. 45 fps is the practical ceiling and 30 fps
is the frame rate that holds steady through crowds and combat. The console release
targets 30 fps for this title as well.

Ubisoft's published requirements agree independently: 60 fps at 1440p High is quoted
against an RTX 3080 with 8–10 GB of dedicated VRAM alongside 16 GB of system RAM.
This machine has 16 GB **total**, shared between CPU and GPU, and a 10-core integrated
GPU. At 1080p High the requirement drops to an RTX 3060 — which is roughly where this
configuration lands once the translation cost is included.

## Where the time actually goes

A 60-second CPU profile taken during gameplay at minimum settings (`sample`, 20 ms
interval, idle threads excluded — 30,652 active samples across 95 threads):

| Share | Component |
| ---: | --- |
| 35.0% | Game engine worker threads (`TaskThread00`–`08`) |
| 22.0% | D3DMetal command list translation (15 dispatch queues, each ~78% busy) |
| 19.6% | Other |
| 8.0% | Game `IdleThread` pool |
| 6.6% | Rosetta exception server |
| 6.5% | QueueWorker |
| 2.3% | Loading thread |

Two conclusions follow.

**The bottleneck is CPU-side, not the GPU.** GPU device utilisation during the same
session ranged between 45% and 75%. The GPU is waiting for work. That is why lowering
resolution returns so little and why frame generation — which does not re-run game
simulation — is the more effective lever here than reducing quality.

**The compatibility module is not a performance cost.** `BlackFlagCompatibility.dylib`
never appears at the top of a stack in the profile, and its total inclusive share is
below 2%. Optimising the module would not change the frame rate; it was ruled out as
a suspect by measurement rather than by assumption.

## What matters and what does not

D3DMetal's cost scales with the number of commands the game submits, so the settings
worth lowering are the ones that change draw-call count — draw distance, loading
distance, micropolygon geometry, scatter density, particle count, shadow cascades
(each cascade re-draws scene geometry).

Texture quality, character quality and water quality do not change command count.
Lowering them costs image quality and returns almost nothing. Keep them high.

Ray tracing is the single most expensive option in both frame time and memory; the
BVH acceleration structure is a large, separate allocation. `raytracing_gi=0` in the
INI does **not** disable it — the mode must be turned off in the in-game menu under
Video → Scalability → Ray Tracing Mode.

## The settings

`Documents/Assassin's Creed Black Flag Resynced/ACBlackFlag.ini`

### Display

```ini
WindowPosX=0
WindowPosY=0
WindowedWidth=3024
WindowedHeight=1964
FullscreenWidth=1920
FullscreenHeight=1200
WindowMode=2
VSyncMode=0
HDREnabled=1
```

`WindowPosY=0` with `WindowedHeight` set to the full display height matters. With
RetinaMode enabled in the prefix, the desktop is 3024×1964 in pixels; a window offset
by 66 pixels (the 33-point menu bar, doubled) and 1890 pixels tall leaves a black band
along the top of the screen. It is not adjustable from the in-game menu, because the
resolution selector writes `FullscreenWidth`/`FullscreenHeight`, which `WindowMode=2`
does not use. 3024×1964 is also one of the resolutions covered by the v3 production
filter controls, where 3024×1890 is not.

### Feature

```ini
framerate_target=30.00000
framerate_limiter=0
dynamic_resolution_min=0.44000
dynamic_resolution_max=1.00000
upscaler_mode=1
upscaler_type=9
sharpness_factor=0.25000
frame_generation_type=0
frame_generation_interpolation_count=0
```

Dynamic resolution is left as a **range**, not pinned. The game scales between 44% and
100% to hold the 30 fps target, which keeps open scenes sharp and gives the renderer
room in crowds. Pinning it to 1.00 is what produced the 23 fps result above.

Frame generation is off here by player preference. On a CPU-bound stack it is the one
feature that can raise perceived smoothness without touching the bottleneck, at the
cost of some input latency — worth enabling if a higher displayed frame rate is wanted.

### Scalability

```ini
Profile=pc_custom

textures_texturequality=4
character_quality=5
character_hairstrands=4
effects_waterquality=3
effects_particlequality=4
effects_physicsimulation=2
effects_posteffects=1

geometry_drawingdistance=2
geometry_loadingdistance=2
geometry_micropolygon=0

terrain_quality=3
terrain_scatterdensity=4
terrain_deformation=1
terrain_virtualtexture=2

lighting_shadowquality=4
lighting_screenspaceeffects=4
lighting_lightquality=2

volumetriceffects_fogquality=2
volumetriceffects_cloudquality=2

raytracing_gi=1
raytracing_bvhquality=1
raytracing_giquality=1
```

The geometry distances and micropolygon detail are the values held down; everything
that only affects appearance is left high. Estimated VRAM reported by the game at
these settings is about 4.5 GB of its 12 GB budget, against roughly 9.4 GB of real
GPU memory measured through `ioreg` — the in-game gauge does not account for the
translation layer's own allocations, so it should not be used for tuning.

## Stability note

This is the most stable configuration found for this translation stack, and the
reasoning behind it is specific to that stack: the frame is limited by translated
CPU work — the game's own engine threads under Rosetta plus D3DMetal command list
conversion — rather than by shading throughput. Settings chosen on a native PC would
be balanced differently.

None of the components in that path can be optimised from this repository. Rosetta
and D3DMetal are closed Apple binaries, and the pinned D3DMetal 4.0 beta 2 build is
the one this game's rendering depends on. The compatibility module, which is ours,
was measured and is not a meaningful cost.

Wine debug output was checked and is not a factor: the Black Flag launcher inherits
`WINEDEBUG=err+all,warn+module` and produced only 18 KB of log across a full session.

## Limitations

Single machine, single game build (v1.0.6), single play session. Frame rates come
from the game's own counter as recorded on screen. The CPU profile's active/idle
split is derived from a blocked-stack heuristic, so component shares carry some
uncertainty; the ordering between them is the reliable part. No claim is made about
full-campaign stability, other scenes, other hardware or other builds.

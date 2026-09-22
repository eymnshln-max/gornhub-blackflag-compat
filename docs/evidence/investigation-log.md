# Black Flag graphics investigation

7–10 September 2026. This technical chronology condenses the experimental records. Measurements from incomplete probes are kept separate from the conclusions supported by the final captures and repair.

## Establishing the failure

The game reached Press Any Key, Animus Hub, cutscenes and gameplay with working audio and input. The displayed image remained black or incomplete. Menu, prerecorded video and live gameplay were labeled separately throughout the later captures.

A short device capture contained four command buffers, one render pass and one draw. That draw sampled an existing 1280×720 RGB10A2Unorm texture and presented its contents. Source and output showed the same black image with a gray panel. The capture did not contain the operation that produced the source texture. It therefore established faithful presentation during that window, not an absence of earlier scene rendering.

## Correcting the measurement tools

The initial contact sheets were not reliable evidence of broken uploads:

- Packed RG11B10Float (format 92) and RGBA16Float (115) needed explicit decoding. Reading their raw bytes as RGB or grayscale produced incorrect previews.
- A preview decoder used magenta for NaN/Inf. That color was a display convention, not proof of a missing game texture.
- Heap-backed textures could alias storage. Reading a retained texture outside its live interval could show another resource's contents.
- Copies needed ordering against the producing work. Reading sequentially on an unrelated queue did not preserve a consistent game frame.

Known-pattern GPU controls passed for formats 70, 92 and 115 with zero source/target byte mismatches. Tests covered padded rows, nonzero offsets, destination origins and heap aliasing. A snapshot retained the expected pattern even after an alias overwrote the same heap storage; the late read correctly showed the overwritten content. These controls validated the tested reader paths, not every upload in the game.

See [readback validation](readback-validation.md) for the scope and limitations.

## Finding the actual copy path

D3DMetal contained both classic blit selectors and Metal 4 command-queue selectors. Their presence did not establish the backend used by any particular operation. Probe-created queues likewise did not identify the game's queues.

Live positive controls triggered hooks on both paths. A 240-second run recorded:

| Instrumented operation | Metal 3 | Metal 4 |
| --- | ---: | ---: |
| Buffer-to-texture copies | 17,501 | 0 |
| Queue creations | 14 | 7 |

The observed uploads used `AGXG17GFamilyBlitContext` and the `copyFromBuffer:...toTexture:...options:` variant. Upload counts stopped increasing after the opening load. Earlier hooks on wrapper classes or only the Metal 4 compute encoder had missed this path. Those zero-event records were not evidence that the game performed no copies.

This identified the observed upload path. It did not establish an upload-layout fault.

## Recovering the interface

Producer tracing followed actual resource identities and writer boundaries. UI writers included `PS_Phoenix` pipelines with invalid color-attachment formats.

A narrowly scoped target-format repair produced the first recognizable service dialog and Animus Hub on 9 September. The text still had missing pieces. Gameplay initially showed the HUD over a black world. Format repair recovered part of the output but did not restore all required color state.

Deriving formats from the actual render-pass attachments exposed more scene content. Text and world surfaces still contained defects. A matching color-state template from the same retained vertex and fragment functions restored complete glyphs and subtitles. Ambiguous template matches were rejected. Extending the template path improved character rendering, while significant scene defects remained.

The beach cinematic played correctly, but it was prerecorded video. It was not evidence that the live 3D renderer was correct. Resetting the first-launch options also did not eliminate the remaining surface and pause-overlay corruption.

## Recovering original attachment state

Inspection of the pinned D3DMetal attachment-construction path showed that a zero packed dynamic format could skip format, blending and write-mask setters together. Supplying only a missing format left the remaining color state wrong.

The repair recovered each pipeline's own original attachment state before omission, then combined it with the actual target formats at bind time. In the pinned renderer:

| Field | Location |
| --- | --- |
| `SetupAttachmentDescriptor` | Image-relative offset `0x113813` |
| Raster observation return address | `0x112ec6` |
| Mesh observation return address | `0x113265` |
| Owner pointer | Caller stack + `0x28` |
| Packed format bytes | Caller stack + `0x30` |
| Static state | Owner + `0x70` |
| Target count | Static state + `0x255` |
| Eight color records | Static state + `0x258`, 12 bytes each |

The source/native comparison contained **30,612 eligible attachment pairs with zero mismatches**. It also identified **419 bound pipelines** with positive target counts and zero packed formats. These results supported restoring the original state instead of inferring it from unrelated pipelines.

Raster restoration improved rendering. Applying the same recovery to mesh pipeline creation cleared the other tested scene defects. The pause screen remained a separate failure. See [source-analysis.json](source-analysis.json) and the illustrated [case study](../CASE_STUDY.md) for the comparison and implementation details.

## Isolating the pause overlay

Ordered before/after captures within the same command buffer localized the corruption:

1. `PS_TemporalAA` produced a coherent scene with zero magenta pixels.
2. `ShadePixel` preserved that scene, again with zero magenta pixels.
3. The matching `PS_ShadePixel` draw replaced it with the checker pattern, containing 1,020,768 magenta pixels in the captured output.

The workaround suppresses color writes only for the observed overlay signature: `VS_ShadeVertex` + `PS_ShadePixel`, one color attachment, no depth/stencil, one sample, the recorded blend factors and a full write mask. It preserves the scene underneath rather than repairing the overlay shader itself.

An SDR positive control preserved all 256 background pixels. A negative control with different blend state still rendered normally. The SDR pause screen then displayed correctly in gameplay.

Enabling HDR reproduced the checker pattern because the overlay now targeted format 115 instead of 70. The HDR capture confirmed the matching shader/state signature. Extending the format gate to include RGBA16Float passed the HDR control and restored the pause screen with `HDREnabled=1`.

## Normal runtime and integration

The working hooks were packaged as a lean compatibility module. Normal launches no longer used framebuffer dumps, capture controls, frequent diagnostic logging or a timed shutdown. The launcher pinned module/renderer hashes, rejected duplicate starts and ran detached from the initiating command.

GornHub detected the live game within the dedicated Black Flag environment. Wine could re-execute it with only `ACBlackFlag.exe` as the process name, so lifecycle matching also checked the resolved working directory inside the correct prefix. All 17 lifecycle tests passed, including outside-prefix and symlink-escape cases. A live stop-button click was not part of this validation.

The resulting v2 checkpoint supported the tested gameplay, readable menus/subtitles and SDR/HDR pause screens. Later resolution, terrain and v6 runtime changes are documented in the [release history](../CHANGELOG.md). The screenshots and capture metadata are indexed in [Evidence](../EVIDENCE.md).

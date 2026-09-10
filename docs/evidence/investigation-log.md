# 2026-09-09: compute identity audit

User handed work to Codex and requested an updated report. GTA and canonical
runtime were not modified. This directory is a separate diagnostic tool.

## Observed result, not a root cause

Probe PID85858, `run/events-85858.jsonl` and `run/counts-85858.json`:
the user explicitly entered the first game scene during this run and reported
sound without visible graphics. Before that transition, the target culling
pipeline identities had been created but had no observed dispatches. After
the transition the SAME identities received indirect dispatch calls:

- CS_MPHAddGPUIRInstances, pipeline139
- CS_MPHCullInstances, pipelines156/167/171/176
- CS_MPHCullBVHMainPass, pipeline181
- CS_MPHCullClusters, pipelines193/209/226/232/237/240

The user-first-scene snapshot contains 21,186 CullBVHMainPass indirect calls;
each of the other listed identities has 2,354 calls. These are CPU encoding
counts, NOT proof of nonzero GPU threadgroups. The dispatch argument values
have not been read by this audit yet. No claim of a fixed black screen.

This directly supersedes the handoff's claims that the game does not call
these passes or disables the culling path. Both scene state and indirect
dispatch coverage matter. Comparing a root parameter's byte offset between
different shaders also does not establish that their bound tables are the
same runtime resource; that requires actual binding/address correlation.

## Measurement coverage and old tool defects

The new tool associates each PSO with its creation function on the returned
object, then tracks that exact object on each encoder. Both ordinary dispatch
variants and indirect dispatch are hooked. It records unknown identities
explicitly; all 2,742,805 observed calls in the pre-transition reviewed
snapshot had known identities. Creation time proximity is never used.

Old `bf_bindless.m` inspection found:
- `hook_compute` stops after its first concrete encoder class (`g_cHooked`).
- `h_setCPS` only updates its associated name if the new PSO is known, so an
  unknown PSO can inherit the previous name. It logs a bind as DISPATCH EDILEN.
- Its creation hooks cover only two synchronous variants; the new tool also
  covers function+reflection and three asynchronous variants.
- Its heartbeat has no process ID and the library loads into Wine helpers;
  repeated zero heartbeat lines alone do not establish missing game work.
- Several old readers use a separate queue after completion and raw buffer
  pointers. Their snapshots cannot automatically be treated as exact values
  at the consumption command, especially for transient heap resources.

These defects do not prove which specific old sample was affected. This run's
direct observation of target dispatches is the decisive correction.

## Controls and side effects

`control/` tests actual synchronous PSO identity, async completion identity,
and all three dispatch selectors. Known GPU atomic result=3, command buffer
status=Completed. Identical positive controls run in the game process and are
marked `test:true`; no helper-process counters mixed into game data.

This audit only observes API calls; it does not patch shaders or add reads to
the game's GPU commands. The runner ended at its 180-second boundary, stopped
its owned game process, and restored the exact pre-run INI bytes. User entered
the scene late in that window; future observation should allow their scene
transition explicitly instead of assuming launch duration defines game state.

## Next concrete measurement

Read the three indirect dispatch dimensions immediately before the identified
culling commands on the GPU timeline, preserving their buffers and state.
Use a known nonzero control and retain a private snapshot until completion.
Do not repeat the old unidentified first-argument or late separate-queue scan.


## GPU argument capture — PID86064

The identity-linked indirect dimensions were read by a small compute kernel
immediately before the original indirect dispatch, in the SAME compute
encoder. The kernel only writes its own snapshot buffer; original PSO and
buffer slots29/30 are restored before the original command. Buffer barriers
are added, so this is a synchronized, instrumented run, not proof that the
unmodified game's synchronization is correct. Each snapshot is retained
and read only after its command buffer completes. No game resource poisoning.

24 game samples completed successfully with the expected marker. Actual
nonzero examples: CullInstances [4,1,1] and [1,1,1]; AddGPUIRInstances [4,1,1];
CullBVHMainPass [29,1,1] and [113,1,1]; CullClusters [1257,1,1] and [1334,1,1].
Other sampled variants have [0,1,1]. Not every variant needs nonzero work.
Therefore the previous all-zero/disabled culling narrative does not hold
for this cutscene. This still does not verify shader outputs or visible
cluster contents at mesh consumption, and is not a graphics fix.

User clarified that the measured phase was a CUTSCENE, later reported actual
gameplay, then closed the game. Only the first two calls of each identity were
sampled, so do NOT relabel these GPU values as gameplay-specific samples.
`user-gameplay-counts.json` is an observation checkpoint of the latest count
file, possibly stale at closure, not fresh GPU argument data. Counts reached
10,593,687 known-identity calls and zero unknowns in the final saved file.

Controls: known CPU arguments [1,1,1] captured; a separate GPU producer first
replaced poison with [3,1,1], the capture observed [3,1,1], and the original
consumer performed exactly3 increments (Completed). This tests GPU ordering
and restoration, not just the decoder. Sources/results: args-control and
args-order-control. Machine game arguments: args-run/argument-summary.json.

User closed the game; do not relaunch without a further need or instruction.
Next useful investigation is the actual culling output / mesh consumer input
in the same scene, using confirmed resource identities and consumption-time
ordering. Do not go back to feature-query guesses or no-dispatch claims.


## Composition follow-up, 2026-09-09

User redirected investigation toward the shared menu/scene image path.
Read-only flag-test audit: proxy/d3d12_proxy.c h_clear, lines129-150, overrides
ALL intercepted ClearRenderTargetView colors with red when BF_RED is set,
then adds white scanline rectangles to every full-target clear when BF_FLAG
is set. It has no RTV-to-resource mapping, swapchain identity filter, or
composition-stage selection. Thus the reported visible crescent/star proves
a modified clear can reach the display, NOT that CS_ComposeUI processed it.
The original flag-run wine log exists but no surviving flag-specific clear
log identifying its ultimate displayed target was found in this inspection.

Historical correction: provenance/compose-registry/compose-4303.json resolves
slot1 as a format90 view of the known presentation copy-source parent. The
saved CS_ComposeUI AIR writes slot1. That establishes a writer; it does NOT
resolve input slots4/5/7. The old prose calling the uniformly-black slot1 an
INPUT and therefore claiming composition is correct is not supported.

New composition reader uses the exact 24-byte GPU descriptor ABI from saved
AIR: slot4 UI, slot5 scene, slot1 output. It reads float4 including alpha on
the GPU, immediately before AND after CS_ComposeUI dispatch, preserving PSO
and buffer30. All game buffers/textures remain unmodified by the reader.
Additional barriers impose ordering; this is a perturbation to disclose.
Snapshot capacity1280x720 each; actual dimensions/marker are written by GPU
and must be checked. Slot7 LUT not captured by this version.

Known 7x5 gradient descriptor selftest passed all pixels and alpha; full-hook
control captured the gradient before and (.2,.4,.8,1) after the original
dispatch, across all three slots. Exact control artifacts under
compose-hook-control. Game probe PID86552 now awaits user-confirmed menu,
then scene sampling via compose-run/request.txt. No game result yet.


### PID86552 first confirmed phase: Press any key (before Animus Hub)

User explicitly distinguished startup prompt, then multi-game Animus Hub,
then Black Flag itself. Do not conflate these states with the game main menu.
The capture's legacy filename prefix `menu` actually means Press any key;
see compose-run/phase-labels.json.

Both before/after command-buffer statuses Completed, dimension markers12345:
slot4 UI1280x720 and slot5 scene896x504 contain ONLY float4(0,0,0,0),
including alpha, at both boundaries. Slot1 output1280x720 has10640 nonzero
RGB pixels before the operation (could be transient prior contents; do not
call this valid image), and becomes exclusively(0,0,0,1) after it.
This is direct GPU sampling through the actual bound descriptor root.
No useful image reaches the two sampled composition inputs in this startup
state. Does not establish the cause upstream, nor validate slot7 LUT or all
other composition variants/states. Await separately identified Animus Hub
and game-scene phases before comparing.


## PID86552 final: startup, Animus Hub and gameplay compared

User-labeled phases in `compose-run/phase-labels.json` are authoritative:
- file prefix menu = Press any key BEFORE Animus Hub
- file prefix cutscene = Animus Hub game selector, NOT cutscene
- file prefix gameplay = user-confirmed Black Flag gameplay

In all THREE sampled states the exact CS_ComposeUI root-table reads report:
UI(slot4)1280x720: all921600 pixels RGBA=(0,0,0,0).
Scene(slot5)896x504: all451584 pixels RGBA=(0,0,0,0).
Both are zero before AND after the original composition dispatch.
Output(slot1)1280x720: all921600 pixels RGBA=(0,0,0,1) AFTER it.
All six command-buffer completion reports are Completed with no error and
all18 dimension/slot markers have the expected12345 value.

Output BEFORE the writer contains varying bits in all three phases. Hub
preview was inspected: patterned colored fragments, not recognizable UI.
The target has not yet been written by this pass and may alias other heap
resources; this is NOT evidence that a valid image is being erased or that
texture layout is corrupt. Read only the live input contents for causality.

Conclusion: in these sampled states no nonzero image was returned from the
two textures bound as composition inputs; black output is consistent with
those inputs. This narrows the investigation upstream of final composition,
or to input descriptor/view/resource access. It does not prove all upstream
rendering is absent, nor a single shared root cause, nor exact descriptor
correctness. A bad view/alias/resource-read path could also give zeros.
The LUT(slot7) and shader sample-vs-read behavior were not separately tested.
Never claim the compositor universally cleared or the root cause solved.

Capture method is discrete snapshots, NOT continuous recording. User asked
to keep recording and was told this limitation; the one gameplay before/after
sample was then taken. User later confirmed gameplay and authorized stopping.
Owned run stopped via stop marker; finished.json reports settings_restored=true.
No runtime/shader replacement persisted, no GTA edits, no new game integration.

Next useful action: trace the actual writers of the UI/scene input resource
identities or compare a GPU write/read through those exact views at their
valid lifetime. Do not return to “culling never dispatches” or the ambiguous
all-target crescent test. Keep stage labels user-confirmed.


## Pool view comparison preparation

D3DMetal binary references newTextureViewPoolWithDescriptor:error:,
setTextureView:descriptor:atIndex:, and copyResourceViewsFromPool. Apple's
local macOS26 SDK MTLTextureViewPool.h confirms these lightweight views return
resource IDs without creating MTLTexture view objects. This explains a gap in
old ordinary-view tracking, NOT proof of a rendering bug.

`pool_map.h` now tracks this path, including pool copies and per-view
format/level/slice/swizzle. Textures are weakly referenced between calls;
selected textures/views are retained for capture. Only relevant-size targets
are retained in metadata; no raw expired texture pointers dereferenced.

`pool_compare.h` compares original pooled descriptor reads against new ordinary
views with the SAME source texture and identical view descriptor. Only the
reader's temporary root/table changes, not the game's composition. Root/table
CPU snapshot is a limitation if updated concurrently; recorded metadata and
GPU dimensions must agree. Original root binding is restored.

Controls passed: pooled known gradient all pixels correct; full hook pooled
vs ordinary105 pixels match the original GPU writer (.2,.4,.8,1). Thus pool
API works in the known sample; no generic pool failure claimed.
Game PID86942 is waiting for user stage confirmation.


## PID97473: pooled and ordinary views return identical empty inputs

User confirmed Press any key in pool-retry-20260909T145758. Three snapshots
(before, after, ordinary view) completed with valid dimensions/markers.
Original pooled and replacement ordinary views of the SAME texture and
identical format/range/swizzle produce byte-identical full snapshot buffers.
Slot4 UI1280x720 and slot5 scene896x504: every RGBA component zero.
Slot1 output after composition: every pixel(0,0,0,1).
Artifacts: comparison.json, menu-{before,after,normal,pool}-97473.*.
This does NOT establish that the source texture is correct or its upstream
writer works. The alternative view path alone does not recover an image in
this sampled state; no generic pool bug or universal access correctness proved.

Resolved source objects at this boundary:
UI texture0x7fb0499611b0, fmt70, heap0x7fb0581472b0 offset9043968;
scene texture0x7fafefc82dc0, fmt115, heap0x7fafeff49870 offset5505024.
Both base mip/slice, identity RGBA swizzle. Next target is writer provenance
for these actual objects, not guessing by dimensions or shader name.
Earlier PID86942 run exited before capture; no result should be attributed to it.


## Render-writer metadata probe prepared

identity_writer.m / writer_history.h adds bounded last-eight-pass metadata
per relevant texture object, normalizing ordinary views through parentTexture.
Records render attachment load/store/clear, actual PSO creation identity and
pipeline bindings. Actual draws counted only for the three direct non-indexed
drawPrimitives variants; zero in this counter does NOT mean no indexed/mesh/
indirect draw. Metal3 renderCommandEncoderWithDescriptor scope only. No GPU
work injected by this metadata extension; existing composition reader remains.
writer-control passed: ordinary view target traced to original texture, known
vertex/fragment identity, one actual triangle, all256 pixels red, Completed.
No game provenance result yet. Previous pool run stopped to relaunch this probe.

Writer run PID97736 is active, awaiting user phase confirmation. There is one
creation-failed event for a CS_DeferredLightCubeMap variant and game.log reports
AGX Failed to materializeAll / exceeded compiled variants footprint limit.
Do NOT call all pipelines error-free in this run. This is not established as
the original black-screen cause; the previous comparison run already had
black inputs without this particular failure. Preserve it as a run limitation.


## PID97736 user-confirmed Press any key: input writer identities matched

writer-run/menu-pool-97736.json resolves UI poolRID1073637 to base texture
0x7fed1a852a20. Its ordinary render view0x7fed3b14b6e0 appears in repeated
passes with VS_Phoenix/PS_Phoenix bound; same histories contain
executeIndirectStep2Render. First pass clear/store, subsequent load/store.
No direct nonindexed calls captured on UI; indexed/ICB paths are NOT covered
by that counter. Do NOT infer no draw. Eight-pass history is bounded, not
a complete list of writers including compute/blit or all lifetime events.

Scene poolRID1073638 resolves base0x7feccbd21700, view0x7feccbd25a50.
Matched render passes bind VS_RenderFullScreen /
PS_TemporalAADisabled_CopyLastFrame, then VS_ShadeVertex / PS_ShadePixel.
Each has one actual intercepted drawPrimitives ... baseInstance call.
Both have load/store, rasterization enabled and full color0 write mask.
Those properties do NOT establish fragment execution/pixel correctness.

All before/after/ordinary GPU readback statuses Completed, markers correct;
UI and scene pixels still zero, output after/ordinary black alpha1.
The writer metadata narrows the actual attachment chain; no fix yet.
Next targeted boundary is the PS_Phoenix attachment after its producing pass
or the scene PS_ShadePixel pass, with valid same-CB readback and matching
resource lifetime; not another blind scan or zero-call inference.

Correction on the compilation warning: HANDOFF earlier records materializeAll/
variants-footprint failures in baseline and frame-inspect too. This warning
is NOT new to writer instrumentation and must not be attributed to it.
Game remains open in owned runner20896/PID97736; this phase's capture is done.
No additional samples happen unless a new request phase is explicitly set.


## Writer-boundary pixel probe prepared

identity_writer_pixels.m: same pool-resolved UI/scene base objects are marked
at a confirmed composition sample. Subsequent first3 UI/first2 scene render
passes on those exact objects are sampled immediately AFTER endEncoding in
the SAME command buffer; Load passes also sampled immediately before creation.
Only stored, single-sample, mip0/slice0/depth0 attachments with fmt70/115.
Blit bytes/row respects4/8 bytes respectively. Signal/wait events serialize
the injected read before subsequent alias reuse. Added synchronization may
change timing; it does not validate the game's original synchronization.
Textures/buffers/events are retained through completion; output inspected
only after Completed. No pixel or shader replacement. Once quotas encoded,
writer-result composition snapshot captures the downstream state.

writer-pixels-control passed both formats using TWO distinct placed textures
at the SAME heap offset: original red capture, overwrite alias green, original
blue capture. All4 captures x128 pixels exact red/blue, Completed. This tests
format decoding and avoids falsely reading final contents for earlier writes.
Prior writer-run PID97736 exited0 naturally and settings_restored=true.


## PID97939 writer-boundary results: already zero immediately after writers

User confirmed Press any key. UI exact base0x7fdc61f592b0: three consecutive
PS_Phoenix-associated render passes, all921600 pixels RGBA(0,0,0,0) AFTER
each pass; Load-before snapshots also allzero. Scene base0x7fdc14891690:
PS_TemporalAADisabled_CopyLastFrame then PS_ShadePixel, all451584 pixels
RGBA(0,0,0,0) before/after both. Nine readbacks Completed; no nonfinite values.
See pixel-analysis.json for original metadata/identities. Downstream
writer-result composition inputs remain zero, output black alpha1.
No populated image was observed between these sampled writers and consumer.
This is NOT proof no fragment executed: indexed/ICB coverage still incomplete.

Next controlled experiment targets ONLY PS_Phoenix + RGBA8 render pipelines:
replace fragment with constant green, preserve vertex/depth/blend/state.
Earlier broad red-fragment tests changed presenter and depth/blend too, so
do not answer this resource-specific question. Positive control renders all
256 pixels green with the targeted pipeline. No original binaries changed.


## PID98202 green experiment INVALID for sampled target

User at Press any key, no visible change. Zero boundary readbacks again, BUT
actual sampled render histories still name PS_Phoenix, not bf_phoenix_color.
Twelve PS_Phoenix format70 creation requests were replaced; that does NOT
prove the sampled writer used any of them. Therefore cannot infer constant
fragment failure or rasterization failure. Format70 pipeline filter may be
too narrow; actual render attachment format does not identify PSO's descriptor
format. Retry removes only that filter, retains PS_Phoenix name restriction
and logs pipeline descriptor format. Mandatory bound-shader verification
before interpreting pixels. No game result claimed from this invalid test.


## PID98357 targeted green retry

Removed format70 filter. Actual sampled UI PSO metadata now identifies
bf_phoenix_color with original format0=Invalid. Thus replacement binding
is confirmed this time. All three UI after-pass snapshots remain zero.
Does not prove no fragment execution: absent color attachment format0,
depth/stencil/scissor/ICB state or output mapping could prevent writes.
Fourteen replacements with formats0/70. User reports no visible change.
Next one-variable experiment keeps ORIGINAL PS_Phoenix, vertex/depth/blend
and changes only Invalid colorAttachment0 to70 for raster-enabled Phoenix
pipelines. This matches the measured attachment but may be incompatible
with a special runtime pipeline mode; record failure rather than force it.
format-control proved Invalid->70 adapter with known original red fragment,
all256 pixels red. No persistent runtime/game-file modification.


## PID98677: USER-CONFIRMED PARTIAL UI RECOVERY — SAVE THIS BUILD

Single mutation: for raster-enabled PS_Phoenix pipeline descriptors whose
colorAttachment0 format is Invalid(0), set only that format to70 RGBA8Unorm.
Original vertex/fragment/depth/blend remain. Two affected descriptors had ALL
eight original formats0. Actual sampled bound PSOs now metadata format70.
UI pass1 after:17367 nonzero RGB pixels,420 unique values; pass2 outputs black
alpha127; pass3 after:16456 nonzero RGB pixels,570 unique values. All Completed.
Scene inputs still zero. This is a partial behavioral improvement, not solved
gameplay or proof all PSOs should be forced to70.

User screenshot15:23:58 explicitly confirms a recognizable Online Service
Error dialog with imperfect/incomplete glyphs. Saved user-confirmed-ui.png.
Do not label this Press any key: automatic sample phase was unconfirmed,
and actual user screenshot shows service error. Error may previously have
been invisible; this experiment does not prove newly caused network failure.

Exact source+dylib checkpoint at target-format-run/confirmed-ui-fix/ with
sha256.json. Runtime remains process-only, no game payload edits, no canonical
launcher persistence yet. Current game PID98677, runner84140. Need user to
dismiss dialog / navigate before next phase. Remaining text corruption and
3D scene must be handled separately; keep this progress, avoid reverting
to generic fragment/rasterization claims.

User subsequently provided15:24:42 screenshot of Animus Hub Memories list:
recognizable menu entries/labels, incomplete glyphs and missing background.
Saved user-confirmed-animus-hub.png. Triggered legacy phase cutscene for
composition snapshot; this label means Hub, NOT a cutscene.

Hub downstream capture Completed: UI115021 nonzero RGB pixels,1636 unique
float4 values; composed output64933 nonzero RGB pixels,830 unique values;
scene still zero. hub-summary.json. Awaiting user Black Flag gameplay stage.


## Gameplay screenshot + source identities PID98677

User screenshot shows compass/objective HUD over black world. Saved
user-gameplay-hud.png. Pool metadata confirms UI1512x945 fmt70 and
scene1058x662 fmt115. UI pipeline format70 (fix active); two scene writer
pipelines PS_TemporalAADisabled_CopyLastFrame and PS_ShadePixel STILL0.
IMPORTANT: fixed compose reader has1280x720 per-pane capacity. At1512x945
it only samples a cropped UI region. Do not analyze it as full UI image or
claim all-pixel checks; dimensions exceed capacity. Scene1058x662 fits.
Next experiment derives missing color formats from actual render attachments
at bind time, preserving original shaders. This is a targeted format repair
of affected pipelines, not proof every graphics state is correct.


## Attachment-derived scene repair prepared

identity_repair.m keeps proven Phoenix creation-format fix. Additionally
retains copied original render pipeline descriptors. On setRenderPipelineState
inside an identified render pass, only raster-enabled fragment pipelines with
ALL original color formatsInvalid and a real color attachment receive a
cached variant with formats taken from all8 actual pass attachments.
Original shaders/depth/stencil/blend preserved. Other pipelines unchanged.
Failures log and fall back. This does not change pipelines embedded directly
in ICBs; that remains a coverage limit. Smaller passes without relevant-size
attachments are outside current recorder.
Controls: known RGBA8 target all256 pixels red; two HDR115 MRT targets red
and blue,256 pixels each. Both Completed, repaired bound identity verified.
Partial UI working source checkpoint remains preserved before this experiment.


## PID99102 initial automatic sample: scene no longer zero, NOT gameplay proof

161 attachment-format repair variants reported in first minute, zero repair
failures. Original shader names preserved; formats include92/25 and MRT
70,70,71,70,92. Sample scene115 all451584 pixels nonzero RGB,208874 unique
values, no nonfinite floats. Decoded scene-preview.png is smooth gray field,
NOT recognizable world/character. Do not claim rendered scene on nonzero
counts alone. UI also contains nonzero text pixels. Nine snapshots Completed.
User state confirmation/Black Flag transition awaited. Checkpoint sources and
dylib preserved under attachment-repair-run/checkpoint with sha256.json.


## USER VIDEO: REAL WORLD AND CHARACTER VISIBLE, THEN CORRUPTION

147.497s screen recording15:30:07 reviewed using4-second contact sheets and
detailed frames120/126/130/136/140 seconds. At~120-136s recognizable animated
character, ship deck, ropes, explosion and changing viewpoint/objective
distance are visible. This is independent user-visible evidence of world
rendering beyond menu/HUD. Severe blown-out whites, wrong shading/cutout-like
patches and imperfect glyphs persist. By140s output is magenta/dark repeated
blocks; do NOT call stable/playable success. No root cause for these remaining
artifacts established; do NOT infer memory layout from block appearance.
Evidence frames and review.json at attachment-repair-run/user-video-evidence.
Do not confuse earlier smooth-gray startup sample with gameplay evidence.


## User clarification: blind first-launch brightness/contrast calibration

User says initial calibration may have been set incorrectly while screen
was black. Pause graphics changes and verify settings first. Current INI
HDR=1 but no readable brightness/contrast/gamma keys. Options.save9894 bytes
is binary, not safely editable by guessed offsets. Options and autosave
backed up separately in calibration-backup with hashes; originals unchanged.
Do not reset all options or delete autosave. Next launch is same image-producing
identity_repair.dylib, no new rendering experiment or automatic GPU snapshot.
User should inspect in-game image calibration values; normal runner still
restores pre-run INI on exit, so intentional calibration INI changes must be
explicitly preserved if needed. Options.save not automatically restored.


## User-authorized Options-only reset

User explicitly requested resetting Options rather than preserving preferences.
Game stopped first. Only ACBlackFlag[Options].save moved to
options-reset-backup (reversible); AutoSave01 SHA256 checked unchanged.
INI/HDR configuration left unchanged to isolate saved calibration/options.
Relaunch uses same identity_repair.dylib, automatic snapshots disabled.
First-launch options/calibration may appear. Do not restore the old Options
automatically, or claim brightness fixed before user confirmation.


## After Options reset: user screenshot evidence

User calibration screenshot: brightness5/contrast5/HDRoff. Magenta blocks
and incomplete letters still present at defaults. Later gameplay screenshots
show greatly reduced white clipping, but missing/incorrect surfaces persist.
User explicitly clarifies clean beach is a VIDEO cutscene; do not count it
as real-time rendering validation. Current remaining: menu/subtitle glyphs
and background artifacts, gameplay surface/shading corruption.

state-audit-run preserves identity_repair behavior, adds metadata only for
actual pass depth/stencil/color formats, PSO formats/blend and bound depth
state/scissor/viewport. Positive control validated depthAlways/scissor16 and
original256 red pixels with color repair. Does not change depth/blending.
User gameplay confirmation awaited.


## 2026-09-09: state audit, input audit, scoped mesh repair

PID2405 state-audit-run exited0. User screenshot20:08:49 confirms the same
remaining gameplay defects.196 unique pass records. Known raster pipeline
depth/stencil formats match targets; no basis for arbitrary depth changes.
Six unknown bound pipelines motivated creation coverage inspection.

Native descriptor copy selftest preserved all8 nondefault formats/blends/write
masks. Input-audit-run PID2809 captured500 input descriptors,0 original/copy
mismatches;359 first-attachment blends enabled,141disabled. Thus not ALL
input pipelines lack blending: the earlier all-disabled observation applied
to BOUND recorded pipeline states. Precompiled inputs are not the same set.
No claim yet that the game intended blending for any particular bound draw.

Mesh creation hook control passed (real compiled mesh PSO). Actual
MS_MPHRasterize/PS_MPHRasterize bound with8colorformats0 to targets[53] or
[53,92]. Previous repair did NOTcover mesh descriptors.

New identity_mesh_repair.dylib preserves established raster repair and adds
attachment-derived format repair ONLY for MS_MPHRasterize, raster-enabled,
fragment present, all8originalcolorformats0, at least1actualcolortarget.
Original mesh/object/fragment shaders, blend/depth/sample properties preserved.
Known mesh control renders256whitepixels/Completed after formatrepair;
existing raster control still256redpixels/Completed. No game outcome yet.

Source files mesh_repair.h,input_mesh_repair.h,writer_mesh_repair.h,
identity_mesh_repair.m,run_mesh_repair.py. No production binary or GTA changes.

Mesh-repair-run PID2949:4real MS_MPHRasterize variants repaired,0mesh
repair failures. GPU composition+writer reads completed. startup-crops.png
shows Online Service Error dialog with still-defective glyphs, black scene
behind it. This is NOT gameplay validation; UI cannot be advanced through
CUA because Wine is not an enabled app (getApp failed; listApps has noWine).
Do not synthesize keyboard input through an alternate interface. User away
at dinner. New mesh extension remains experimentally unconfirmed in gameplay.
Complete source/binary checkpoint and hashes saved in mesh-repair-run/checkpoint.


## Mesh extension gameplay verdict, user-confirmed phases

PID3477 mesh-gameplay-review-run: user20:39:43 says gameplay unchanged.
20:42:05 pause screen magenta/black; both screenshots saved. Experimental
mesh extension has NO demonstrated visual benefit. Do not promote as fix.
Pause (request token menu) and gameplay snapshots both completed status4.
In sampled1280x720 crops of actual1504x917/918textures, all float values finite.
Pause: scene slot5 already contains magenta-black pattern (617472magenta
pixels), UI slot4 does not; output contains samepattern. Gameplay: UI slot4
already has missingglyphparts; scene slot5 already has broken silhouettes/
surface holes. Final composed image retains them. Both previews inspected.
This localizes visible defects BEFORE final UI/scene composition, but does
not identify original cause or prove UI/world defects share one cause.
Do not infer memorylayout or failedblending solely from appearance.


## 2026-09-09: exact pipeline identity chain and Phoenix template experiment

Pipeline-chain-run PID4064: chain IDs link original descriptor, submitted
descriptor, bound PSO and first observed direct/indexed draw. Initial178bound
chains had0blend/write-mask changes due to our repair; all178sources already
had blendingdisabled. Thus our format-only copy is not dropping blending.
Reference creation inputs with blendingenabled are different PSOs. HOWEVER
Phoenix exact retained vertex/fragment function identities recur in prior
nonzero-format PSOs. Matching pass formats,depth/stencil,samples,raster and
alpha coverage yields6of8bound Phoenix chain cases with one distinct prior
color state;2are ambiguous and must be skipped (phoenix-candidates.json).
Matching functions alone does NOT prove game intended that state's reuse.

Controlled experiment identity_template_restore.dylib: Phoenix-only, original
allcolorformats0, find unique earlier colorstate from exact function objects
and matching actual8formats/depth/stencil/samples/raster/alpha settings;
copy only colorattachments onto current descriptor. Retains original
vertex/fragment functions and all noncolor state. Multiple candidates with
differing colors means nochange. Existing rasterformatrepair remains fallback.
No meshextension: previous gameplay test showed no visible benefit.

Control passed actual256pixels from2translucent layers (~191red,128alpha),
indexed+directdraws, Completed, and deliberate ambiguous template rejection.
Game effect pending. New sources template_restore.h,writer_template_restore.h,
identity_template_restore.m,run_template_restore.py,template-restore-control.m.
Run directory template-restore-run. No permanent runtime, save or GTA edit.


## CONFIRMED PARTIAL FIX: Phoenix glyph rendering

User explicitly says glyphs fixed in template-restore-run PID4276.
menu-after-4276 GPU snapshot Completed4 visually inspected: actual screen
is Animus Hub; BLACK FLAG RESYNCED, EDWARD, SHADOWS,ODYSSEY,subtitlelabels
are intact, unlike prior screenshots. user-confirmed-output.png is a
1280x720crop of actual1504x917 output, not entire window. Grey background
and incomplete character art remain; this is not complete menu/gameplay fix.
Six template-restored events before confirmation,0template-failed.
Checkpoint source/binary sha256.json stored under template-restore-run/checkpoint.
Current run4276 runner34095 remains active. Keep confirmed template restore
for subsequent work; do not overwrite checkpoint. Await gameplay/subtitle
and pause screen comparison; no claim world surface defects improved.


## Phoenix confirmed in gameplay/subtitles; scene extension started

User confirms world unchanged but glyphs and subtitles correct. Pause screenshot
21:05:16 saved template-restore-run/user-pause-confirmed.png: Resume/Load/
Options/Quit menus readable, pink/black background persists. Preserve this
confirmed Phoenix checkpoint. PID4276 stopped via owned runner, INI restored.

New PID4572 runner76178 scene-template-run uses identity_scene_template.dylib.
Only change vs confirmed template restore: allow non-Phoenix raster fragment
pipelines to participate in the same unique exact-function template mechanism.
Originalallzeroformats required; actual8colorformats,depth/stencil,samples,
raster/alpha state matching required; ambiguous colors rejected. No new
shader/depth/geometry override. Translucentpixels+ambiguitycontrol passed.
Game world result PENDING; user asked to enter gameplay and compare.
No GTA/save/production runtime changes.


## USER-CONFIRMED SCENE IMPROVEMENT — preserve this checkpoint

scene-template-run PID4572: user screenshots21:09:07 Hub and21:09:53
gameplay confirm character face/clothing visible in Hub and more coherent
character in gameplay; user explicitly says gameplay better. Visible large
ship/environment holes remain. Glyphs remain readable in supplied images.
This is a partial scene fix, NOT complete compatibility/playability.
352template restorations,0template failures at confirmation.
Checkpoint source+dylib: scene-template-run/confirmed-partial-fix/sha256.json.
User images and verdict stored in run directory. Gameplay composition
capture requested with user-confirmed phase. No new mutation after verdict.
Keep prior Phoenix-only checkpoint too; future experiments build on this
confirmed scene state and must not claim all remaining errors share a cause.


## 2026-09-10: original attachment source probe prepared; execution environment blocked

Confirmed scene-template checkpoint hashes all match. Owned prior run4572
finished with exit0 and settings_restored=true. No game started this turn.

Static disassembly identifies SetupAttachmentDescriptor at0x113813 in the
BF-scoped D3DMetal4.0b2. A zero packed-format byte OR index>=staticCount
skips format AND blend AND write-mask setters for that target. This code
path explains a possible common mechanism, NOT the live root cause yet.
Read-only source_state.h hooks colorAttachments at two build-specific caller
return addresses (mesh0x112ec6, raster0x113265), decodes original static
state and packed dynamic formats, attaches them to pipeline-chain metadata.
No D3DMetal binary bytes changed. Correct caller-frame layout remains to
be positively validated; these offsets must never be reused for another build.

New source-state-decode-control passes synthetic packed formats, all96state
bytes, inaccessible-pointer rejection; does NOT validate live ABI/GPU.
New identity_source_state.dylib compiles. Existing confirmed template repair
remains its fallback; original-state automatic repair is NOT implemented.

Current environment cannot create a Metal device: standalone x86_64 probe
(without any diagnostic hooks/game) prints device=NONE, exits2. Existing
full-control abort occurred before source hooks installed. Process inspection
via ps is also EPERM in current restricted session. Sandbox restrictions are
consistent with this, but device=nil alone does not prove the OS-level cause.
Do not rerun the game or use another launching surface to bypass restrictions.
Added explicit failure reporting instead of abort in the new constructor;
new runner refuses when process inspection or standalone Metal preflight fails,
before game launch/settings changes.
Evidence: source-state-control/environment-check.json, metal-availability.m.
Next: restore permitted GPU/process execution, validate getter/caller ABI with
a positive control, then one original-vs-submitted-state startup trace. Only
apply a direct-source repair if the original values and missing transfer are
validated. GTA, game payload, saves, and production runtime untouched.


## 2026-09-10: access restored; direct original-state repair in game

Standalone Metal device Apple M5 and shader compilation now pass. Full
source-state-control passes actual GPU translucent pixels AND synthetic x86
caller-stack fixture dispatched through real objc_msgSend into the same hook.
Fixture accepting return address is compiled only into standalone control.

Read-only source-state-run PID15905 captured original static settings and
packed dynamic formats. Live cross-validation: 30612 eligible
source/native target pairs, 0 mismatches across format, blend,
factors, operations and write mask. 419 bound original-all-zero
pipelines have positive staticCount and all8packedFormats zero. These skip
SetupAttachmentDescriptor's setters; this is observed metadata, not proof
that every remaining visual defect has this cause. Process stopped via owned
runner; INI restored. source-analysis.json contains evidence.

New source_restore.h restores THIS pipeline's own recorded color state at
bind with actual pass formats. Requires original allzeroformats, zero dynamic
formats, staticCount1..8, validated enum ranges, raster+fragment. Targets
beyond staticCount write no channels. Shader/depth/noncolor state preserved.
Caches per sourcePSO+formats. Unknown/failing cases retain confirmed template
fallback. Standalone source-restore-control passes real two-layer blended
pixels, live hook stack fixture, and existing ambiguity control.

Active source-restore-run PID16081, shell session74092, owns1800s runner.
175source restorations and0source failures at early inspection. User says
menu OK and is entering gameplay; this is menu confirmation only, full
gameplay/pause verdict PENDING. No permanent runtime or GTA/save edits.
Sources identity_source_restore.m, writer_source_restore.h, source_restore.h,
source_state.h, source_state_decode.h, pipeline_chain_source.h,
run_source_restore.py, source-restore-control.m. Best previous checkpoint
scene-template-run/confirmed-partial-fix remains byte-for-byte unchanged.


## Original-source restoration: video reviewed, mesh path added (verdict pending)

source-restore-run user video00:41:15, 59.8s, four sampled frames saved
user-video-contact.png: character/loading area coherent; sea and gameplay
visible, but some ship surface defects remain. User confirms menu OK.
Pause00:42:34 still purple/black blocks (user-pause.png). Preserved complete
source/dylib checkpoint source-restore-run/confirmed-partial-fix/sha256.json.
This is another PARTIAL improvement. PID16081 stopped, INI restored.

New source-restore-mesh-run PID16359 shell24839 adds same own-state restore
to newRenderPipelineStateWithMeshDescriptor:options:reflection:error:.
Includes mesh colors/owner/source fields in chain metadata; uses native
mesh descriptor copy and mesh creation call. Standard raster path unchanged.
Controls: mesh two-layer alpha blend on256pixels, standard direct draw.
Live mesh original/native comparison: 15 active pairs, 0 mismatches.
Six actual mesh restorations observed:4MS_MPHRasterize variants and2
irconverter_domain_shader_triangle_passthrough variants (70,30). No source
restore failures. The latter path was outside old MPH-only mesh experiment.
Visual verdict requested for pause and gameplay; do not claim improvement yet.

Correction to prior rough call-site labels: standard raster getter return is
0x112ec6; mesh getter return0x113265 (labels were reversed in an earlier note).
The code always listened to both; the earlier label error did not alter data.
No production runtime, GTA, game payload or save edits.


## 2026-09-10: pause corruption localized; scoped workaround awaiting verdict

User confirms source-restore-mesh: other visual defects fixed, purple pause
background remains. This partial successful state is preserved under
source-restore-mesh-run/confirmed-partial-fix/sha256.json. Prior PID16359
finished exit0/settings_restored.

New pause-boundary-run PID16940 keeps exact source+mesh fixes; only scene
readback quota2->4. User explicitly confirmed paused and held screen.
All8scene before/after readbacks Completed4. Sequence on exact target:
1 PS_TemporalAA yields coherent scene,0magenta pixels.
2 ShadePixel preserves scene,0magenta pixels.
3 PS_ShadePixel changes scene to checker pattern,1020768magenta pixels.
4 next temporal pass again produces coherent scene.
This is same-command-buffer producer boundary evidence, NOT an inference
from shader names or missing events. Inputs to PS_ShadePixel not diagnosed.

New pause_overlay.h workaround disables color writes only for PS_ShadePixel
with VS_ShadeVertex, format70single target, no depth/stencil,sample1, full
writeMask and observed srcAlpha blend4/dst5 for RGB and alpha. Original
shader retained, pipeline copy cached; other passes unchanged. This omits
the faulty overlay's visual effect rather than fixes its underlying input.
Scope uses shader names+state, not unique function hash: other contexts with
the same signature may also lose that overlay. Must assess visually.

Control: matching signature preserves256green background pixels; different
blend state draws256magenta pixels normally. Both Completed.
pause-boundary owned process stopped and INI restored. Active new run
pause-workaround-run PID17098 shell53998. User asked to compare pause
background; verdict PENDING. Sources identity_pause_workaround.m,
writer_pause_workaround.h,pause_overlay.h,run_pause_workaround.py,
pause-workaround-control.m. No production runtime/GTA/payload/save changes.


## 2026-09-10: USER-CONFIRMED normal SDR + HDR; GornHub profile installed

CURRENT ENTRY: platform/tools/black_flag.py -> compatibility/v2/BlackFlagCompatibility.dylib.
User confirmed diagnostic SDR pause workaround, then lean v1 normal runtime:
"müthiş cano her şey". HDR enabled by user brought pink pause overlay back.
HDR capture pause-hdr-run/menu-pool-17951.json identifies scene target format115,
PS_ShadePixel + VS_ShadeVertex with the SAME observed blend4/5 RGB+alpha,
writeMask15, single target, no depth/stencil, sample1. Workaround now accepts
format70 OR115, all other signature restrictions retained. HDR GPU control
preserves all256 background pixels for matching state, altered blend state
renders normally. This is still suppression of a faulty overlay, not a repair
of that shader's underlying input/algorithm.

User confirmed v2 HDR: "düzgün cano eline sağlık". Live HDREnabled=1 and v2 loaded
verified. Pause HDR diagnostic PID17951 stopped via owned runner, finished.json
confirms INI restored. Normal detached PID18266 currently left open for user.
No timed shutdown, no framebuffer dumps, no per-frame diagnostic recording.
No automatic settings resets. No game payload, save or GTA runtime changes.

Lean module includes own-source attachment state restoration on raster AND mesh,
prior fallback restoration and narrow pause workaround. manifest.json pins
module and BF-specific D3DMetal4.0b2 hash because offsets are build-specific.
Do NOT update renderer blindly. v1 preserved as confirmed SDR checkpoint;
pause-workaround-run/confirmed-fix preserves successful diagnostic source/build.
v2 manifest and live-status-validation.json record latest evidence.
Known scope: repair tracks targets width400..1600,height200..1000 (except controls).
Higher resolutions and long gameplay sessions are NOT yet verified. Same-name,
same-state overlay elsewhere may also be suppressed. Do not claim all-game proof.

GornHub profile installed at ~/Library/Application Support/GornHub/Games/
black-flag-resynced.json. Launch/check use black_flag.py, separate BF prefix,
no companions. Live backend reports running, exact stop target PID18266.
Duplicate launch attempt rejected as already open. No actual stop was performed
for hub verification; end-to-end clicking Oyna/Kapat remains untested this turn.
Existing GTA profile SHA256 unchanged (see v2/live-status-validation.json).

Generic Runtime/session.py now recognizes Wine re-exec basename-only .exe
processes, requiring resolved cwd within this prefix drive_c AND matching local
executable file. Original absolute Windows path behavior retained. Added real
snapshot-path regression tests incl outside-prefix/missing-file/symlink escape;
all17 ownership tests pass. Installed and build app helpers updated, both code
signatures verified. Running GornHub need not close; Cmd-R refreshes profiles.
Normal launch is detached and preserves HDR/preferences; runtime hash preflight
is read-only. For future work start from compatibility/v2, NOT old experiments.

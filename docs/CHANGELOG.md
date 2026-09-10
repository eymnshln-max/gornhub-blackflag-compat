# Release history — 10 September 2026

## v4 — island terrain correction (current, user confirmed)

After reaching the island, the player reported recurring rainbow-colored and spiky-looking ground while Edward and the HUD remained largely coherent. Reducing the quality preset did not consistently eliminate it. Screenshots alone could not distinguish malformed geometry from corrupt surface shading, and the reported 6/12 GB memory gauge did not prove memory exhaustion.

Review found that v3 only associated repair metadata with render passes whose color textures measured 400–4096 pixels wide and 200–2160 high. That display-oriented rule also excluded offscreen targets from recovery of their own original attachment state.

The v4 patch makes two changes:

- Track every render pass with a color target and permit exact per-pipeline original-state restoration regardless of target dimensions. The existing validity checks still apply to the captured state. The template/format fallback and pause-overlay suppression retain their previous size restriction.
- If decoding fails at a recognized D3DMetal source-state call site, clear the associated record instead of leaving a previous record available for reuse.

The player confirmed that the terrain corruption disappeared with the combined patch. We did not isolate the two changes in separate gameplay runs, so this confirms the combined fix at the observed location rather than uniquely identifying a causal change. Full-campaign and other-machine behavior remain unverified.

A production-activation 16×16 mesh control verifies two-layer alpha blending outside the former minimum dimensions; SDR/HDR matching and nonmatching overlay controls passed. These controlled tests complement, rather than replace, the player's terrain confirmation. A logging-only terrain audit was prepared but never launched, and supplied no evidence.

The pinned renderer, game files, saves, localization and graphics preferences were not modified by this graphics fix. Current launcher selects v4. v3 and v2 remain available as checkpoints.

## v3 — higher-resolution support (preserved)

Expanded the earlier 1600×1000 maximum target gate to 4096×2160 while retaining its 400×200 minimum. The owner confirmed 1920×1200 High and subsequently used 2560×1600. Production-filter SDR/HDR controls covered 1512×945, 2560×1600 and 3024×1964. Black Flag's Wine prefix separately enabled RetinaMode; the repository launcher does not provision that registry setting.

## v2 — original published private checkpoint

Original raster and mesh attachment-state restoration, readable text, visible opening gameplay, and the scoped SDR/HDR corrupt-pause-overlay workaround. See the illustrated [case study](CASE_STUDY.md) for the initial investigation.

## Local integration notes

The owner separately installed a third-party Turkish translation and confirmed Turkish in-game text. It is not part of this graphics mod; its payload, installer and saves are not redistributed here. The earlier local item-giver investigation is likewise not included as a supported feature of this repository.

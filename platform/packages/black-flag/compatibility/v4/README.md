# v4: offscreen original-state restoration

Original per-pipeline source-state restoration now applies to color targets of any size. The old display-sized gate remains for the inferred template/format fallbacks and pause-overlay suppression. No shader/resource payload is changed. A failed matched source-state decode clears stale associated state instead of reusing it.

The 16x16 offscreen mesh GPU control exercises production activation without BF_COMPAT_TEST and verifies two-layer alpha blending. Existing SDR/HDR overlay controls pass. These controls test the repair mechanism; the terrain result is recorded below. v3 is the preserved rollback. Renderer remains pinned.

The recurring island terrain corruption disappeared with v4 (2026-09-10). This is location-specific gameplay confirmation, not full-campaign validation.

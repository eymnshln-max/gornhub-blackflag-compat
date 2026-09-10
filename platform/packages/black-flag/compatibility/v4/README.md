# v4: offscreen original-state restoration

Original per-pipeline source-state restoration now applies to color targets of any size. The old display-sized gate remains for the inferred template/format fallbacks and pause-overlay suppression. No shader/resource payload is changed. A failed matched source-state decode clears stale associated state instead of reusing it.

The 16x16 offscreen mesh GPU control exercises production activation without BF_COMPAT_TEST and verifies two-layer alpha blending. Existing SDR/HDR overlay controls pass. These controls do not prove terrain is fixed; user gameplay validation pending. v3 is the preserved rollback. Renderer remains pinned.

User subsequently confirmed that v4 fixed the observed island terrain corruption (2026-09-10). This is location-specific gameplay confirmation, not full-campaign validation.

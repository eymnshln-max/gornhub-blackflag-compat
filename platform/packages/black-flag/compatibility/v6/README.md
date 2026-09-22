# v6 — Cached hook lookups

Retains v5 rendering repairs and 4% presentation zoom. Adds bounded per-thread caches for original method resolution and repeated hook installation. A shared atomic epoch invalidates inherited lookups after new hooks are installed. Removes discarded source-state diagnostic dictionary copies. No graphics settings or resource grants.

Validation: inheritance/cross-thread invalidation and mesh/offscreen/pause/HDR/resolution GPU controls passed. A 200,000-call lookup-only microbenchmark measured 0.130472s before versus 0.003094s cached; this is not an FPS measurement. The full v6 launch stack subsequently reached one week / 14 hours of gameplay at approximately 40–45 FPS. The isolated FPS contribution of caching remains unmeasured.

Installation and rollback: see [the current installation guide](../../../../../docs/INSTALLATION.md). The repository preserves older v2/v3/v4 packages; v5 is not included.

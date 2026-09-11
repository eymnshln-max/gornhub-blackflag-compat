# Evidence index

Snapshot created 10 September 2026. The report is English; historical primary logs preserve their original wording and intermediate conclusions.

## Working project

Paths in the original investigation refer to a private working installation. Local home/workspace paths in the preserved logs have been replaced with placeholders.

| Delivered item | Original location / role |
| --- | --- |
| `platform/packages/black-flag/compatibility/v2/` | `platform/packages/black-flag/compatibility/v2/`: final source, controls and pinned manifest; proprietary renderer/game binaries excluded |
| `platform/tools/black_flag.py` | `platform/tools/black_flag.py`: normal detached launcher |
| `platform/tools/black_flag_runtime.py` | `platform/tools/black_flag_runtime.py`: BF-only environment |
| `GornHub/Runtime/session.py` | `GornHub/Runtime/session.py`: exact process ownership and lifecycle |
| `GornHub/tests/test_session.py` | `GornHub/tests/test_session.py`: preserved in its original relative layout; runnable with the command in the code guide |
| `evidence/investigation-log.md` | `platform/packages/black-flag/diagnostic/identity-audit/RESULTS.md`: chronological measurements, corrections and user verdicts |
| `evidence/readback-validation.md` | `platform/packages/black-flag/diagnostic/readback-check/RESULTS.md`: pixel-format, aliasing and hook validation |
| `evidence/source-analysis.json` | `identity-audit/source-state-run/source-analysis.json`: 30,612 comparisons and affected pipeline records |
| `evidence/hdr-pause-capture.json` | `identity-audit/pause-hdr-run/menu-pool-17951.json`: live HDR resource and writer metadata |
| `evidence/hdr-diagnostic-finished.json` | `identity-audit/pause-hdr-run/finished.json`: owned diagnostic shutdown and INI restoration |

## Visual provenance

All visual assets are actual user screenshots or frames from user recordings. None are AI-generated. The historical investigation screenshots below are preserved because they show distinct stages of the repair; the latest finished result is kept once in the README.

| Asset | Provenance / stage |
| --- | --- |
| `01-first-ui.png` | `identity-audit/target-format-run/user-confirmed-ui.png`: first recovered service dialog, incomplete text |
| `02-hud-without-world.png` | `identity-audit/target-format-run/user-gameplay-hud.png`: HUD over a black world |
| `03-readable-text-pink-pause.png` | `identity-audit/template-restore-run/user-pause-confirmed.png`: correct text, corrupt pause background |
| `04-partial-world.png` | Desktop `Screenshot 2026-09-09 at 20.03.41.png`: intermediate world rendering defects |
| [Current state of the game](../README.md#current-state-of-the-game) | Latest user-supplied screenshot; canonical final-state visual for this repository |

## Scope of preservation

This archive is documentation, selected primary evidence and our code. It does not duplicate the full installed game, multi-gigabyte GPU captures, every experiment, saves or account files. Earlier source/checkpoint bundles remain in the working project under `identity-audit/target-format-run`, `template-restore-run`, `scene-template-run`, `source-restore-run`, `source-restore-mesh-run` and `pause-workaround-run`.

The source and compiled dylib match the tested package manifest. Full recordings and GPU captures remain local. Private repository packaging does not imply a new test on another machine.

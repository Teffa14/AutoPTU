# Career battle transition performance notes

The visible arena transition must block only on work required to render the featured match.

Before this slice, the final decision request generated the featured tactical battle, generated every non-broadcast calendar result, applied season progression, built the next season, persisted all transcripts, and only then returned to the browser.

The new pipeline is:

1. Commit the final decision and immutable schedule.
2. Generate and persist the featured tactical transcript.
3. Return the featured transcript to the browser and enter the arena.
4. While the replay is running, generate lightweight non-broadcast summaries and resolve the season.
5. Update the client run before the Continue Career action is enabled.

A failed finalization is recoverable and can be retried because battle generation and calendar summaries are deterministic for the prepared schedule.

The performance target for later profiling is to measure decision-to-featured-transcript separately from season-finalization time. Java migration should only replace this boundary after parity benchmarks show a material improvement over the Python oracle.

## Battle visual quality boundary

Career battle playback now has two renderer profiles that consume the same authoritative battle transcript.

Full mode keeps Pixi antialiasing, renders up to 2x device-pixel resolution, and enables transient projectiles, impacts, status labels, flashes, scale reactions, and impulse effects.

Light mode renders the Pixi tactical layer at 1x resolution without antialiasing and suppresses transient Pixi effects. It keeps the tactical grid, deterministic actor positions, Pokémon sprites, HUD, HP/status information, event callouts, commentary, playback timing, and battle result.

The browser automatically selects Light mode when reduced motion is requested, when reported hardware concurrency is four cores or fewer, or when reported device memory is 4 GB or less. A player preference overrides hardware auto-selection, except reduced motion always remains Light. The preference is stored locally when browser storage is available.

This boundary must remain presentation-only. Changing visual quality must never regenerate a transcript, change AI choices, alter hit/damage calculations, change movement legality, or produce a different winner.

Follow-up profiling should compare frame time, long tasks, GPU/CPU utilization, and memory use on the same transcript in Full and Light modes. The visual route should be tuned before any rules simplification is considered.

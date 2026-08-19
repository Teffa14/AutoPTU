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

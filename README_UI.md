# AutoPTU UI Guide

This repo uses a small design system shared across the battle UI, character builder, and paperdoll. All screens should pull from the design system first and only add app-specific overrides in `auto_ptu/api/static/styles.css`.

## Design System Files

- `design-system/tokens.css`: colors, spacing, radii, typography, z-index, transitions.
- `design-system/components.css`: panels, buttons, tabs, cards, pills, tooltips, modals, lists, slots, logs.
- `design-system/layout.css`: shared layout grids and breakpoints.
- `design-system/ui.js`: tabs, tooltips, modals, toasts, accordions, focus management.

## Add A New Screen

1. Create the HTML file under `auto_ptu/api/static/`.
2. Include the design system CSS and `ui.js` before app scripts:
   - `../../../design-system/tokens.css`
   - `../../../design-system/components.css`
   - `../../../design-system/layout.css`
   - `../../../design-system/ui.js`
3. Add `styles.css` only for screen-specific overrides.
4. Reuse shared classes:
   - Panels: `ds-panel`, `ds-panel-head`, `ds-panel-title`
   - Buttons: `ds-button`
   - Tabs: `ds-tab-list` + `ds-tab` with `data-tablist` + `data-tab-panel`
   - Cards: `ds-card`
   - Pills: `ds-pill` (use `.light` for light variants)
   - Tooltips: `data-tooltip="..."` and optional `data-tooltip-placement="top|bottom|left|right|auto"`
   - Modals: `data-modal-open`, `data-modal`, `data-modal-close`

## Tooltip Pattern

Add `data-tooltip="Your text"` to any element. Use `data-tooltip-placement="auto"` to allow auto-flip based on viewport.

## Drag + Drop (Builder)

The builder uses SortableJS and the shelf pattern:

- Deck cards live in `.char-deck-list`.
- Drop targets are `.char-shelf-list` with `data-shelf-kind` and optional `data-shelf-rank`.
- Invalid drops show a toast with the reason and do not mutate state.

## Prerequisites

Prereqs are evaluated using a small AST and rendered as checklists, not raw text. The evaluator supports:

- `AND` / `OR`
- `level >= N`
- `skillRank(skillId) >= rank`
- `hasClass(classId)`
- `hasFeature(featureId)`
- `countFeaturesWithTag(tag) >= N`

Checklist rendering lives in `auto_ptu/api/static/app.js` (`renderPrereqChecklist`).

## UI Gallery

Open `auto_ptu/api/static/ui-gallery.html` to see all components/states for quick regression checks.

## Packaged Web Build

`AutoPTUWeb.exe` does not live-edit from the source tree. If you change files under `auto_ptu/api/static/` and then open the packaged app from `dist/AutoPTUWeb`, you must rebuild the packaged app or you will be looking at stale bundled assets.

Use:

- `rebuild_auto_ptu_web.bat`

That script is the canonical packaged-web path. It:

1. closes `AutoPTUWeb.exe` if it is running
2. syncs frontend assets into the packaged runtime
3. runs the web verification slice
4. rebuilds `dist/AutoPTUWeb` with PyInstaller
5. writes `dist/AutoPTUWeb/BUILD_INFO.txt`

If a UI change is not visible in `AutoPTUWeb.exe`, check `dist/AutoPTUWeb/BUILD_INFO.txt` first.

## Cinematic Auto (Battle UI)

Battle topbar now includes cinematic controls for AI-vs-AI auto battles:

- `Cinematic Auto`: enables camera-driven lock phases during auto-step.
- `Dir`: cinematic director profile (`Broadcast`, `Movie`, `Fast Cast`).
- `Cam`: camera speed (`Fast`, `Medium`, `Slow`).
- `Export Replay`: exports cached cinematic events as JSON for replay/debug.
- `Cine:` status pill: live frame-time and queue depth signal for perf scaling.

Behavior guarantees:

- Auto-step is gated while camera lock, cinematic phase, or animation queue is active.
- Camera transitions are tweened (no direct jump zoom) with deadzone suppression to avoid jitter.
- In cinematic mode, move/ability animation capture is full fidelity (no `slice(-N)` truncation).

Perf handling:

- FX density scales down when frame-time or queue depth degrades.
- Low-priority VFX are deferred first when non-cinematic queue pressure is high.
## AI Model Lifecycle

- `GET /api/ai/models`: lists available AI model versions and metadata.
- `POST /api/ai/models/select`: switches active model for auto battles.
- The battle UI persists the last explicitly selected AI model and restores it on startup when it still exists.
- `Refresh AI` in the battle UI actively reloads model metadata so runtime changes can be applied without restarting the app.
- The main AI strip exposes a short insight summary derived from the selected model analysis payload.
- Auto-versioning: when drift/error metrics cross configured thresholds, a new model version is cut automatically instead of mutating the active baseline in place.
- Rule safety stays authoritative: action legality still flows through the existing PTU engine gates.

## Battle Royale Side Scaling

- Default random battle remains 2 sides for backward compatibility.
- Royale/random generation can now request N sides without 2-side roster injection overriding the request.
- UI control gating stays lifecycle-aware so prompt/lock/cinematic phases pause auto-step correctly.

## Logs And Replay Persistence

- Cinematic replay events can be exported from the battle UI via `Export Replay`.
- AI batch simulations persist `results.jsonl` and `summary.json` for offline analysis.
- Session-level notes are tracked in `SESSION_LOG.md` and release notes in `CHANGELOG.md`.

## Local Cry Assets (Gen9 Pack)

- Cry lookup now supports local fallback directories before PokeAPI download/cache.
- Default auto-detected path: `IMPLEMENTATION FILES/Generation 9 Pack v3.3.4/Audio/SE/Cries` (if present).
- Optional override: set `AUTO_PTU_LOCAL_CRY_DIRS` using OS path separator (`;` on Windows, `:` on Unix).

## Local Sprite Assets (Gen9 Graphics)

- Sprite lookup now supports local fallback directories before network sprite download.
- Default auto-detected path: `IMPLEMENTATION FILES/Generation 9 Pack v3.3.4/Graphics/Pokemon/Front`.
- Optional override: set `AUTO_PTU_LOCAL_SPRITE_DIRS` using OS path separator (`;` on Windows, `:` on Unix).

## Local Item Icon Assets (Gen9 Graphics)

- Item icon lookup now supports local fallback directories before PokeAPI icon download.
- Default auto-detected path: `IMPLEMENTATION FILES/Generation 9 Pack v3.3.4/Graphics/Items`.
- Optional override: set `AUTO_PTU_LOCAL_ITEM_ICON_DIRS` using OS path separator (`;` on Windows, `:` on Unix).

## Local UI Assets (Gen9 Graphics/UI)

- Added static API route for local Gen9 UI images:
  - `GET /assets/gen9/ui/{asset_path}`
- Source root:
  - `IMPLEMENTATION FILES/Generation 9 Pack v3.3.4/Graphics/UI`
- Current usage:
  - battle combatant status chips now display a local status icon marker from `Battle/icon_statuses.png` when available.

## Local Move Animation Assets (Gen9 Move Animation Project)

- Added move animation lookup route:
  - `GET /api/move_anim/{move_name}`
- Added static serving route for animation sheets:
  - `GET /assets/gen9/move-anims/{filename}`
- Source root:
  - `IMPLEMENTATION FILES/Gen 9 Move Animation Project/Graphics/Animations`
- Current usage:
  - ranged moves use named move sheets when available and animate from source to target.
  - melee moves use contact motion plus hit VFX, preferring named move sheets when available.
  - generic projectile/trail fallback VFX were removed from the active packaged runtime path.
  - unresolved names fall back to trajectory/contact/impact behavior instead of the removed generic attack animation family.

## Responsive Battle Layout

- The battlefield now sizes from the actual viewport instead of a fixed tile model.
- Grid tiles, tokens, HP overlays, hazard markers, badges, and panel chrome scale with the available stage area.
- Topbar collapse/expand triggers a layout refresh so the battlefield can reclaim vertical space on smaller windows.

## Campaign Table

- Open `/campaign` and press **Begin adventure** for the populated, six-chapter Prism Trail. The player-facing screen leads with chapter progress, current fiction, objective, three contextual choices, party cards, and a large Continue/Enter Battle control; administrative creation forms are folded away.
- The starter party includes a persistent local Ollama GM and three player agents with distinct personas and Pokémon companions. **Play party round**, individual **Let act** buttons, GM turn, and Autoplay all submit through the same campaign command boundary as a person. Model selections persist through battle navigation and deterministic fallback remains playable when Ollama is offline or returns an invalid decision.
- GM tools cover scenes, spotlight, clocks, quests, faction standing, campaign time, safety resume, tactical battle links, and are kept in a collapsed Director tools drawer.
- Players can speak in or out of character, make deterministic checks, keep private/table notes, and pause the table for a check-in. Spectators are read-only.
- Scene floors expose numbered multi-tile destinations within the selected Trainer or Pokemon's Speed. Click or drag once; the server resolves the deterministic path while enforcing walls, occupancy, ownership, scene readiness, and fog-frontier privacy.
- Gold scene markers open a contextual interaction panel. Players can investigate only when an owned token is in range; the GM independently controls marker visibility and lock state. Authored results and seeded checks enter the shared story feed only after interaction.
- Campaign state is snapshot-backed and evented, so tables survive server restarts. WebSocket events invalidate each participant's role-redacted snapshot immediately; no shared privileged snapshot is broadcast.

## Battle Command Center

- Enable `Plan actions` to stage any payload already supported by the battle engine, including movement, moves, items, maneuvers, trainer features, creative actions, and End Turn.
- Every declaration is dry-run against a deterministic battle clone. The queue can be reordered, removed, cleared, resolved one at a time, or resolved as a batch.
- The GM can open a named reaction window. Eligible combatants may stack an out-of-turn move or pass; the GM resolves the stack last-in, first-out.
- `Focus Board` hides scenario/camera setup while keeping live battle controls available. Current-actor actions now live beside the combatant roster instead of below Setup.
- Campaign battles add **Agent Act** to the foldable turn controller. It asks a companion agent to choose from the engine's exact legal moves, targets, shifts, or End Turn and commits the result through the real battle engine.
- `How to Play` and the battlefield instruction banner explain the active control state. Shortcuts are `?` guide, `E` end turn, `P` planning, `N` resolve next, `Shift+N` resolve all, `Escape` cancel targeting, `C`/`T` camera focus, and `Shift+R` restart.
- Shortcuts are ignored while typing in an input, select, or textarea. Plain Enter and plain `R` no longer trigger destructive battle actions.

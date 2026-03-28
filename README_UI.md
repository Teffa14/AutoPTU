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
  - move impacts now attempt to overlay the local move animation sprite sheet (by move name) on hit.
  - unresolved names safely fall back to existing procedural VFX only.

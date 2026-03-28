# UI Audit (Battle + Builder)

## Scope and constraints used
- Audited current client under `auto_ptu/api/static/*`.
- Preserved existing battle rules resolution and backend routes (`/api/battle/new`, `/api/action`, `/api/state`, `/api/ai/step`, sprite routes).
- Focused on incremental refactor and UX reliability (no framework changes).

## Current behavior inventory

### Battle UI
- Main battle shell in `index.html` with top toolbar, grid panel, feed panel, info panel.
- State polling every 1.5s (`refreshState`, `refreshSpriteStatus`) in `app.js`.
- Grid supports zoom/pan/center, move targeting, tile selection, hazard badges, and combatant overlays.
- Tooltip paths exist for move list, terrain/weather chips, combatant chips, and log keywords.
- Prompt overlay is rendered from `state.pending_prompts` and blocks visual flow but previously left some controls under-gated.
- Log supports category filters and keyword enrichment.

### Character Builder
- Runs from same `app.js`; screen mode determined by DOM presence (`isBattleUI`).
- Stepper exists as tab-like view switcher (profile/skills/advancement/class/features/edges/poke-edges/extras/inventory/pokemon-team/summary).
- Includes guided mode, history/undo/redo, snapshots, local save/load, and Fancy PTU export/import helpers.
- Pokemon Team step supports species catalog, legality checks, learnset/ability/item checks, and local build cards.
- Poke Edges step supports filters + search + checkbox selection with prereq checks.

## Functional risks
- **Control-state drift in battle lifecycle**: multiple controls were enabled/disabled ad hoc in different places (`render`, `toggleAuto`, `renderPrompts`, `aiStep`) which can diverge during mode switches and prompt states.
- **Error surfacing fragmentation**: runtime banner + browser `alert()` + occasional toasts caused inconsistent UX and blocked flow.
- **Prompt lock leakage**: player could still attempt tile actions while prompts were pending.
- **Fullscreen/resize scaling fragility**: grid fit logic could over-shrink during transient resize/fullscreen transitions.
- **Tile semantics discoverability**: selected tile summary lacked explicit terrain-type effect description.
- **Poke Edge UX gap**: no card-deck to slot-board interaction and no drag-time prereq ghost feedback.
- **Schema behavior mismatch risk**: Poke Edge ordering was implicit (Set) and not preserved for UI sloting intent.

## Navigability map
- `index.html` (battle primary)
  - Topbar links to `create.html` and `ui-gallery.html`.
  - In-page tabs switch battle info vs classes/builder panel.
- `create.html` (builder primary)
  - Topbar links back to battle/regression/gallery.
  - Step buttons switch views directly (not forced forward wizard).
  - Summary supports local save/load/snapshot operations.
- Import/export
  - Local storage via `autoptu_character`.
  - Trainer import/load in battle tab.
  - Fancy PTU import/export paths preserved through existing builder code.

## UI consistency findings
- Strong existing token/component base in `design-system/*`, but usage in `styles.css` still mixes hardcoded colors and repeated patterns.
- Similar cards/pills/list-row patterns implemented multiple times across features/edges/poke-edges/inventory.
- Tooltip pattern had multiple implementations (DS tooltip + app-specific tooltip); behavior mostly consistent but not centrally orchestrated.

## Recommendations with file-level targets
- `auto_ptu/api/static/app.js`
  - Centralize battle lifecycle gating via a dedicated UI helper.
  - Replace blocking error alerts with unified toast/runtime surface.
  - Add prompt-state action guards and resize/fullscreen fit hardening.
  - Upgrade selected tile info to include effect descriptions.
  - Introduce ordered Poke Edge slot state (`poke_edge_order`) with backward-compatible loading.
- `auto_ptu/api/static/design-system/ui.js`
  - Provide typed toast/notify API and shared typing-context helper for keyboard guards.
- `auto_ptu/api/static/styles.css`
  - Add reusable builder board/slot styles for deck->slot UX.
- `auto_ptu/api/static/ui/battle_ui.js`
  - Compute/apply lifecycle gates from a single place.
- `auto_ptu/api/static/ui/builder_ui.js`
  - Implement Poke Edge Card Deck -> Slot Board drag/drop and ghost prereq feedback.
- `auto_ptu/api/static/logic/prereq_eval.js`
  - Adapt prereq status into consistent UI evaluation payloads.
- `auto_ptu/api/static/logic/character_state.js`
  - Keep Set + order-array state coherent for ordered slot UIs.

## Implemented proof upgrades in this pass
- Builder proof: Poke Edge Card Deck -> Slot Board drag/drop with prereq ghost reason on invalid placement.
- Battle proof: centralized lifecycle gating + unified non-blocking error/toast surface, including prompt lock behavior and auto-AI pause handling.

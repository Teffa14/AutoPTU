# Campaign and Out-Of-Combat Architecture

This document records the implemented campaign-table foundation and the remaining out-of-combat roadmap. It is intentionally modular and aligns with `ARCHITECTURE_POLICY.md`.

## Implemented Foundation (July 2026)

- `auto_ptu/rules/campaign_state.py` owns serializable participants, scenes, clocks, quests, factions, chat, journals, safety state, and campaign time.
- `auto_ptu/rules/campaign_commands.py` is the permission and deterministic dice boundary. It accepts explicit commands and emits ordered campaign events.
- `auto_ptu/api/campaign_service.py` authenticates table participants, persists snapshots plus append-only events, and restores campaigns after restart.
- `auto_ptu/api/campaign_api.py` exposes create, join, state, command, and event endpoints under `/api/campaigns`.
- `/campaign` is a role-aware table workspace for GM, player, and spectator play. It polls persistent state so several browser clients can share the same table.
- Combat scenes can link to the tactical board. The battle board's command service stages, validates, reorders, removes, and resolves existing engine actions, and owns explicit out-of-turn reaction windows.

Campaign command permissions are authoritative on the server. The current tactical battle remains one local server-owned encounter; its role selector is a table control, not yet a campaign-authenticated remote-player ownership boundary.

**Guiding Principles**
- No monoliths. Each system is a small, focused module with clear contracts.
- Rules live in rules modules, not API or UI.
- All state changes are evented and auditable.
- Campaign data is append-friendly and migration-safe.

**Scope**
- Out-of-combat rules: travel, social, crafting, downtime, exploration, hazards, shopping.
- Roleplay systems: NPCs, factions, reputation, quests, clocks, scenes.
- VTT functions: maps, tokens, fog, lighting, chat, dice, permissions, journals.

## Core Domains

**Campaign**
- Owns world state, time, locations, factions, and active scenes.
- Contains Parties and Characters.

**Character**
- Trainer profile, stats, skills, features, edges, inventory, money, reputation.
- Linked to Pokémon roster, storage, and training history.

**Scene**
- A roleplay or exploration context.
- Holds participants, map, clocks, notes, and active effects.

**Quest**
- Structured objectives, rewards, and progress checkpoints.

**Faction**
- Reputation track, relationships, and special access rules.

**VTT**
- Maps, tokens, and shared board state.
- Real-time collaboration and permissions.

## Module Layout

The campaign modules above are implemented. The focused overworld and richer VTT modules below remain the proposed expansion layout.

**Rules**
- `auto_ptu/rules/overworld/`
  - `travel.py` Travel speed, routes, hazards.
  - `social.py` Social checks, disposition, reputation.
  - `crafting.py` Recipes, time, materials.
  - `downtime.py` Training, tutoring, jobs.
  - `exploration.py` Discovery, foraging, scouting.
  - `shopping.py` Markets, availability, discounts.
  - `capture.py` Out-of-combat capture and tracking.
- `auto_ptu/rules/roleplay/`
  - `quests.py` Objective state machine.
  - `clocks.py` Progress clocks, ticking rules.
  - `factions.py` Reputation and influence.
  - `dialogue.py` Dialogue nodes and outcomes.
- `auto_ptu/rules/vtt/`
  - `maps.py` Map metadata and layers.
  - `tokens.py` Token ownership, visibility.
  - `fog.py` Fog of war rules.
  - `lighting.py` Light sources and vision.
  - `chat.py` Chat, dice, and commands.
  - `journals.py` Notes, handouts, pins.

**Data**
- `auto_ptu/data/overworld/` Tables, rules config, travel routes.
- `auto_ptu/data/roleplay/` Quest templates, NPC templates.
- `auto_ptu/data/vtt/` Default map assets and configs.

**API**
- `auto_ptu/api/overworld_api.py`
- `auto_ptu/api/roleplay_api.py`
- `auto_ptu/api/vtt_api.py`

**UI**
- `auto_ptu/api/static/overworld.js`
- `auto_ptu/api/static/vtt.js`
- `auto_ptu/api/static/roleplay.js`

## State Model (High-Level)

**CampaignState**
- id, name, time, calendar
- locations, factions, quests
- parties, scenes

**SceneState**
- id, name, type (roleplay, exploration, combat)
- participants (characters, npcs)
- map_id, tokens, fog, lighting
- clocks, notes, effects

**CharacterState**
- trainer profile, stats, skills, features, edges
- inventory, money, reputation
- pokemon roster

## Rules Execution Flow

1. UI sends a command (travel, talk, craft, etc).
2. API validates contract and dispatches to a rule module.
3. Rule module updates state via an event.
4. Event is persisted and broadcast to clients.

## Persistence Strategy

**Event log first**
- Every campaign command becomes an ordered event.
- SQLite snapshots provide fast restart recovery.
- Campaign indexes and serialized collections use stable ordering.
- Event schema versioning remains required before external migrations are supported.

## Permissions

Roles:
- GM
- Player
- Spectator

Core rules:
- Only GM can mutate campaign-level data.
- Players can mutate their own characters.
- Token controls based on ownership or GM override.

## Migration Plan

Phase 0 — complete
- Define campaign contracts and event schemas.
- Implement persistence, token roles, polling, chat/dice, scenes, clocks, quests, factions, journals, safety tools, and combat links.

Battle command phase — complete
- Dry-run and stage existing engine actions without mutating authoritative battle state.
- Reorder, cancel, resolve-next, and resolve-all declarations.
- Open, collect, pass, stack, and resolve explicit out-of-turn reaction windows.

Phase 1
- Travel, downtime, social checks.
- Scene management and basic VTT map/tokens.

Phase 2
- Quests, clocks, factions.
- Fog, lighting, and basic chat/dice.

Phase 3
- Advanced VTT features and automation.

## Open Questions

- Do we store NPCs as Characters or separate type?
- Is party inventory centralized or per character?
- How do we handle homebrew rule packs for out-of-combat?
- Should live multi-client updates remain polling-based or move to WebSockets?
- How should campaign participant tokens map to tactical combatant ownership?

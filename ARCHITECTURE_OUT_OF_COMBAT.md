# Out-Of-Combat Architecture (Draft)

This document defines the target architecture for out-of-combat systems, roleplay tooling, and VTT features. It is intentionally modular and aligns with `ARCHITECTURE_POLICY.md`.

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

## Module Layout (Proposed)

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
- All actions become events.
- Snapshotting for performance.
- Event schema versioned.

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

Phase 0
- Define contracts and event schemas.
- Implement basic persistence and event broadcast.

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

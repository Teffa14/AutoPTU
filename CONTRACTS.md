# Contracts (Draft)

This document defines API, event, and data contracts for out-of-combat, roleplay, and VTT systems. It is a working draft and will evolve as modules are implemented.

## Versioning
- Contract versions follow `v1`, `v2` namespaces.
- Breaking changes require a new version.

## API Contracts

**Campaigns**
- `GET /api/campaigns`
  - Returns campaign list.
- `POST /api/campaigns`
  - Creates campaign.
- `GET /api/campaigns/{id}`
  - Returns campaign snapshot.

**Scenes**
- `POST /api/campaigns/{id}/scenes`
  - Creates scene.
- `POST /api/scenes/{id}/close`
  - Closes scene.

**Characters**
- `POST /api/campaigns/{id}/characters`
  - Create character in campaign.
- `GET /api/characters/{id}`
  - Snapshot.

**Overworld**
- `POST /api/overworld/travel`
  - Command: travel route.
- `POST /api/overworld/craft`
  - Command: craft item.
- `POST /api/overworld/shop`
  - Command: purchase items.

**Roleplay**
- `POST /api/roleplay/check`
  - Command: skill check.
- `POST /api/roleplay/dialogue`
  - Command: select dialogue node.
- `POST /api/roleplay/quest`
  - Command: update quest state.

**VTT**
- `GET /api/vtt/maps`
  - Map list.
- `POST /api/vtt/maps`
  - Create map.
- `POST /api/vtt/tokens`
  - Spawn or update token.
- `POST /api/vtt/fog`
  - Update fog of war.
- `POST /api/vtt/light`
  - Update lighting.
- `POST /api/vtt/chat`
  - Send chat message or dice command.

## Command Payloads (v1)

**Travel**
```json
{
  "campaign_id": "camp-1",
  "party_id": "party-1",
  "route_id": "route-3",
  "pace": "normal"
}
```

**Skill Check**
```json
{
  "character_id": "char-1",
  "skill": "Survival",
  "dc": 14,
  "context": "tracking"
}
```

**Token Update**
```json
{
  "scene_id": "scene-1",
  "token_id": "token-44",
  "position": [12, 9],
  "visible": true
}
```

## Event Contracts (v1)

Events are broadcast over websocket and stored in the event log.

**Base Event**
```json
{
  "id": "evt-123",
  "type": "travel_started",
  "time": "2026-03-02T00:00:00Z",
  "actor_id": "char-1",
  "payload": {}
}
```

**Travel Events**
- `travel_started`
- `travel_progressed`
- `travel_completed`
- `travel_hazard`

**Roleplay Events**
- `skill_check`
- `dialogue_choice`
- `quest_updated`
- `reputation_changed`

**VTT Events**
- `token_moved`
- `fog_updated`
- `light_updated`
- `chat_message`
- `dice_roll`

## Data Contracts

**Character**
- profile, stats, skills, features, edges, inventory, money.

**InventoryItem**
- id, name, quantity, tags, metadata.

**Quest**
- id, name, state, objectives, rewards.

**Token**
- id, name, position, owner_id, vision, light.

## Validation Rules

- Commands must be idempotent where possible.
- All commands must include `campaign_id`.
- Invalid commands return 400 with error details.

## Security

- Auth token attached to all write requests.
- Permissions checked by campaign role.

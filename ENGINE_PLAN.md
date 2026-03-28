# Auto PTU Engine Plan

This document captures the plan for rebuilding Auto PTU into a complete PTU 1.05 rules engine packaged as a single executable. It summarizes the data ingestion strategy, high-level architecture, and phased implementation roadmap.

## Current Progress (2025-12-23)

- **Playable demo shipped** - PyInstaller bundle + launcher expose the Rainy Training Grounds scenario so non-technical players can experiment with the grid-aware encounter.
- **Rules/CLI alignment** - Initiative ordering, turn phases, PTU-range validation, smarter AI scoring, and dice-first narration are live in `auto_ptu.rules`/`auto_ptu.gameplay`, giving us confidence in damage math before we add multi-trainer flows.
- **Multi-trainer interactive battles** - The text session now spawns every trainer side (player or AI) on the same grid, renders per-combatant markers/statuses, and drives turns until only one team remains, paving the way for switching/recall rules.
- **Next immediate targets** - Expand the initiative queue to multiple trainers/parties, add LOS + template shapes for targeting/movement, and grow the persistent/volatile status catalog (Paralysis/Sleep/Freeze, Confusion, etc.) ahead of trainer actions and multi-mon battles.

## 1. Data Ingestion Strategy

Goal: unify the CSV bundles in `files/` with the PTU 1.05 rulebook PDFs so the engine has authoritative data for Pokemon, trainers, moves, features, edges, abilities, classes, and references.

### 1.1 Sources

| Domain | Files |
| --- | --- |
| Pokemon species, moves, capabilities, skills, items | `files/Copia de Fancy PTU 1.05 Sheet - Version Hisui - *.csv`, `files/GalarDex + Armor_Crown.pdf`, `files/HisuiDex.pdf` |
| Trainers, classes, features, edges, recipes | `files/rulebook/Pokemon Tabletop United 1.05 Core.pdf`, `files/rulebook/Indices and Reference.pdf`, `files/rulebook/Game of Throhs.pdf`, `files/rulebook/Blessed and the Damned.pdf` |
| Supplemental rule references | `files/rulebook/Arceus References.pdf`, `files/rulebook/Do Porygon Dream of Mareep.pdf`, `files/rulebook/PTU changelog 1.05.txt`, `files/rulebook/PTU May/Sept 2015 Playtest Packet.pdf`, `files/rulebook/Useful Charts.pdf` |
| Character sheets / templates | `files/rulebook/PTU 1.05 Pokemon Sheet.pdf`, `files/rulebook/PTU 1.05 Trainer Sheet.pdf` |

### 1.2 Extractors

1. **Structured CSV loaders (Python)** - extend `auto_ptu.csv_repository` into a package with loaders for species, moves, abilities, skills, capabilities, items, recipes. Normalize the columns (e.g., `damage_base`, `freq`, `effects`), convert enums (freq, action type) to canonical values, and record data provenance.
2. **PDF parsers (PyPDF2)** - targeted extraction scripts that parse specific sections/tables from the core rulebook and supplements. Output machine-readable JSON (e.g., `data/rules/features.json`, `data/rules/edges.json`, `data/rules/capabilities.json`). Focus on:
   - Feature/Edge definitions (name, frequency, action type, prerequisites, effect text).
   - Ability definitions + keywords.
   - Capability descriptions and mechanical hooks.
   - Combat tables (damage base, condition effects, weather tables).
3. **Manual YAML overrides** - keep a `data/overrides/` folder for cases where PDF text can't be reliably parsed (e.g., complex tables, errata). These files document the manual source with page references.
4. **Validation scripts** - add CLI utilities under `auto_ptu/tools/` to diff CSV/PDF data against expected constraints (e.g., ensure every feature has a valid frequency enum, every capability links to a hook in the engine).

### 1.3 Data Schema

Create typed schemas (Pydantic models) for:

- `SpeciesRecord`, `MoveRecord`, `AbilityRecord`, `CapabilityRecord`
- `TrainerFeature`, `TrainerEdge`, `ClassFeature`, `Recipe`
- `ItemRecord` (held items, consumables), `StatusDefinition`
- `TerrainDefinition`, `WeatherDefinition`

Persist normalized JSON snapshots under `auto_ptu/data/compiled/*.json` so the engine can load without re-parsing PDFs every launch. Provide a build script (`python -m auto_ptu.tools.build_data`) that regenerates the compiled data from CSV/PDF sources.

## 2. Engine Architecture

### 2.1 Modules

1. **`auto_ptu.data`** - schema models + loaders for compiled JSON. Provides query APIs for species, moves, trainer archetypes, etc.
2. **`auto_ptu.rules`** - core mechanics engine implementing PTU 1.05 rules:
   - Stat calculations, combat stages, derived stats
   - Move resolution, accuracy, damage pipeline
   - Status afflictions (persistent & volatile)
   - Weather/terrain modifiers, capability hooks
   - Trainer feature and edge effects
3. **`auto_ptu.sim`** - battle state machines:
   - Turn/round management, initiative queues, action resolution order
   - Targeting, movement, grid handling (including abstracted distances)
   - AI opponents (greedy/expectimax/Monte Carlo) leveraging full mechanics
4. **`auto_ptu.cli`** - Typer CLI exposing:
   - Data inspection (describe species, moves, features)
   - Campaign/campaign builder workflows
   - Play/simulate commands invoking the engine
5. **`auto_ptu.ui` (future)** - placeholder for any GUI surface (PySide/Electron) sharing the same engine API.

### 2.2 State Machines

- **BattleState** - tracks round, initiative slots, pending actions, weather, terrain, status timers, trainer actions.
- **Action** objects - encapsulate move usage, maneuvers, item use, feature activation, switching, etc., each with validation + resolve methods.
- **Effect pipeline** - modular hooks triggered at specific phases (before accuracy roll, before damage, after damage, end of turn) so abilities/features/capabilities can register modifiers.

### 2.3 Integration

- CLI `play` command instantiates a `BattleSession` with trainer roster data and loops through user input (console now, GUI later).
- Existing `MatchEngine` evolves into a facade over `auto_ptu.sim` for automation/test harnesses.
- Tests under `tests/` cover move resolution, status effects, trainer feature interactions, etc., referencing data from compiled JSON (not PDFs directly).

## 3. Implementation Roadmap

1. **Data ingestion foundation**
   - Build CSV loaders for species, moves, skills.
   - Script targeted PDF extraction for capabilities, abilities, features, edges.
   - Define schemas + compiled data outputs.
2. **Stats & data integration**
   - Wire compiled data into `PokemonSpec`, `TrainerSpec`, `MoveSpec`.
   - Add validation/unit tests ensuring sample species/trainers match rulebook stats.
3. **Combat core**
   - Implement stat derivations, combat stages, initiative, action economy.
   - Build accuracy/damage pipeline with type effectiveness, STAB, crits, resistances.
   - Support Struggle attacks, maneuvers, and environmental interactions.
4. **Statuses & conditions**
   - Persistent (Burn, Poison, etc.) and volatile (Confuse, Flinch, etc.) handling with duration + saves.
   - Weather/terrain systems and capability hooks.
5. **Trainer integration**
   - Implement feature/edge effects, action costs, trainer-directed commands.
   - Add item usage, recipes, crafting hooks (where applicable).
6. **AI & simulations**
   - Upgrade expectimax/Monte Carlo to use full mechanics.
   - Provide config options for different AI difficulty modes.
7. **CLI/UX polish**
   - Enhance prompts, add logging/recap outputs, ensure PyInstaller bundle includes rule data.
8. **QA & validation**
   - Regression tests covering iconic scenarios (Gym battle, weather effects, status stacking).
   - Cross-check outputs against rulebook examples.

Each phase should land with documented coverage (unit tests + rule citations) so future UI layers can trust the engine behavior.


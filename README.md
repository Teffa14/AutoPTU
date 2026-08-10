# Auto PTU

Auto PTU is a local-first encounter generator and battle simulator for Pokemon Tabletop United (PTU). It focuses on deterministic, testable combat resolution and a CLI-first workflow.

> Este repositorio contiene también **AutoPTU Career**, el modo carrera web. Consulta
> [README_CAREER.md](README_CAREER.md) para arquitectura, ejecución y despliegue.

PTUDatabase and the CSV sheets in `files/` are the source of truth for item descriptions and mechanics. Foundry is a last-resort reference to copy math or logic only when the primary datasets are missing.

Docs index: `DOCS_INDEX.md` lists the authoritative project documents and archives.

## Runtime Architecture

- PTU rules legality and combat resolution remain authoritative in the rules engine.
- The live AI decision core currently runs through `auto_ptu/rules/ai_hybrid.py`.
- `auto_ptu/ai/policy_adapter.py` is the supported integration seam for alternate AI policies. External AI repos should plug into that adapter boundary instead of wiring directly into the rules engine.
- `auto_ptu/gameplay.py` orchestrates battle flow, AI diagnostics capture, and packaged runtime coordination.
- `dist/AutoPTUWeb` is generated output, not a live source tree.

## Quickstart

```powershell
cd AutoPTU
python -m venv .venv && .venv\Scripts\activate
pip install -e .
auto-ptu describe
auto-ptu run demo_campaign.json --team-size 2
auto-ptu play demo_campaign.json --team-size 2
```

### Web campaign and tactical board

Run the current source UI with:

```powershell
python auto_ptu_web_launcher.py
```

The launcher opens the local game in your browser. Open `Campaign` and press **Begin The Prism Trail** to start the populated six-chapter campaign with an Ollama GM and three companion Trainers—no manual campaign setup is required. Choose a starter, then use the visible scene rail and world map to play. The starter becomes a persistent owned actor and is the same Pokemon loaded into tactical battles. A GM can reveal a scene, make it ready, activate it, or hold it back; players cannot see or travel to future locations until activation. Click a connected regional node or drag the party marker to travel. On the scene floor, select your Trainer or Pokemon and click or drag to any numbered glowing destination within its Speed; the server resolves the deterministic shortest legal path. Select gold scene markers to inspect, talk, enter, shop, or uncover authored clues. Vision, remembered cells, blocked terrain, hidden NPCs, secret outcomes, point availability, and interaction locks are redacted per player and controlled by the GM. Combat chapters take you to the tactical board, where the foldable turn controller exposes Move, Actions, Plan, Agent Act, Undo, and End Turn.

Ollama is optional: when it is running, the game lists installed models and uses structured legal actions; otherwise the same controls continue with deterministic fallback decisions. The responsive local default is `qwen2.5:3b`, while larger installed models remain selectable for GM prose.

The server currently binds to `127.0.0.1`, so separate roles can be tested in multiple browsers on the same computer. LAN/internet hosting requires a deliberate networking and authentication deployment pass.

The verified 2026-07-17 release story completed all 14 scenes and seven battles through the Champion with zero browser/HTTP errors. Scene pathing, interactions, locks, and responsive controls are verified in `reports/MILESTONE_PATH_INTERACTIONS_2026-07-17.md`; the full-campaign evidence remains in `reports/MILESTONE_SCENE_PRIVACY_AND_PLAYTHROUGH_2026-07-17.md`.

## Tests

```powershell
python -m pytest
```

## Data Sources

- CSV bundle: `files/`
- PTU Database YAML: `PTUDatabase-main/Data/ptu.1.05.yaml`
- Rulebook PDFs: `files/rulebook/`

## Build

```powershell
pyinstaller --clean AutoPTU.spec
```

## Packaged Web Build

Use the packaged web rebuild script when changing files under `auto_ptu/api/static/` or other packaged runtime assets:

```powershell
cmd /c rebuild_auto_ptu_web.bat
```

That script is the canonical path for `AutoPTUWeb.exe`. It closes the running packaged app, rebuilds `dist/AutoPTUWeb` in place, syncs packaged runtime assets, runs the packaged-web verification slice, and writes `dist/AutoPTUWeb/BUILD_INFO.txt`.

## Contributing

- Read `CONTRIBUTING.md` and `ARCHITECTURE_POLICY.md` before adding rules.
- Add a test for every new hook or rules change.
- Update `CHANGELOG.md` and the relevant trackers.

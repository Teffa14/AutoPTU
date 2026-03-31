# Auto PTU

Auto PTU is a local-first encounter generator and battle simulator for Pokemon Tabletop United (PTU). It focuses on deterministic, testable combat resolution and a CLI-first workflow.

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

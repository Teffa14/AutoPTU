# Auto PTU

Auto PTU is a local-first encounter generator and battle simulator for Pokemon Tabletop United (PTU). It focuses on deterministic, testable combat resolution and a CLI-first workflow.

PTUDatabase and the CSV sheets in `files/` are the source of truth for item descriptions and mechanics. Foundry is a last-resort reference to copy math or logic only when the primary datasets are missing.

Docs index: `DOCS_INDEX.md` lists the authoritative project documents and archives.

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

## Contributing

- Read `CONTRIBUTING.md` and `ARCHITECTURE_POLICY.md` before adding rules.
- Add a test for every new hook or rules change.
- Update `CHANGELOG.md` and the relevant trackers.

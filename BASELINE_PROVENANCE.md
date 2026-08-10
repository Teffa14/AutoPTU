# AutoPTU Career baseline provenance

- Source workspace: `C:\Users\tefa1\AutoPTU`
- Source branch: `main`
- Source commit: `27c4e636ca8132ce0e31ed17f394ba248a1b7174`
- Snapshot date: `2026-08-10` (Australia/Brisbane)
- Relevant working-tree files copied: `39`
- Ordered relevant-file manifest SHA-256: `bb7c30d05514af7401581882dff0416fb77a96c60423d3b593c59505e3d6c154`
- First manifest entry: `.gitignore` / `c7a6744072770fdf0cd0cc6ce03cc019f882d951d38275320887ee2b3c2ee48a`
- Last manifest entry: `tests/test_web_regressions.py` / `dfdb525837354f2a5cc0700772a9e256f67954a4ddeb98b3cd3fd85b8e350814`

The aggregate hash was calculated from the UTF-8 sequence of sorted
`relative-path<TAB>sha256` entries. Generated builds, caches, temporary files,
runtime reports, and AI rating artifacts were intentionally excluded. The
original AutoPTU workspace was not modified by this snapshot.

## Required baseline verification

```powershell
python -m pytest -q tests/test_campaign_play.py tests/test_battle_commands.py tests/test_trainer_features.py tests/test_web_regressions.py
```

Expected result: `163 passed`.

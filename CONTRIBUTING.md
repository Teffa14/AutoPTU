# Contributing to Auto PTU

Thanks for helping turn Auto PTU into a fully playable PTU 1.05 experience! This guide keeps every change understandable for brand-new teammates and non-coders. Always narrate what you are doing, why it matters, and where the rulebook backs it up.

## 1. Pick a roadmap item

1. Read `ROADMAP.md` and `BATTLE_ENGINE_DESIGN.md` to see which milestone is `[in progress]`.
2. Open the PTU Core 1.05 rulebook (Chapter 7: Combat) plus any supplements cited in the roadmap entry.
3. Record the page numbers you will implement. Quote them in code comments/docstrings so readers can cross-check.

## 2. Plan before you code

1. Summarize the change in plain language (1-3 paragraphs) and drop it into the top of the PR/commit or the relevant doc section.
2. Write down the scenario you will use for validation (e.g., "Pikachu (SPD 12) vs. Squirtle (SPD 9) to prove initiative order"). Every mechanic needs at least one reproducible test.
3. If the feature spans multiple files, update `ENGINE_PLAN.md` or `BATTLE_ENGINE_DESIGN.md` first so reviewers know the architecture.

## 3. Implement with junior-friendly comments

1. Reference PTU chapters directly in comments only where the code is non-obvious. Example: `# PTU Core p. 203 - Shift happens before Standard Action`.
2. Prefer data-driven logic (CSV/compiled JSON) instead of hard-coded strings. When you must hard-code values, cite the table that provided them.
3. Keep functions short and composable; name helpers after the rulebook concept (e.g., `build_initiative_queue` instead of `sort_list`).

## 4. Test with clear scenarios

1. Add or extend files under `tests/`. Encode each mechanic as a `unittest.TestCase` with descriptive method names.
2. Use deterministic RNG seeds so dice results are reproducible.
3. Run the suite locally: `python -m unittest`.
4. If you ship user-facing changes, also rebuild the executable with `pyinstaller AutoPTU.spec` and sanity-check the launcher menu.

## 5. Update docs every time

1. Append your change note to `CHANGELOG.md` under the `[Unreleased]` heading.
2. If you advanced a milestone, mark it `[done]` or `[in progress]` in `ROADMAP.md`.
3. Expand any relevant design doc sections so future contributors understand the new system without reading the entire diff.

## 6. Keep the repo clean

1. Treat generated output as disposable. Build folders, one-off screenshots, temporary maps, simulation batches, and local reports should never be mixed into source changes unless the file is a deliberate checked-in fixture.
2. Keep scratch work in ignored `tmp_*` or `_tmp_*` files only. If a helper script becomes useful to other contributors, move it into `scripts/` and document what it generates.
3. Respect repository line endings. Python, JS, CSS, HTML, JSON, and Markdown stay LF; Windows launcher scripts stay CRLF. The repo-level `.editorconfig` and `.gitattributes` exist to stop accidental whole-file churn.
4. Separate source changes from generated refreshes. If you regenerate a coverage report, dataset, or asset bundle, do it in a dedicated follow-up commit so reviewers can tell code changes from output changes.
5. Before opening a PR or handing work off, run the smallest meaningful validation set and note it explicitly. At minimum:
   `python -m pytest tests/test_trainer_passive_perks.py tests/test_web_regressions.py -q`
   `node --check auto_ptu/api/static/app.js`
6. Use `python scripts/validate_repo.py` as the default validation entrypoint. For wider refactors, run `python scripts/validate_repo.py --full`.


Following these steps leaves breadcrumbs for future teammates (and our future selves). When in doubt, over-communicate in the docs before touching code.


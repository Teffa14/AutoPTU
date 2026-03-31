from pathlib import Path

from auto_ptu import gameplay


def test_seed_runtime_ai_reports_copies_models_and_profile(monkeypatch, tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    bundle_root = tmp_path / "bundle"
    reports_dir = runtime_root / "portable_reports"
    bundled_reports = bundle_root / "reports"
    bundled_models = bundled_reports / "ai_models"
    bundled_models.mkdir(parents=True, exist_ok=True)
    (bundled_models / "model_20260401_000000_test.json").write_text('{"profiles":{}}', encoding="utf-8")
    (bundled_models / "ratings.json").write_text('{"ratings":[]}', encoding="utf-8")
    (bundled_reports / "ai_profiles.json").write_text('{"profiles":{}}', encoding="utf-8")

    monkeypatch.setattr(gameplay, "RUNTIME_ROOT", runtime_root)
    monkeypatch.setattr(gameplay, "PROJECT_ROOT", bundle_root)
    monkeypatch.setattr(gameplay, "REPORTS_DIR", reports_dir)

    gameplay._seed_runtime_ai_reports()

    assert (reports_dir / "ai_models" / "model_20260401_000000_test.json").exists()
    assert (reports_dir / "ai_models" / "ratings.json").exists()
    assert (reports_dir / "ai_profiles.json").exists()

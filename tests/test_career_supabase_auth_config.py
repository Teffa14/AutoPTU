from pathlib import Path


def test_supabase_auth_redirects_target_github_pages() -> None:
    config = (Path(__file__).resolve().parents[1] / "supabase" / "config.toml").read_text(encoding="utf-8")

    assert 'site_url = "https://teffa14.github.io/AutoPTU/career-game/"' in config
    assert '"https://teffa14.github.io/AutoPTU/career-game/"' in config
    assert '"https://teffa14.github.io/AutoPTU/career-game/**"' in config
    assert "autoptu-career.vercel.app" not in config

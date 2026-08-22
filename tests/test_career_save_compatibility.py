from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.models import CareerRun


def test_save_loader_ignores_unknown_top_level_fields() -> None:
    run = CareerEngine().new_run(
        player_id="save-forward-compat",
        name="Ari",
        region="kanto",
        starter="Rattata",
        classes=["Ace Trainer"],
        seed=731,
    )
    payload = run.to_dict()
    payload["legacy_browser_panel"] = {"tab": "club", "expanded": True}
    payload["future_extension_flag"] = True

    restored = CareerRun.from_dict(payload)

    assert restored.id == run.id
    assert restored.build.name == run.build.name
    assert restored.active_roster == run.active_roster
    assert restored.timeline == run.timeline

from auto_ptu.api import server


def test_move_anim_resolution_prefers_curated_map_entry():
    assert server._resolve_move_anim_file("First Impression") == "GEN8- First Impression.png"


def test_move_anim_resolution_does_not_fall_back_to_generic_type_sheet():
    assert server._resolve_move_anim_file("Tackle") is None


def test_move_anim_resolution_rejects_generic_mapped_strike_and_slash_assets():
    assert server._resolve_move_anim_file("Scratch") is None
    assert server._resolve_move_anim_file("Quick Attack") is None


def test_move_anim_resolution_allows_curated_type_themed_assets_when_they_are_the_mapped_move_sheet():
    assert server._resolve_move_anim_file("Water Gun") == "PRAS- Water.png"
    assert server._resolve_move_anim_file("Psychic") == "PRAS- Psychic BG.png"

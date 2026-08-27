from auto_ptu.career.trainer_sprites import DEFAULT_TRAINER_SPRITE, normalize_trainer_sprite


def test_safe_showdown_sprite_ids_are_preserved() -> None:
    assert normalize_trainer_sprite(" aarune ") == "aarune"
    assert normalize_trainer_sprite("Juliana-S") == "juliana-s"
    assert normalize_trainer_sprite("red-gen1main") == "red-gen1main"


def test_trainer_sprite_ids_fail_closed_without_coercion() -> None:
    class Hostile:
        def __str__(self) -> str:
            raise AssertionError("trainer sprite coercion must not run")

    assert normalize_trainer_sprite(Hostile()) == DEFAULT_TRAINER_SPRITE
    assert normalize_trainer_sprite(True) == DEFAULT_TRAINER_SPRITE
    assert normalize_trainer_sprite("../../secret") == DEFAULT_TRAINER_SPRITE
    assert normalize_trainer_sprite("red.png") == DEFAULT_TRAINER_SPRITE

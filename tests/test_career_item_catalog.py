from auto_ptu.career.items import item_catalog, shop_catalog
from auto_ptu.career.roster import TRAINING_KIT_WEAR


def test_training_kit_catalog_discloses_exact_longevity_cost() -> None:
    item = item_catalog()["Training Kit"]
    product = shop_catalog()["training_kit"]

    assert item["career_health_cost"] == TRAINING_KIT_WEAR
    assert product["career_health_cost"] == TRAINING_KIT_WEAR
    assert str(TRAINING_KIT_WEAR) in item["description_es"]
    assert str(TRAINING_KIT_WEAR) in item["description_en"]
    assert "retira" in item["description_es"]
    assert "retires" in item["description_en"]
    assert str(TRAINING_KIT_WEAR) in product["description_es"]
    assert str(TRAINING_KIT_WEAR) in product["description_en"]

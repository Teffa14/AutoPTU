import unittest

from auto_ptu import ptu_engine


class PTUEngineTests(unittest.TestCase):
    def test_build_mon_from_dict_accepts_frequency_key(self) -> None:
        mon = ptu_engine.build_mon_from_dict(
            {
                "species": "Pikachu",
                "level": 20,
                "types": ["Electric"],
                "hp_stat": 6,
                "atk": 5,
                "def": 4,
                "spatk": 6,
                "spdef": 4,
                "spd": 8,
                "moves": [
                    {
                        "name": "Thunder Shock",
                        "type": "Electric",
                        "category": "Special",
                        "db": 6,
                        "frequency": "At-Will",
                    }
                ],
            }
        )

        self.assertEqual("At-Will", mon.known_moves[0].freq)


if __name__ == "__main__":
    unittest.main()

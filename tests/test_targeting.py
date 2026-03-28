import unittest

from auto_ptu.data_models import MoveSpec
from auto_ptu.rules import targeting


class TargetingTests(unittest.TestCase):
    def test_blast_is_square(self) -> None:
        move = MoveSpec(
            name="Blast Test",
            type="Normal",
            category="Special",
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            area_kind="Blast",
            area_value=2,
            freq="At-Will",
        )
        tiles = targeting.affected_tiles(None, (0, 0), (5, 5), move)
        expected = {(5, 5), (5, 6), (6, 5), (6, 6)}
        self.assertEqual(tiles, expected)

    def test_close_blast_is_adjacent_square(self) -> None:
        move = MoveSpec(
            name="Close Blast Test",
            type="Normal",
            category="Special",
            range_kind="CloseBlast",
            range_value=2,
            target_kind="Self",
            target_range=0,
            area_kind="CloseBlast",
            area_value=2,
            freq="At-Will",
        )
        tiles = targeting.affected_tiles(None, (5, 5), (6, 5), move)
        expected = {(6, 5), (6, 4), (7, 5), (7, 4)}
        self.assertEqual(tiles, expected)

    def test_cone_is_three_wide_rows(self) -> None:
        move = MoveSpec(
            name="Cone Test",
            type="Normal",
            category="Special",
            range_kind="Cone",
            range_value=3,
            target_kind="Self",
            target_range=0,
            area_kind="Cone",
            area_value=3,
            freq="At-Will",
        )
        tiles = targeting.affected_tiles(None, (0, 0), (3, 0), move)
        expected = {
            (1, -1),
            (1, 0),
            (1, 1),
            (2, -1),
            (2, 0),
            (2, 1),
            (3, -1),
            (3, 0),
            (3, 1),
        }
        self.assertEqual(tiles, expected)

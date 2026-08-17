package io.autoptu.core.rules;

import io.autoptu.core.model.GridCoord;
import io.autoptu.core.model.GridState;
import io.autoptu.core.model.MoveSpec;
import org.junit.jupiter.api.Test;

import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

class TargetingTest {
    private static MoveSpec move(
            String targetKind,
            Integer targetRange,
            String areaKind,
            Integer areaValue
    ) {
        return new MoveSpec(
                targetKind,
                targetKind,
                targetRange,
                targetRange,
                areaKind,
                areaValue,
                targetKind
        );
    }

    @Test
    void normalizesTargetAndAreaKindsLikePython() {
        MoveSpec spec = new MoveSpec("Ranged, 1 Target", null, 6, null, "Close Blast 3", 3, "Ranged 6, Close Blast 3");
        assertEquals("ranged", Targeting.normalizedTargetKind(spec));
        assertEquals("close", Targeting.normalizedAreaKind(spec));
    }

    @Test
    void targetRequirementMatchesSelfFieldAndDirectionalAreas() {
        assertFalse(Targeting.moveRequiresTarget(move("Self", 0, null, null)));
        assertFalse(Targeting.moveRequiresTarget(move("Field", 0, "Field", 0)));
        assertTrue(Targeting.moveRequiresTarget(move("Self", 0, "Cone", 3)));
        assertTrue(Targeting.moveRequiresTarget(move("Self", 0, "Line", 4)));
        assertTrue(Targeting.moveRequiresTarget(move("Self", 0, "CloseBlast", 2)));
    }

    @Test
    void chebyshevDistanceMatchesGridRules() {
        assertEquals(4, Targeting.chebyshevDistance(new GridCoord(1, 1), new GridCoord(5, 3)));
    }

    @Test
    void footprintsPreservePythonEvenSizeAnchoring() {
        assertEquals(
                Set.of(new GridCoord(5, 5), new GridCoord(5, 6), new GridCoord(6, 5), new GridCoord(6, 6)),
                Targeting.footprintTiles(new GridCoord(5, 5), "Large")
        );
        assertEquals(9, Targeting.footprintTiles(new GridCoord(5, 5), "Huge").size());
        assertEquals(16, Targeting.footprintTiles(new GridCoord(5, 5), "Gigantic").size());
    }

    @Test
    void footprintDistanceMeasuresClosestOccupiedTiles() {
        assertEquals(
                1,
                Targeting.footprintDistance(
                        new GridCoord(0, 0), "Large",
                        new GridCoord(2, 0), "Medium"
                )
        );
    }

    @Test
    void rangedAndMeleeRangeUseFootprintsWhenProvided() {
        MoveSpec melee = move("Melee", 1, null, null);
        assertTrue(Targeting.isTargetInRange(
                new GridCoord(0, 0), new GridCoord(2, 0), melee,
                "Large", "Medium", new GridState(10, 10)
        ));
        assertFalse(Targeting.isTargetInRange(
                new GridCoord(0, 0), new GridCoord(3, 0), melee,
                "Large", "Medium", new GridState(10, 10)
        ));
    }

    @Test
    void lineAreaMatchesPythonDirectionStep() {
        MoveSpec line = move("Self", 0, "Line", 3);
        assertEquals(
                Set.of(new GridCoord(3, 2), new GridCoord(4, 2), new GridCoord(5, 2)),
                Targeting.affectedTiles(new GridState(10, 10), new GridCoord(2, 2), new GridCoord(4, 2), line)
        );
    }

    @Test
    void coneUsesThreeTileWideRows() {
        MoveSpec cone = move("Self", 0, "Cone", 2);
        Set<GridCoord> result = Targeting.affectedTiles(
                new GridState(10, 10), new GridCoord(2, 2), new GridCoord(4, 2), cone
        );
        assertEquals(
                Set.of(
                        new GridCoord(3, 1), new GridCoord(3, 2), new GridCoord(3, 3),
                        new GridCoord(4, 1), new GridCoord(4, 2), new GridCoord(4, 3)
                ),
                result
        );
    }

    @Test
    void closeBlastPreservesPythonEvenSizeShape() {
        MoveSpec closeBlast = move("Self", 0, "CloseBlast", 2);
        assertEquals(
                Set.of(
                        new GridCoord(3, 2), new GridCoord(3, 1),
                        new GridCoord(4, 2), new GridCoord(4, 1)
                ),
                Targeting.affectedTiles(new GridState(10, 10), new GridCoord(2, 2), new GridCoord(3, 2), closeBlast)
        );
    }

    @Test
    void blastIsSquareCenteredOnTarget() {
        MoveSpec blast = move("Ranged", 6, "Blast", 3);
        Set<GridCoord> result = Targeting.affectedTiles(
                new GridState(10, 10), new GridCoord(1, 1), new GridCoord(5, 5), blast
        );
        assertEquals(9, result.size());
        assertTrue(result.contains(new GridCoord(4, 4)));
        assertTrue(result.contains(new GridCoord(6, 6)));
    }

    @Test
    void burstClipsToGridButKeepsCenter() {
        MoveSpec burst = move("Ranged", 6, "Burst", 1);
        Set<GridCoord> result = Targeting.affectedTiles(
                new GridState(2, 2), new GridCoord(0, 0), new GridCoord(0, 0), burst
        );
        assertEquals(Set.of(
                new GridCoord(0, 0), new GridCoord(0, 1),
                new GridCoord(1, 0), new GridCoord(1, 1)
        ), result);
    }

    @Test
    void lineOfSightUsesSameBresenhamCellsAsPython() {
        GridState grid = new GridState(10, 10);
        GridCoord origin = new GridCoord(0, 0);
        GridCoord target = new GridCoord(4, 2);
        assertFalse(Targeting.lineOfSightClear(grid, origin, target, Set.of(new GridCoord(2, 1))));
        assertTrue(Targeting.lineOfSightClear(grid, origin, target, Set.of(new GridCoord(2, 2))));
    }

    @Test
    void targetAnchorTilesRespectKindAndGridBounds() {
        GridState grid = new GridState(5, 5);
        GridCoord origin = new GridCoord(2, 2);
        assertEquals(25, Targeting.targetAnchorTiles(grid, origin, move("Ranged", 2, null, null)).size());
        assertEquals(8, Targeting.targetAnchorTiles(grid, origin, move("Melee", 1, null, null)).size());
        assertEquals(Set.of(origin), Targeting.targetAnchorTiles(grid, origin, move("Self", 0, null, null)));
    }
}

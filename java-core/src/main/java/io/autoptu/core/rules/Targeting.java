package io.autoptu.core.rules;

import io.autoptu.core.model.GridCoord;
import io.autoptu.core.model.GridState;
import io.autoptu.core.model.MoveSpec;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Java parity port of auto_ptu/rules/targeting.py.
 *
 * Keep behavior aligned with the Python oracle. Do not "clean up" geometry semantics
 * unless the Python implementation and parity fixtures change first.
 */
public final class Targeting {
    private static final Pattern KIND_TOKEN = Pattern.compile("[a-z]+");

    private Targeting() {
    }

    public static String normalizedTargetKind(MoveSpec move) {
        return normalizeKind(firstNonBlank(move.targetKind(), move.rangeKind()), "ranged");
    }

    public static String normalizedAreaKind(MoveSpec move) {
        if (isBlank(move.areaKind())) {
            return "";
        }
        return normalizeKind(move.areaKind(), "ranged");
    }

    public static boolean moveRequiresTarget(MoveSpec move) {
        String kind = normalizedTargetKind(move);
        String area = normalizedAreaKind(move);
        if (kind.equals("field")) {
            return false;
        }
        if (Set.of("cone", "line", "closeblast").contains(area)) {
            return true;
        }
        return !kind.equals("self");
    }

    public static int moveRangeDistance(MoveSpec move) {
        String kind = normalizedTargetKind(move);
        if (kind.equals("self") || kind.equals("field")) {
            return 0;
        }
        if (nonZero(move.targetRange())) {
            return Math.max(1, move.targetRange());
        }
        if (nonZero(move.rangeValue())) {
            return Math.max(1, move.rangeValue());
        }
        return kind.equals("melee") ? 1 : 6;
    }

    public static int chebyshevDistance(GridCoord a, GridCoord b) {
        return Math.max(Math.abs(a.x() - b.x()), Math.abs(a.y() - b.y()));
    }

    public static int footprintSideForSize(String sizeLabel) {
        String label = sizeLabel == null ? "" : sizeLabel.strip().toLowerCase(Locale.ROOT);
        return switch (label) {
            case "large" -> 2;
            case "huge" -> 3;
            case "gigantic" -> 4;
            default -> 1;
        };
    }

    public static Set<GridCoord> footprintTiles(GridCoord anchor, String sizeLabel) {
        // Python intentionally does not clip footprints to the grid here.
        return squareTiles(anchor, footprintSideForSize(sizeLabel), null);
    }

    public static int footprintDistance(
            GridCoord aAnchor,
            String aSize,
            GridCoord bAnchor,
            String bSize
    ) {
        Set<GridCoord> aTiles = footprintTiles(aAnchor, aSize);
        Set<GridCoord> bTiles = footprintTiles(bAnchor, bSize);
        if (aTiles.isEmpty() || bTiles.isEmpty()) {
            return chebyshevDistance(aAnchor, bAnchor);
        }
        int minimum = Integer.MAX_VALUE;
        for (GridCoord aTile : aTiles) {
            for (GridCoord bTile : bTiles) {
                minimum = Math.min(minimum, chebyshevDistance(aTile, bTile));
            }
        }
        return minimum;
    }

    public static boolean isTargetInRange(
            GridCoord attackerPos,
            GridCoord targetPos,
            MoveSpec move,
            String attackerSize,
            String targetSize,
            GridState grid
    ) {
        String kind = normalizedTargetKind(move);
        String area = normalizedAreaKind(move);
        int distance;
        if (attackerSize != null || targetSize != null) {
            distance = footprintDistance(
                    attackerPos,
                    attackerSize == null ? "Medium" : attackerSize,
                    targetPos,
                    targetSize == null ? "Medium" : targetSize
            );
        } else {
            distance = chebyshevDistance(attackerPos, targetPos);
        }

        if (kind.equals("self")) {
            if (area.equals("line") || area.equals("cone")) {
                int maxDistance = Math.max(1, firstNonZero(move.areaValue(), move.targetRange(), move.rangeValue(), 1));
                return distance > 0 && distance <= maxDistance;
            }
            if (area.equals("closeblast")) {
                return distance == 1;
            }
            return attackerPos.equals(targetPos);
        }
        if (kind.equals("field")) {
            return true;
        }
        int maxDistance = moveRangeDistance(move);
        if (kind.equals("melee")) {
            return distance == 1;
        }
        return distance <= maxDistance;
    }

    public static Set<GridCoord> affectedTiles(
            GridState grid,
            GridCoord attackerPos,
            GridCoord targetPos,
            MoveSpec move
    ) {
        String areaKind = normalizedAreaKind(move);
        if (areaKind.isEmpty()) {
            return singleton(targetPos != null ? targetPos : attackerPos);
        }
        if (areaKind.equals("field")) {
            return allTiles(grid);
        }
        int radius = Math.max(0, intOrZero(move.areaValue()));
        return switch (areaKind) {
            case "burst" -> {
                GridCoord center = targetPos != null && !normalizedTargetKind(move).equals("self")
                        ? targetPos : attackerPos;
                yield burstTiles(center, radius, grid);
            }
            case "blast" -> squareTiles(targetPos != null ? targetPos : attackerPos, radius, grid);
            case "closeblast" -> closeBlastTiles(
                    attackerPos,
                    targetPos != null ? targetPos : attackerPos,
                    radius,
                    grid
            );
            case "line" -> targetPos == null
                    ? burstTiles(attackerPos, 0, grid)
                    : lineTiles(attackerPos, targetPos, Math.max(1, radius), grid);
            case "cone" -> targetPos == null
                    ? burstTiles(attackerPos, radius, grid)
                    : coneTiles(attackerPos, targetPos, Math.max(1, radius), grid);
            default -> singleton(targetPos != null ? targetPos : attackerPos);
        };
    }

    public static Set<GridCoord> targetAnchorTiles(GridState grid, GridCoord origin, MoveSpec move) {
        String area = normalizedAreaKind(move);
        if (area.equals("cone") || area.equals("line")) {
            int maxDistance = Math.max(1, firstNonZero(move.areaValue(), 1));
            String rangeText = firstNonBlank(move.rangeText(), move.rangeKind(), "").strip().toLowerCase(Locale.ROOT);
            if (rangeText.contains("pass")) {
                maxDistance = Math.max(maxDistance, moveRangeDistance(move));
            }
            Set<GridCoord> tiles = new LinkedHashSet<>();
            for (int x = origin.x() - maxDistance; x <= origin.x() + maxDistance; x++) {
                for (int y = origin.y() - maxDistance; y <= origin.y() + maxDistance; y++) {
                    GridCoord coord = new GridCoord(x, y);
                    if (grid != null && !grid.inBounds(coord)) {
                        continue;
                    }
                    if (coord.equals(origin)) {
                        continue;
                    }
                    if (chebyshevDistance(origin, coord) <= maxDistance) {
                        tiles.add(coord);
                    }
                }
            }
            return tiles;
        }

        if (area.equals("closeblast")) {
            Set<GridCoord> tiles = new LinkedHashSet<>();
            for (int x = origin.x() - 1; x <= origin.x() + 1; x++) {
                for (int y = origin.y() - 1; y <= origin.y() + 1; y++) {
                    GridCoord coord = new GridCoord(x, y);
                    if (coord.equals(origin)) {
                        continue;
                    }
                    if (grid != null && !grid.inBounds(coord)) {
                        continue;
                    }
                    if (chebyshevDistance(origin, coord) == 1) {
                        tiles.add(coord);
                    }
                }
            }
            return tiles;
        }

        String kind = normalizedTargetKind(move);
        if (kind.equals("self")) {
            return singleton(origin);
        }
        if (kind.equals("field")) {
            return allTiles(grid);
        }

        int maxDistance = moveRangeDistance(move);
        Set<GridCoord> tiles = new LinkedHashSet<>();
        for (int x = origin.x() - maxDistance; x <= origin.x() + maxDistance; x++) {
            for (int y = origin.y() - maxDistance; y <= origin.y() + maxDistance; y++) {
                GridCoord coord = new GridCoord(x, y);
                if (grid != null && !grid.inBounds(coord)) {
                    continue;
                }
                if (coord.equals(origin) && kind.equals("melee")) {
                    continue;
                }
                if (chebyshevDistance(origin, coord) <= maxDistance) {
                    tiles.add(coord);
                }
            }
        }
        return tiles;
    }

    public static boolean lineOfSightClear(
            GridState grid,
            GridCoord origin,
            GridCoord target,
            Set<GridCoord> blocking
    ) {
        if (grid == null || origin.equals(target)) {
            return true;
        }
        Set<GridCoord> blockers = blocking == null ? Set.of() : blocking;
        List<GridCoord> cells = bresenhamCells(origin, target);
        for (int i = 1; i < cells.size(); i++) {
            GridCoord coord = cells.get(i);
            if (coord.equals(target)) {
                break;
            }
            if (blockers.contains(coord)) {
                return false;
            }
        }
        return true;
    }

    static List<GridCoord> bresenhamCells(GridCoord start, GridCoord end) {
        int x0 = start.x();
        int y0 = start.y();
        int x1 = end.x();
        int y1 = end.y();
        int dx = Math.abs(x1 - x0);
        int dy = Math.abs(y1 - y0);
        int sx = x0 < x1 ? 1 : x0 > x1 ? -1 : 0;
        int sy = y0 < y1 ? 1 : y0 > y1 ? -1 : 0;
        int err = dx - dy;
        int x = x0;
        int y = y0;
        List<GridCoord> cells = new ArrayList<>();
        cells.add(new GridCoord(x, y));
        while (x != x1 || y != y1) {
            int e2 = 2 * err;
            if (e2 > -dy) {
                err -= dy;
                x += sx;
            }
            if (e2 < dx) {
                err += dx;
                y += sy;
            }
            cells.add(new GridCoord(x, y));
        }
        return cells;
    }

    private static Set<GridCoord> allTiles(GridState grid) {
        Set<GridCoord> tiles = new LinkedHashSet<>();
        if (grid == null) {
            return tiles;
        }
        for (int x = 0; x < grid.width(); x++) {
            for (int y = 0; y < grid.height(); y++) {
                tiles.add(new GridCoord(x, y));
            }
        }
        return tiles;
    }

    private static Set<GridCoord> burstTiles(GridCoord center, int radius, GridState grid) {
        Set<GridCoord> tiles = new LinkedHashSet<>();
        for (int dx = -radius; dx <= radius; dx++) {
            for (int dy = -radius; dy <= radius; dy++) {
                GridCoord coord = new GridCoord(center.x() + dx, center.y() + dy);
                if (grid != null && !grid.inBounds(coord)) {
                    continue;
                }
                if (chebyshevDistance(center, coord) <= radius) {
                    tiles.add(coord);
                }
            }
        }
        // Match Python: center is added even when it would otherwise be clipped.
        tiles.add(center);
        return tiles;
    }

    private static Set<GridCoord> squareTiles(GridCoord center, int size, GridState grid) {
        int side = Math.max(1, size);
        int offsetMin = -((side - 1) / 2);
        int offsetMax = side / 2;
        Set<GridCoord> tiles = new LinkedHashSet<>();
        for (int dx = offsetMin; dx <= offsetMax; dx++) {
            for (int dy = offsetMin; dy <= offsetMax; dy++) {
                GridCoord coord = new GridCoord(center.x() + dx, center.y() + dy);
                if (grid != null && !grid.inBounds(coord)) {
                    continue;
                }
                tiles.add(coord);
            }
        }
        return tiles;
    }

    private static Set<GridCoord> lineTiles(
            GridCoord origin,
            GridCoord target,
            int length,
            GridState grid
    ) {
        Set<GridCoord> tiles = new LinkedHashSet<>();
        GridCoord step = directionStep(origin, target);
        if (step.equals(new GridCoord(0, 0))) {
            return singleton(origin);
        }
        for (int distance = 1; distance <= length; distance++) {
            GridCoord coord = new GridCoord(
                    origin.x() + step.x() * distance,
                    origin.y() + step.y() * distance
            );
            if (grid != null && !grid.inBounds(coord)) {
                break;
            }
            tiles.add(coord);
        }
        return tiles;
    }

    private static Set<GridCoord> closeBlastTiles(
            GridCoord origin,
            GridCoord target,
            int size,
            GridState grid
    ) {
        int side = Math.max(1, size);
        GridCoord step = directionStep(origin, target);
        if (step.equals(new GridCoord(0, 0))) {
            return squareTiles(origin, side, grid);
        }
        GridCoord perp = new GridCoord(step.y(), -step.x());
        int offsetMin = -((side - 1) / 2);
        int offsetMax = side / 2;
        Set<GridCoord> tiles = new LinkedHashSet<>();
        for (int distance = 1; distance <= side; distance++) {
            GridCoord base = new GridCoord(
                    origin.x() + step.x() * distance,
                    origin.y() + step.y() * distance
            );
            for (int offset = offsetMin; offset <= offsetMax; offset++) {
                GridCoord coord = new GridCoord(
                        base.x() + perp.x() * offset,
                        base.y() + perp.y() * offset
                );
                if (grid != null && !grid.inBounds(coord)) {
                    continue;
                }
                tiles.add(coord);
            }
        }
        return tiles;
    }

    private static Set<GridCoord> coneTiles(
            GridCoord origin,
            GridCoord target,
            int radius,
            GridState grid
    ) {
        Set<GridCoord> tiles = new LinkedHashSet<>();
        GridCoord step = directionStep(origin, target);
        if (step.equals(new GridCoord(0, 0))) {
            return burstTiles(origin, radius, grid);
        }
        GridCoord perp = new GridCoord(step.y(), -step.x());
        for (int distance = 1; distance <= radius; distance++) {
            GridCoord center = new GridCoord(
                    origin.x() + step.x() * distance,
                    origin.y() + step.y() * distance
            );
            for (int offset : new int[]{-1, 0, 1}) {
                GridCoord coord = new GridCoord(
                        center.x() + perp.x() * offset,
                        center.y() + perp.y() * offset
                );
                if (grid != null && !grid.inBounds(coord)) {
                    continue;
                }
                tiles.add(coord);
            }
        }
        return tiles;
    }

    private static GridCoord directionStep(GridCoord origin, GridCoord target) {
        return new GridCoord(sign(target.x() - origin.x()), sign(target.y() - origin.y()));
    }

    private static int sign(int value) {
        return Integer.compare(value, 0);
    }

    private static String normalizeKind(String value, String defaultValue) {
        String selected = isBlank(value) ? defaultValue : value;
        String text = (selected == null ? "" : selected).toLowerCase(Locale.ROOT);
        Matcher matcher = KIND_TOKEN.matcher(text);
        if (matcher.find()) {
            return matcher.group();
        }
        return (defaultValue == null ? "ranged" : defaultValue).toLowerCase(Locale.ROOT);
    }

    private static boolean isBlank(String value) {
        return value == null || value.isBlank();
    }

    private static String firstNonBlank(String... values) {
        for (String value : values) {
            if (!isBlank(value)) {
                return value;
            }
        }
        return "";
    }

    private static boolean nonZero(Integer value) {
        return value != null && value != 0;
    }

    private static int intOrZero(Integer value) {
        return value == null ? 0 : value;
    }

    private static int firstNonZero(Integer... values) {
        for (Integer value : values) {
            if (value != null && value != 0) {
                return value;
            }
        }
        return 0;
    }

    private static Set<GridCoord> singleton(GridCoord coord) {
        Set<GridCoord> result = new LinkedHashSet<>();
        result.add(coord);
        return result;
    }
}

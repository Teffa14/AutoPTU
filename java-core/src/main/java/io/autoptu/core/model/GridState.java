package io.autoptu.core.model;

/** Minimal grid contract required by the first Java rules slice. */
public record GridState(int width, int height) {
    public GridState {
        if (width < 0 || height < 0) {
            throw new IllegalArgumentException("Grid dimensions cannot be negative.");
        }
    }

    public boolean inBounds(GridCoord coord) {
        return coord.x() >= 0 && coord.y() >= 0 && coord.x() < width && coord.y() < height;
    }
}

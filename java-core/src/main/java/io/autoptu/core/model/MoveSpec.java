package io.autoptu.core.model;

/**
 * First language-neutral subset of Python's MoveSpec needed by targeting.
 * Additional PTU move fields will be added only when the next ported subsystem requires them.
 */
public record MoveSpec(
        String targetKind,
        String rangeKind,
        Integer targetRange,
        Integer rangeValue,
        String areaKind,
        Integer areaValue,
        String rangeText
) {
}

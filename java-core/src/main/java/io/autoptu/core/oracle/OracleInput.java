package io.autoptu.core.oracle;

import java.util.Map;

/** Stable input envelope for Python-vs-Java parity fixtures. */
public record OracleInput(
        String rulesVersion,
        String schemaVersion,
        String rngVersion,
        String contentHash,
        long seed,
        Map<String, Object> battleSpec
) {
}

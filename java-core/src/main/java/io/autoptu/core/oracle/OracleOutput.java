package io.autoptu.core.oracle;

import java.util.List;
import java.util.Map;

/** Stable normalized output envelope used to compare Java against the Python oracle. */
public record OracleOutput(
        String eventSchemaVersion,
        Map<String, Object> initialState,
        List<Map<String, Object>> orderedEvents,
        Map<String, Object> finalState,
        String resultHash
) {
}

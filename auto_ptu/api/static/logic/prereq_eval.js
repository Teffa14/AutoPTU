(function () {
  function evaluatePrereq(entry, kind, handlers) {
    const prereq = String(entry?.prerequisites || "").trim();
    const statusInfo = typeof handlers?.prereqStatus === "function" ? handlers.prereqStatus(prereq, kind) : { status: "available", missing: [] };
    const allowed = typeof handlers?.isAllowed === "function" ? !!handlers.isAllowed(entry) : true;
    const missing = Array.isArray(statusInfo?.missing) ? statusInfo.missing.filter(Boolean) : [];
    const reason = missing.length
      ? `Missing prerequisite: ${missing.join(", ")}`
      : !allowed
      ? "Prerequisites not met."
      : "";
    return {
      status: statusInfo?.status || "available",
      allowed,
      missing,
      reason,
    };
  }

  function statusLabel(status) {
    if (status === "available") return "Available";
    if (status === "close") return "Close";
    if (status === "blocked") return "Locked";
    return "Unavailable";
  }

  window.PTUPrereqEval = {
    evaluatePrereq,
    statusLabel,
  };
})();

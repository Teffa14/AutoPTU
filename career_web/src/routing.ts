export function normalizeCareerBasePath(basePath: string): string {
  const trimmed = String(basePath || "/").trim();
  const withLeadingSlash = trimmed.startsWith("/") ? trimmed : `/${trimmed}`;
  const normalized = withLeadingSlash.replace(/\/+$/, "");
  return normalized || "";
}

export function careerPathFromLocation(pathname: string, basePath: string): string {
  const base = normalizeCareerBasePath(basePath);
  const path = String(pathname || "/");
  if (path === base || path === `${base}/`) return "";
  if (base && path.startsWith(`${base}/`)) return path.slice(base.length + 1);
  if (!base && path.startsWith("/")) return path.slice(1);
  return "";
}

export function careerNavigationTarget(path: string, basePath: string): string {
  const base = normalizeCareerBasePath(basePath);
  const suffix = String(path || "").replace(/^\/+/, "");
  return suffix ? `${base}/${suffix}` : `${base}/`;
}

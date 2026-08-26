const PRIMARY_UPSTREAM = "https://autoptu-career.vercel.app";
const FALLBACK_UPSTREAM = "https://autoptu-career-api.onrender.com";
const RANKED_ACCOUNT_DOMAIN = "ranked.autoptu.app";
const ALLOWED_ORIGINS = new Set([
  "https://teffa14.github.io",
  "http://127.0.0.1:5174",
  "http://localhost:5174",
]);

function cors(origin: string | null): HeadersInit {
  const allowed = origin && ALLOWED_ORIGINS.has(origin) ? origin : "https://teffa14.github.io";
  return {
    "Access-Control-Allow-Origin": allowed,
    "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Authorization,Content-Type,Idempotency-Key,X-Career-Identity,X-Career-Handle,X-Career-User",
    "Access-Control-Expose-Headers": "Content-Type,Retry-After,X-Career-Upstream",
    "Vary": "Origin",
  };
}

function suffixFor(url: URL): string {
  for (const prefix of ["/functions/v1/career-api", "/career-api"]) {
    if (url.pathname.startsWith(prefix)) {
      const suffix = url.pathname.slice(prefix.length);
      return suffix.startsWith("/") ? suffix : `/${suffix}`;
    }
  }
  return url.pathname.startsWith("/") ? url.pathname : `/${url.pathname}`;
}

function forwardedHeaders(req: Request): Headers {
  const headers = new Headers(req.headers);
  for (const key of ["host", "origin", "referer", "cf-connecting-ip", "x-forwarded-for", "apikey", "x-client-info"]) {
    headers.delete(key);
  }
  return headers;
}

function normalizeRankedId(value: unknown): string {
  const rankedId = String(value ?? "").trim().toLowerCase();
  if (!/^[a-z0-9][a-z0-9._-]{2,23}$/.test(rankedId)) {
    throw new Error("Ranked ID must be 3-24 characters using letters, numbers, dot, underscore or hyphen.");
  }
  return rankedId;
}

function rankedEmail(rankedId: string): string {
  return `${rankedId}@${RANKED_ACCOUNT_DOMAIN}`;
}

async function registerRankedAccount(req: Request, origin: string | null): Promise<Response> {
  try {
    const payload = await req.json() as { ranked_id?: unknown; password?: unknown };
    const rankedId = normalizeRankedId(payload.ranked_id);
    const password = String(payload.password ?? "");
    if (password.length < 8 || password.length > 72) {
      return jsonResponse({ detail: "Ranked password must be 8-72 characters." }, 400, origin);
    }

    const supabaseUrl = Deno.env.get("SUPABASE_URL")?.replace(/\/$/, "") ?? "";
    const serviceRole = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
    if (!supabaseUrl || !serviceRole) {
      return jsonResponse({ detail: "Ranked account service is not configured." }, 503, origin);
    }

    const created = await fetch(`${supabaseUrl}/auth/v1/admin/users`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${serviceRole}`,
        "apikey": serviceRole,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: rankedEmail(rankedId),
        password,
        email_confirm: true,
        user_metadata: { ranked_id: rankedId, account_kind: "career_ranked" },
      }),
    });

    if (!created.ok) {
      let detail = "Could not create ranked account.";
      try {
        const error = await created.json() as { message?: unknown; msg?: unknown; error_description?: unknown };
        detail = String(error.message ?? error.msg ?? error.error_description ?? detail);
      } catch {
        // Keep the generic message when GoTrue does not return JSON.
      }
      const duplicate = created.status === 422 && /already|registered|exists/i.test(detail);
      return jsonResponse({ detail: duplicate ? "Ranked ID is already registered." : detail }, duplicate ? 409 : created.status, origin);
    }

    return jsonResponse({ ranked_id: rankedId }, 201, origin);
  } catch (error) {
    return jsonResponse({ detail: error instanceof Error ? error.message : String(error) }, 400, origin);
  }
}

function jsonResponse(payload: unknown, status: number, origin: string | null): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { ...cors(origin), "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}

async function proxyTo(upstreamBase: string, req: Request, suffix: string, query: string) {
  const upstreamUrl = new URL(`${upstreamBase}${suffix || "/"}`);
  upstreamUrl.search = query;
  return await fetch(upstreamUrl, {
    method: req.method,
    headers: forwardedHeaders(req),
    body: req.method === "GET" || req.method === "HEAD" ? undefined : req.body,
    redirect: "follow",
  });
}

Deno.serve(async (req: Request) => {
  const origin = req.headers.get("origin");
  if (origin && !ALLOWED_ORIGINS.has(origin)) {
    return new Response("Forbidden origin", { status: 403, headers: cors(null) });
  }
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: cors(origin) });
  }

  const url = new URL(req.url);
  const suffix = suffixFor(url);
  if (suffix === "/auth/register") {
    if (req.method !== "POST") return jsonResponse({ detail: "Method not allowed." }, 405, origin);
    return await registerRankedAccount(req, origin);
  }

  let upstreamName = "vercel-api-fallback";
  try {
    let upstream = await proxyTo(PRIMARY_UPSTREAM, req, suffix, url.search);
    if (upstream.status === 404 && req.method === "GET" && suffix !== "/api/v1/catalog") {
      const renderAttempt = await proxyTo(FALLBACK_UPSTREAM, req, suffix, url.search);
      if (renderAttempt.status !== 404) {
        upstream = renderAttempt;
        upstreamName = "render";
      }
    }

    const body = await upstream.arrayBuffer();
    const responseHeaders = new Headers(cors(origin));
    const contentType = upstream.headers.get("content-type");
    if (contentType) responseHeaders.set("Content-Type", contentType);
    const retryAfter = upstream.headers.get("retry-after");
    if (retryAfter) responseHeaders.set("Retry-After", retryAfter);
    responseHeaders.set("X-Career-Upstream", upstreamName);
    responseHeaders.set("Cache-Control", "no-store");

    return new Response(body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    return jsonResponse({ detail: `Career API unavailable: ${String(error)}` }, 502, origin);
  }
});

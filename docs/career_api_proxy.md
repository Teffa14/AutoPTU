# Career browser API proxy

The GitHub Pages Career client uses the public Supabase Edge Function `career-api` as its browser-facing API origin.

The Edge Function accepts requests only from the AutoPTU GitHub Pages origin and local Career development origins, answers CORS preflight locally, forwards the original method/body/authentication headers server-to-server to the Render Career API, and returns the upstream response with browser-safe CORS headers.

This keeps the static GitHub Pages frontend independent of Render's browser CORS configuration while preserving the authoritative AutoPTU Career API as the upstream runtime.

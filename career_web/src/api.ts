import { authHeaders } from "./auth";
import type { BattleTranscript, CareerCatalog, CareerRun } from "./types";

const base = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ?? "";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const identity = await authHeaders();
  const response = await fetch(`${base}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...identity, ...(init.headers ?? {}) },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || `Request failed (${response.status})`);
  return payload as T;
}

export const careerApi = {
  catalog: (locale: string) => request<CareerCatalog>(`/api/v1/catalog?locale=${encodeURIComponent(locale)}`),
  create: (payload: Record<string, unknown>) => request<CareerRun>("/api/v1/runs", { method: "POST", body: JSON.stringify(payload) }),
  run: (id: string) => request<CareerRun>(`/api/v1/runs/${encodeURIComponent(id)}`),
  lineup: (run: CareerRun, pokemonIds: string[]) => request<CareerRun>(
    `/api/v1/runs/${encodeURIComponent(run.id)}/lineup`,
    {
      method: "POST",
      body: JSON.stringify({ expected_revision: run.revision, pokemon_ids: pokemonIds }),
    },
  ),
  decide: (run: CareerRun, optionId: string) => request<{ run: CareerRun; battle_ids: string[] }>(
    `/api/v1/runs/${encodeURIComponent(run.id)}/decisions`,
    {
      method: "POST",
      headers: { "Idempotency-Key": `${run.id}:${run.revision}:${optionId}` },
      body: JSON.stringify({ expected_revision: run.revision, option_id: optionId }),
    },
  ),
  battle: (runId: string, battleId: string) => request<BattleTranscript>(`/api/v1/runs/${encodeURIComponent(runId)}/battles/${encodeURIComponent(battleId)}`),
  retire: (runId: string) => request<CareerRun>(`/api/v1/runs/${encodeURIComponent(runId)}/retire`, { method: "POST", body: JSON.stringify({ reason: "voluntary" }) }),
  share: (runId: string) => request<{ url: string; include_replay: boolean }>(
    `/api/v1/runs/${encodeURIComponent(runId)}/shares`,
    { method: "POST", body: JSON.stringify({ include_replay: false }) },
  ),
  publicShare: (shareId: string) => request<{ share_id: string; summary: Record<string, unknown>; has_replay: boolean }>(`/api/v1/shares/${encodeURIComponent(shareId)}`),
  daily: (day: string) => request<Record<string, unknown>>(`/api/v1/daily/${day}`),
  dailyAttempt: (day: string, payload: Record<string, unknown>) => request<{ run: CareerRun; attempt_no: number }>(
    `/api/v1/daily/${day}/attempts`,
    { method: "POST", body: JSON.stringify(payload) },
  ),
  leaderboard: (day: string, mode: string) => request<Record<string, unknown>>(`/api/v1/daily/${day}/leaderboards/${mode}`),
};

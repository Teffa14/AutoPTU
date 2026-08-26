import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const publishable = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY as string | undefined;
export const supabase: SupabaseClient | null = url && publishable ? createClient(url, publishable, {
  auth: {
    autoRefreshToken: true,
    detectSessionInUrl: true,
    persistSession: true,
  },
}) : null;

const localUserKey = "autoptu-career-development-user";

export type CareerAuthMode = "public" | "casual" | "ranked";

export async function authHeaders(mode: CareerAuthMode = "casual"): Promise<Record<string, string>> {
  if (mode === "public") return {};
  if (mode === "casual") return localCareerHeaders();
  if (!supabase) return {};

  const { data } = await supabase.auth.getSession();
  const session = data.session;
  if (!session?.access_token || session.user.is_anonymous) return {};
  return { Authorization: `Bearer ${session.access_token}` };
}

export async function hasPersistentCareerAccount(): Promise<boolean> {
  if (!supabase) return false;
  const { data } = await supabase.auth.getSession();
  return Boolean(data.session?.access_token && !data.session.user.is_anonymous);
}

export async function signInWithPassword(email: string, password: string): Promise<void> {
  if (!supabase) throw new Error("Supabase Auth is not configured in this build.");
  const { error } = await supabase.auth.signInWithPassword({ email: email.trim(), password });
  if (error) throw error;
}

export async function signUpWithPassword(email: string, password: string): Promise<{ signedIn: boolean }> {
  if (!supabase) throw new Error("Supabase Auth is not configured in this build.");
  const { data, error } = await supabase.auth.signUp({ email: email.trim(), password });
  if (error) throw error;
  return { signedIn: Boolean(data.session?.access_token && !data.session.user.is_anonymous) };
}

export async function signInWithEmail(email: string): Promise<void> {
  if (!supabase) throw new Error("Supabase Auth is not configured in this build.");
  const { error } = await supabase.auth.signInWithOtp({ email, options: { emailRedirectTo: authReturnUrl() } });
  if (error) throw error;
}

export async function signInWithProvider(provider: "google" | "discord"): Promise<void> {
  if (!supabase) throw new Error("Supabase Auth is not configured in this build.");
  const { data: current } = await supabase.auth.getUser();
  const options = { redirectTo: authReturnUrl() };
  if (current.user?.is_anonymous) {
    const { error: linkError } = await supabase.auth.linkIdentity({ provider, options });
    if (!linkError) return;
    // Existing anonymous sessions from older builds can still be upgraded.
  }
  const { error } = await supabase.auth.signInWithOAuth({ provider, options });
  if (error) throw error;
}

export async function signOut(): Promise<void> {
  if (!supabase) return;
  const { error } = await supabase.auth.signOut();
  if (error) throw error;
}

function localCareerHeaders(): Record<string, string> {
  let developmentUser = localStorage.getItem(localUserKey);
  if (!developmentUser) {
    developmentUser = crypto.randomUUID();
    localStorage.setItem(localUserKey, developmentUser);
  }
  return { "X-Career-User": developmentUser };
}

export function authReturnUrlForLocation(origin: string, pathname: string, hash = ""): string {
  const marker = "/career-game";
  const markerIndex = pathname.indexOf(marker);
  const configuredBase = String(import.meta.env.BASE_URL || "/career-game/");
  const fallbackBase = configuredBase.endsWith("/") ? configuredBase : `${configuredBase}/`;
  const appBase = markerIndex >= 0 ? `${pathname.slice(0, markerIndex)}${marker}/` : fallbackBase;
  const routeHash = hash.startsWith("#/") ? hash : "";
  return `${origin}${appBase}${routeHash}`;
}

function authReturnUrl(): string {
  return authReturnUrlForLocation(window.location.origin, window.location.pathname, window.location.hash);
}

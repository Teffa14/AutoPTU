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

export async function authHeaders(): Promise<Record<string, string>> {
  if (supabase) {
    const { data } = await supabase.auth.getSession();
    if (data.session?.access_token) return { Authorization: `Bearer ${data.session.access_token}` };
  }
  return localCareerHeaders();
}

export async function hasPersistentCareerAccount(): Promise<boolean> {
  if (!supabase) return false;
  const { data } = await supabase.auth.getSession();
  return Boolean(data.session?.access_token && !data.session.user.is_anonymous);
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

function authReturnUrl(): string {
  const path = window.location.pathname.startsWith("/career-game/")
    ? window.location.pathname
    : "/career-game/";
  return `${window.location.origin}${path}`;
}

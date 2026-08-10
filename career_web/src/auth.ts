import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const publishable = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY as string | undefined;
export const supabase: SupabaseClient | null = url && publishable ? createClient(url, publishable) : null;

const localUserKey = "autoptu-career-development-user";

export async function authHeaders(): Promise<Record<string, string>> {
  if (supabase) {
    let { data } = await supabase.auth.getSession();
    if (!data.session) {
      await supabase.auth.signInAnonymously();
      data = (await supabase.auth.getSession()).data;
    }
    if (data.session?.access_token) return { Authorization: `Bearer ${data.session.access_token}` };
  }
  let developmentUser = localStorage.getItem(localUserKey);
  if (!developmentUser) {
    developmentUser = crypto.randomUUID();
    localStorage.setItem(localUserKey, developmentUser);
  }
  return { "X-Career-User": developmentUser };
}

export async function signInWithEmail(email: string): Promise<void> {
  if (!supabase) throw new Error("Supabase Auth is not configured in this build.");
  const { error } = await supabase.auth.signInWithOtp({ email, options: { emailRedirectTo: window.location.origin + "/career-game/" } });
  if (error) throw error;
}

export async function signInWithProvider(provider: "google" | "discord"): Promise<void> {
  if (!supabase) throw new Error("Supabase Auth is not configured in this build.");
  const { error } = await supabase.auth.signInWithOAuth({ provider, options: { redirectTo: window.location.origin + "/career-game/" } });
  if (error) throw error;
}

// Browser Supabase client. RLS applies: every query runs as the signed-in user.
// Generated credentials live in `.env` (see `.env.example`); never hardcode real keys here.
import { createClient } from "@supabase/supabase-js";

import type { Database } from "./types";

const SUPABASE_URL = import.meta.env["VITE_SUPABASE_URL"] as string | undefined;
const SUPABASE_KEY = import.meta.env["VITE_SUPABASE_PUBLISHABLE_KEY"] as string | undefined;

if (!SUPABASE_URL || !SUPABASE_KEY) {
  // Keep the public site renderable before credentials are configured; auth then
  // reports "not signed in" instead of crashing every route that mounts the provider.
  console.warn("[supabase] VITE_SUPABASE_URL / VITE_SUPABASE_PUBLISHABLE_KEY are not set.");
}

export const supabase = createClient<Database>(
  SUPABASE_URL ?? "https://placeholder.supabase.co",
  SUPABASE_KEY ?? "public-anon-key",
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  },
);

import { createClient } from '@supabase/supabase-js'

import { env } from '@/lib/env'

export const supabase = createClient(env.supabaseUrl, env.supabaseAnonKey)

export async function getAccessToken(): Promise<string | undefined> {
  const { data } = await supabase.auth.getSession()
  return data.session?.access_token
}

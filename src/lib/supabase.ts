console.log("ENV CHECK");
console.log(import.meta.env);

import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export async function invokeFunction<T>(
  name: string,
  body: Record<string, unknown> | FormData
): Promise<T> {
  const isFormData = body instanceof FormData

  const { data, error } = await supabase.functions.invoke(name, {
    body: isFormData ? body : JSON.stringify(body),
    headers: isFormData ? undefined : { 'Content-Type': 'application/json' },
  })

  if (error) throw new Error(error.message || 'Function invocation failed')
  return data as T
}

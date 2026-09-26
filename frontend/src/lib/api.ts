import { env } from '@/lib/env'
import { ApiError, request } from '@/lib/http'
import { getAccessToken } from '@/lib/supabase'

async function authHeaders(): Promise<Record<string, string>> {
  const token = await getAccessToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function call<T>(path: string, method: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { ...(await authHeaders()) }
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }
  return request<T>(`${env.apiBaseUrl}${path}`, { method, headers, body })
}

export const api = {
  get: <T>(path: string) => call<T>(path, 'GET'),
  post: <T>(path: string, body?: unknown) => call<T>(path, 'POST', body),
  put: <T>(path: string, body?: unknown) => call<T>(path, 'PUT', body),
  patch: <T>(path: string, body?: unknown) => call<T>(path, 'PATCH', body),
  delete: <T>(path: string) => call<T>(path, 'DELETE'),
}

export { ApiError }

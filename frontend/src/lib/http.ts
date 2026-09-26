const DEFAULT_TIMEOUT_MS = 15_000

export class ApiError extends Error {
  readonly status: number
  readonly isNetworkError: boolean
  readonly body: unknown

  constructor(message: string, options: { status: number; isNetworkError: boolean; body?: unknown }) {
    super(message)
    this.name = 'ApiError'
    this.status = options.status
    this.isNetworkError = options.isNetworkError
    this.body = options.body
  }
}

export interface RequestOptions {
  method?: string
  headers?: Record<string, string>
  body?: unknown
  timeoutMs?: number
}

async function parseBody(response: Response): Promise<unknown> {
  const text = await response.text()
  if (!text) return undefined
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

export async function request<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', headers = {}, body, timeoutMs = DEFAULT_TIMEOUT_MS } = options

  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), timeoutMs)

  let response: Response
  try {
    response = await fetch(url, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    })
  } catch (error) {
    throw new ApiError(error instanceof Error ? error.message : 'Network request failed', {
      status: 0,
      isNetworkError: true,
    })
  } finally {
    clearTimeout(timeout)
  }

  const data = await parseBody(response)

  if (!response.ok) {
    throw new ApiError(`Request failed with status ${response.status}`, {
      status: response.status,
      isNetworkError: false,
      body: data,
    })
  }

  return data as T
}

import { useCallback, useEffect, useState } from 'react'

import { listThreads, type ThreadSummary } from '@/lib/threads'

interface UseThreadsResult {
  threads: ThreadSummary[]
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
}

export function useThreads(): UseThreadsResult {
  const [threads, setThreads] = useState<ThreadSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setThreads(await listThreads())
    } catch {
      setError('Could not load conversations.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // Standard fetch-on-mount; react-hooks/set-state-in-effect flags this preset-wide
    // (fires on shadcn's own generated use-mobile.ts too), not specific to this code.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh()
  }, [refresh])

  return { threads, loading, error, refresh }
}

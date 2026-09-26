import type { UIMessage } from 'ai'

import { api } from '@/lib/api'

export interface ThreadSummary {
  id: string
  title: string | null
  createdAt: string
  updatedAt: string
}

interface ThreadWire {
  id: string
  title: string | null
  created_at: string
  updated_at: string
}

function fromWire(thread: ThreadWire): ThreadSummary {
  return { id: thread.id, title: thread.title, createdAt: thread.created_at, updatedAt: thread.updated_at }
}

export async function listThreads(): Promise<ThreadSummary[]> {
  const threads = await api.get<ThreadWire[]>('/chat/threads')
  return threads.map(fromWire)
}

export async function createThread(): Promise<ThreadSummary> {
  const thread = await api.post<ThreadWire>('/chat/threads', {})
  return fromWire(thread)
}

export async function getThreadMessages(threadId: string): Promise<UIMessage[]> {
  return api.get<UIMessage[]>(`/chat/threads/${threadId}/messages`)
}

import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport, type UIMessage } from 'ai'

import { MessageInput } from '@/components/chat/message-input'
import { MessageList } from '@/components/chat/message-list'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Spinner } from '@/components/ui/spinner'
import { env } from '@/lib/env'
import { getAccessToken } from '@/lib/supabase'
import { getThreadMessages } from '@/lib/threads'

function ChatThread({ threadId, initialMessages }: { threadId: string; initialMessages: UIMessage[] }) {
  const transport = useMemo(
    () =>
      new DefaultChatTransport({
        api: `${env.apiBaseUrl}/chat/stream`,
        headers: async (): Promise<Record<string, string>> => {
          const token = await getAccessToken()
          return token ? { Authorization: `Bearer ${token}` } : {}
        },
        body: { threadId },
      }),
    [threadId]
  )

  const { messages, sendMessage, status, error } = useChat({
    id: threadId,
    messages: initialMessages,
    transport,
  })

  const busy = status === 'submitted' || status === 'streaming'

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <MessageList messages={messages} />
      {error && (
        <div className="mx-auto w-full max-w-2xl px-4 pb-2">
          <Alert variant="destructive">
            <AlertDescription>{error.message}</AlertDescription>
          </Alert>
        </div>
      )}
      <MessageInput disabled={busy} onSend={(text) => sendMessage({ text })} />
    </div>
  )
}

export function ChatThreadPage() {
  const { threadId } = useParams<{ threadId: string }>()
  const [initialMessages, setInitialMessages] = useState<UIMessage[] | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    if (!threadId) return
    // Standard fetch-on-thread-change; react-hooks/set-state-in-effect flags this
    // preset-wide (fires on shadcn's own generated use-mobile.ts too), not specific
    // to this code.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setInitialMessages(null)
    setLoadError(null)
    getThreadMessages(threadId)
      .then(setInitialMessages)
      .catch(() => setLoadError('Could not load this conversation.'))
  }, [threadId])

  if (!threadId) return null

  if (loadError) {
    return (
      <div className="flex flex-1 items-center justify-center p-4">
        <Alert variant="destructive" className="max-w-sm">
          <AlertDescription>{loadError}</AlertDescription>
        </Alert>
      </div>
    )
  }

  if (initialMessages === null) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Spinner className="size-6" />
      </div>
    )
  }

  return <ChatThread key={threadId} threadId={threadId} initialMessages={initialMessages} />
}

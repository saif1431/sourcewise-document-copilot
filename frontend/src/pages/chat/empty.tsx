import { useNavigate } from 'react-router-dom'
import { MessageSquareIcon } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from '@/components/ui/empty'
import { createThread } from '@/lib/threads'

export function ChatEmptyState() {
  const navigate = useNavigate()

  async function handleNewChat() {
    const thread = await createThread()
    navigate(`/chats/${thread.id}`)
  }

  return (
    <Empty className="flex-1 border-none">
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <MessageSquareIcon />
        </EmptyMedia>
        <EmptyTitle>No conversation selected</EmptyTitle>
        <EmptyDescription>Pick a conversation from the sidebar, or start a new one.</EmptyDescription>
      </EmptyHeader>
      <EmptyContent>
        <Button onClick={handleNewChat}>New chat</Button>
      </EmptyContent>
    </Empty>
  )
}

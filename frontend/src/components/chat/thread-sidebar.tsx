import { Link, useNavigate, useParams } from 'react-router-dom'
import { PlusIcon } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar'
import { useThreads } from '@/hooks/use-threads'
import { createThread } from '@/lib/threads'

export function ThreadSidebar() {
  const { threadId } = useParams()
  const navigate = useNavigate()
  const { threads, loading, refresh } = useThreads()

  async function handleNewChat() {
    try {
      const thread = await createThread()
      await refresh()
      navigate(`/chats/${thread.id}`)
    } catch (error) {
      console.error('Failed to create a new thread', error)
    }
  }

  return (
    <Sidebar>
      <SidebarHeader>
        <Button onClick={handleNewChat} className="w-full justify-start">
          <PlusIcon data-icon="inline-start" />
          New chat
        </Button>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Conversations</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {!loading && threads.length === 0 && (
                <p className="px-2 py-1.5 text-sm text-muted-foreground">No conversations yet.</p>
              )}
              {threads.map((thread) => (
                <SidebarMenuItem key={thread.id}>
                  <SidebarMenuButton
                    render={<Link to={`/chats/${thread.id}`} />}
                    isActive={thread.id === threadId}
                  >
                    {thread.title ?? 'New conversation'}
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  )
}

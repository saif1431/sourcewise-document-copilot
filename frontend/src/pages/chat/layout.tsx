import { Outlet } from 'react-router-dom'

import { ThreadSidebar } from '@/components/chat/thread-sidebar'
import { SidebarInset, SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar'

export function ChatLayout() {
  return (
    <SidebarProvider>
      <ThreadSidebar />
      <SidebarInset>
        <header className="flex h-12 shrink-0 items-center gap-2 border-b px-3">
          <SidebarTrigger />
        </header>
        <Outlet />
      </SidebarInset>
    </SidebarProvider>
  )
}

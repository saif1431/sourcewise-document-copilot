import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from '@/components/protected-route'
import { TooltipProvider } from '@/components/ui/tooltip'
import { AuthProvider } from '@/lib/auth'
import { ChatEmptyState } from '@/pages/chat/empty'
import { ChatLayout } from '@/pages/chat/layout'
import { ChatThreadPage } from '@/pages/chat/thread'
import { SignInPage } from '@/pages/sign-in'
import { SignUpPage } from '@/pages/sign-up'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <TooltipProvider>
          <Routes>
            <Route path="/login" element={<SignInPage />} />
            <Route path="/signup" element={<SignUpPage />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<ChatLayout />}>
                <Route path="/chats" element={<ChatEmptyState />} />
                <Route path="/chats/:threadId" element={<ChatThreadPage />} />
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/chats" replace />} />
          </Routes>
        </TooltipProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App

import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { Spinner } from '@/components/ui/spinner'
import { useAuth } from '@/lib/use-auth'

export function ProtectedRoute() {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner className="size-6" />
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}

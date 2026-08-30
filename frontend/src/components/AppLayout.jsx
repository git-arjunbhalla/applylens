import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

function navClass({ isActive }) {
  return isActive ? 'underline' : 'hover:underline'
}

function AppLayout() {
  const { user, logout } = useAuth()

  return (
    <div>
      <header className="border-b border-neutral-200">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div className="flex flex-wrap items-center gap-6">
            <span className="font-semibold text-neutral-900">ApplyLens</span>
            <nav className="flex gap-4 text-sm text-neutral-800">
              <NavLink to="/" end className={navClass}>
                Dashboard
              </NavLink>
              <NavLink to="/applications" className={navClass}>
                Applications
              </NavLink>
            </nav>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <p className="text-sm text-neutral-600">You are signed in as {user.email}.</p>
            <button
              className="rounded border border-neutral-300 px-3 py-2 text-sm text-neutral-900"
              type="button"
              onClick={logout}
            >
              Log out
            </button>
          </div>
        </div>
      </header>
      <Outlet />
    </div>
  )
}

export default AppLayout

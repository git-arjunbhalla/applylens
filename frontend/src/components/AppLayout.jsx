import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import BrandMark from './BrandMark'
import { buttonClass } from './Button'
import ThemeToggle from './ThemeToggle'

function navClass({ isActive }) {
  return [
    'rounded-md px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent',
    isActive ? 'bg-accent-soft text-ink' : 'text-ink hover:bg-accent-soft/50',
  ].join(' ')
}

function AppLayout() {
  const { user, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <a
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-40 focus:rounded-md focus:bg-surface focus:px-3 focus:py-2"
        href="#main-content"
      >
        Skip to content
      </a>
      <header className="sticky top-0 z-30 border-b border-line bg-surface/90 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <BrandMark className="h-8 w-8 shrink-0 text-ink" />
            <span className="font-display text-lg font-semibold tracking-tight">ApplyLens</span>
            <nav className="ml-2 hidden items-center gap-1 md:flex" aria-label="Main">
              <NavLink to="/" end className={navClass} onClick={() => setMenuOpen(false)}>
                Dashboard
              </NavLink>
              <NavLink to="/applications" className={navClass} onClick={() => setMenuOpen(false)}>
                Applications
              </NavLink>
              <NavLink to="/analyze" className={navClass} onClick={() => setMenuOpen(false)}>
                Analyze
              </NavLink>
            </nav>
          </div>
          <div className="flex items-center gap-2">
            <p className="max-w-36 truncate text-sm text-muted sm:max-w-56" title={user.email}>
              You are signed in as {user.email}.
            </p>
            <ThemeToggle />
            <button className={buttonClass('secondary')} type="button" onClick={logout}>
              Log out
            </button>
            <button
              className={`${buttonClass('secondary', 'md:hidden')} min-h-10`}
              type="button"
              aria-expanded={menuOpen}
              aria-controls="mobile-nav"
              onClick={() => setMenuOpen((open) => !open)}
            >
              Menu
            </button>
          </div>
        </div>
        {menuOpen ? (
          <nav id="mobile-nav" className="border-t border-line px-4 py-3 md:hidden" aria-label="Main">
            <div className="flex flex-col gap-1">
              <NavLink to="/" end className={navClass} onClick={() => setMenuOpen(false)}>
                Dashboard
              </NavLink>
              <NavLink to="/applications" className={navClass} onClick={() => setMenuOpen(false)}>
                Applications
              </NavLink>
              <NavLink to="/analyze" className={navClass} onClick={() => setMenuOpen(false)}>
                Analyze
              </NavLink>
            </div>
          </nav>
        ) : null}
      </header>
      <div id="main-content">
        <Outlet />
      </div>
    </div>
  )
}

export default AppLayout

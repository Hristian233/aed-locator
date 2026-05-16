import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const navClass = ({ isActive }: { isActive: boolean }) =>
  `text-sm font-medium ${isActive ? 'text-teal-700' : 'text-slate-600 hover:text-teal-600'}`

export function Layout() {
  const { user, logout, isAdmin } = useAuth()

  return (
    <div className="flex min-h-screen flex-col">
      <header className="z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <Link to="/" className="flex items-center gap-2 font-bold text-slate-900">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-600 text-white">
              ♥
            </span>
            AED Locator
          </Link>
          <nav className="flex items-center gap-4" aria-label="Main">
            <NavLink to="/" className={navClass} end>
              Map
            </NavLink>
            <NavLink to="/submit" className={navClass}>
              Report AED
            </NavLink>
            {isAdmin && (
              <NavLink to="/admin" className={navClass}>
                Admin
              </NavLink>
            )}
            {user ? (
              <button
                type="button"
                onClick={logout}
                className="rounded-full border border-slate-200 px-3 py-1.5 text-sm text-slate-700"
              >
                Sign out
              </button>
            ) : (
              <NavLink to="/auth" className={navClass}>
                Sign in
              </NavLink>
            )}
          </nav>
        </div>
      </header>
      <main className="flex flex-1 flex-col">
        <Outlet />
      </main>
    </div>
  )
}

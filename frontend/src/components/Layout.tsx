import { Link, NavLink, Outlet } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../context/AuthContext'
import { LanguageSwitcher } from './LanguageSwitcher'

const navClass = ({ isActive }: { isActive: boolean }) =>
  `text-sm font-medium ${isActive ? 'text-teal-700' : 'text-slate-600 hover:text-teal-600'}`

export function Layout() {
  const { t } = useTranslation()
  const { user, logout, isAdmin } = useAuth()

  return (
    <div className="flex h-dvh flex-col overflow-hidden">
      <header className="z-20 shrink-0 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-2 px-4 py-3 sm:gap-4">
          <Link to="/" className="flex min-w-0 items-center gap-2 font-bold text-slate-900">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-teal-600 text-white">
              ♥
            </span>
            <span className="truncate">{t('app.title')}</span>
          </Link>
          <nav className="flex items-center gap-2 sm:gap-4" aria-label="Main">
            <NavLink to="/" className={navClass} end>
              {t('nav.map')}
            </NavLink>
            <NavLink to="/submit" className={navClass}>
              {t('nav.report')}
            </NavLink>
            {isAdmin && (
              <NavLink to="/admin" className={navClass}>
                {t('nav.admin')}
              </NavLink>
            )}
            <LanguageSwitcher />
            {user ? (
              <button
                type="button"
                onClick={logout}
                className="rounded-full border border-slate-200 px-3 py-1.5 text-sm text-slate-700"
              >
                {t('nav.signOut')}
              </button>
            ) : (
              <NavLink to="/auth" className={navClass}>
                {t('nav.signIn')}
              </NavLink>
            )}
          </nav>
        </div>
      </header>
      <main className="flex min-h-0 flex-1 flex-col">
        <Outlet />
      </main>
    </div>
  )
}

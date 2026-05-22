import { useState } from 'react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../context/AuthContext'
import { LanguageSwitcher } from './LanguageSwitcher'

const navClass = ({ isActive }: { isActive: boolean }) =>
  `block rounded-lg px-3 py-2 text-sm font-medium ${
    isActive ? 'bg-teal-50 text-teal-700' : 'text-slate-700 hover:bg-slate-100'
  }`

const desktopNavClass = ({ isActive }: { isActive: boolean }) =>
  `text-sm font-medium ${isActive ? 'text-teal-700' : 'text-slate-600 hover:text-teal-600'}`

function NavItems({
  isAdmin,
  user,
  logout,
  onNavigate,
  linkClass,
}: {
  isAdmin: boolean
  user: ReturnType<typeof useAuth>['user']
  logout: () => void
  onNavigate?: () => void
  linkClass: typeof navClass | typeof desktopNavClass
}) {
  const { t } = useTranslation()

  return (
    <>
      <NavLink to="/" className={linkClass} end onClick={onNavigate}>
        {t('nav.map')}
      </NavLink>
      <NavLink to="/submit" className={linkClass} onClick={onNavigate}>
        {t('nav.report')}
      </NavLink>
      {isAdmin && (
        <NavLink to="/admin" className={linkClass} onClick={onNavigate}>
          {t('nav.admin')}
        </NavLink>
      )}
      <div className={onNavigate ? 'px-3 py-1' : ''}>
        <LanguageSwitcher />
      </div>
      {user ? (
        <button
          type="button"
          onClick={() => {
            logout()
            onNavigate?.()
          }}
          className={
            onNavigate
              ? 'w-full rounded-lg border border-slate-200 px-3 py-2 text-left text-sm text-slate-700'
              : 'rounded-full border border-slate-200 px-3 py-1.5 text-sm text-slate-700'
          }
        >
          {t('nav.signOut')}
        </button>
      ) : (
        <NavLink to="/auth" className={linkClass} onClick={onNavigate}>
          {t('nav.signIn')}
        </NavLink>
      )}
    </>
  )
}

export function Layout() {
  const { t } = useTranslation()
  const { user, logout, isAdmin } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)

  const closeMenu = () => setMenuOpen(false)

  return (
    <div className="flex h-dvh flex-col overflow-hidden">
      <header className="relative z-30 shrink-0 border-b border-slate-200 bg-white">
        <div className="flex items-center justify-between gap-3 px-4 py-3">
          <Link
            to="/"
            className="flex min-w-0 items-center gap-2 font-bold text-slate-900"
            onClick={closeMenu}
          >
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-teal-600 text-white">
              ♥
            </span>
            <span className="truncate">{t('app.title')}</span>
          </Link>

          <button
            type="button"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-slate-700 hover:bg-slate-100 md:hidden"
            aria-label={menuOpen ? t('nav.menuClose') : t('nav.menuOpen')}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((open) => !open)}
          >
            {menuOpen ? (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className="h-6 w-6"
                aria-hidden
              >
                <path strokeLinecap="round" d="M6 6l12 12M18 6L6 18" />
              </svg>
            ) : (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className="h-6 w-6"
                aria-hidden
              >
                <path strokeLinecap="round" d="M4 7h16M4 12h16M4 17h16" />
              </svg>
            )}
          </button>

          <nav
            className="hidden items-center gap-4 md:flex"
            aria-label="Main"
          >
            <NavItems
              isAdmin={isAdmin}
              user={user}
              logout={logout}
              linkClass={desktopNavClass}
            />
          </nav>
        </div>

        {menuOpen && (
          <>
            <button
              type="button"
              className="fixed inset-0 z-40 bg-black/30 md:hidden"
              aria-label={t('nav.menuClose')}
              onClick={closeMenu}
            />
            <nav
              className="absolute right-0 top-full z-50 flex w-full flex-col gap-1 border-b border-slate-200 bg-white p-3 shadow-lg md:hidden"
              aria-label="Main"
            >
              <NavItems
                isAdmin={isAdmin}
                user={user}
                logout={logout}
                onNavigate={closeMenu}
                linkClass={navClass}
              />
            </nav>
          </>
        )}
      </header>
      <main className="flex min-h-0 flex-1 flex-col">
        <Outlet />
      </main>
    </div>
  )
}

import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import clsx from 'clsx'

const navItems = [
  { to: '/', label: 'Início', icon: '○' },
  { to: '/search', label: 'Pesquisar', icon: '◇' },
  { to: '/catalog', label: 'Catalogar', icon: '＋' },
]

export default function Layout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const initial = (user?.name || user?.login || '?').charAt(0).toUpperCase()

  return (
    <div className="min-h-screen flex bg-surface-50">
      <aside className="w-64 bg-slate-900 text-slate-200 flex flex-col">
        <div className="px-6 pt-7 pb-6">
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-semibold tracking-tight text-white">bibsimples</span>
          </div>
          <p className="mt-1 text-xs uppercase tracking-widest text-slate-500">
            Biblioteca
          </p>
        </div>

        <nav className="flex-1 px-3">
          <ul className="space-y-1">
            {navItems.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    clsx(
                      'flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-white/10 text-white'
                        : 'text-slate-400 hover:text-white hover:bg-white/5'
                    )
                  }
                >
                  <span className="text-base w-5 text-center text-slate-500">{item.icon}</span>
                  <span>{item.label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <div className="px-4 pb-5 pt-4 border-t border-white/5">
          <div className="flex items-center gap-3 mb-3 px-2">
            <div className="w-9 h-9 rounded-full bg-primary-600 text-white text-sm font-semibold flex items-center justify-center shrink-0">
              {initial}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {user?.name || user?.login || 'Usuário'}
              </p>
              <p className="text-xs text-slate-500 truncate">{user?.login}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full px-3 py-2 text-sm text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors text-left"
          >
            Sair
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-auto">
        <div className="max-w-6xl mx-auto px-8 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

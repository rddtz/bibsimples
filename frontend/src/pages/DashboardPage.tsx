import { Link } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

const greeting = () => {
  const h = new Date().getHours()
  if (h < 12) return 'Bom dia'
  if (h < 18) return 'Boa tarde'
  return 'Boa noite'
}

export default function DashboardPage() {
  const user = useAuthStore((state) => state.user)
  const firstName = (user?.name || user?.login || '').split(' ')[0]

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
          {greeting()}{firstName ? `, ${firstName}` : ''}
        </h1>
        <p className="mt-1 text-slate-500">
          O que você quer fazer hoje?
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <Link
          to="/search"
          className="group bg-white border border-surface-200 rounded-2xl p-6 hover:border-primary-300 hover:shadow-card-lg transition-all"
        >
          <div className="flex items-start gap-4">
            <div className="w-11 h-11 rounded-xl bg-primary-50 text-primary-600 flex items-center justify-center text-xl shrink-0 group-hover:bg-primary-100 transition-colors">
              ◇
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-900">Pesquisar acervo</h2>
              <p className="mt-1 text-sm text-slate-500">
                Encontre livros pelo título, autor ou assunto.
              </p>
            </div>
          </div>
        </Link>

        <Link
          to="/catalog"
          className="group bg-white border border-surface-200 rounded-2xl p-6 hover:border-primary-300 hover:shadow-card-lg transition-all"
        >
          <div className="flex items-start gap-4">
            <div className="w-11 h-11 rounded-xl bg-accent-50 text-accent-700 flex items-center justify-center text-xl shrink-0 group-hover:bg-accent-100 transition-colors">
              ＋
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-900">Catalogar livro</h2>
              <p className="mt-1 text-sm text-slate-500">
                Adicione um livro novo ou exemplares de um livro existente.
              </p>
            </div>
          </div>
        </Link>
      </div>

      <div className="bg-white border border-surface-200 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-slate-900">Estatísticas</h2>
          <span className="text-xs uppercase tracking-wider text-slate-400">
            em breve
          </span>
        </div>
        <div className="text-center text-slate-400 py-10">
          <p className="text-sm">
            Os relatórios de empréstimos aparecerão aqui assim que o módulo de
            circulação estiver pronto.
          </p>
        </div>
      </div>
    </div>
  )
}

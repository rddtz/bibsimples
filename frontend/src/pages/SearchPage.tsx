import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { searchApi } from '../services/api'

interface SearchResult {
  id: number
  title: string
  author: string
  database: string
  holdings_count: number
  holdings_available: number
  holdings_lent: number
}

interface SearchResponse {
  search: {
    record_count: number
    data: SearchResult[]
  }
}

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [submittedQuery, setSubmittedQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [totalCount, setTotalCount] = useState(0)

  const { mutate: runSearch, ...searchMutation } = useMutation({
    mutationFn: (q: string) => searchApi.search(q),
    onSuccess: (data: SearchResponse) => {
      setResults(data.search?.data || [])
      setTotalCount(data.search?.record_count || 0)
    },
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    const q = query.trim()
    if (!q) return
    setSubmittedQuery(q)
    runSearch(q)
  }

  const hasSearched = searchMutation.isSuccess || searchMutation.isError
  const showEmpty = hasSearched && !searchMutation.isPending && results.length === 0
  const showInitial = !hasSearched && !searchMutation.isPending

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
          Pesquisar
        </h1>
        <p className="mt-1 text-slate-500">
          Busque por título, autor ou termo no catálogo.
        </p>
      </div>

      <form onSubmit={handleSearch} className="mb-6">
        <div className="flex gap-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ex: Machado de Assis, Dom Casmurro…"
            className="flex-1 px-4 py-3 text-slate-900 bg-white border border-surface-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent shadow-card"
            autoFocus
          />
          <button
            type="submit"
            disabled={!query.trim() || searchMutation.isPending}
            className="px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-xl transition-colors disabled:opacity-60 disabled:cursor-not-allowed shadow-card"
          >
            {searchMutation.isPending ? 'Buscando…' : 'Buscar'}
          </button>
        </div>
      </form>

      {searchMutation.isError && (
        <div className="mb-6 p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl">
          <p className="text-sm font-medium">Não foi possível concluir a busca</p>
          <p className="text-xs mt-0.5 text-rose-600">
            {searchMutation.error?.message || 'Erro desconhecido'}
          </p>
        </div>
      )}

      {hasSearched && totalCount > 0 && (
        <p className="text-sm text-slate-500 mb-3">
          {totalCount} resultado{totalCount === 1 ? '' : 's'}
          {submittedQuery ? <> para <span className="text-slate-900 font-medium">"{submittedQuery}"</span></> : ''}
        </p>
      )}

      {results.length > 0 && (
        <div className="space-y-2">
          {results.map((r) => (
            <ResultRow key={r.id} record={r} />
          ))}
        </div>
      )}

      {showEmpty && (
        <div className="bg-white border border-surface-200 rounded-2xl py-16 text-center">
          <p className="text-3xl mb-3">📭</p>
          <p className="text-slate-700 font-medium">Nada encontrado</p>
          <p className="text-sm text-slate-500 mt-1">
            Não há resultados para
            {submittedQuery ? <> <span className="font-medium text-slate-700">"{submittedQuery}"</span></> : ' essa busca'}.
          </p>
        </div>
      )}

      {showInitial && (
        <div className="bg-white border border-surface-200 rounded-2xl py-16 text-center">
          <p className="text-3xl mb-3">◇</p>
          <p className="text-slate-700 font-medium">Comece digitando um termo acima</p>
          <p className="text-sm text-slate-500 mt-1">
            A busca cobre título, autor e outros campos do registro.
          </p>
        </div>
      )}
    </div>
  )
}

function ResultRow({ record }: { record: SearchResult }) {
  const total = record.holdings_count ?? 0
  const available = record.holdings_available ?? 0
  const status = available > 0 ? 'available' : total > 0 ? 'unavailable' : 'none'

  return (
    <div className="bg-white border border-surface-200 rounded-xl px-5 py-4 flex items-center gap-4 hover:border-primary-300 hover:shadow-card-lg transition-all">
      <div className="flex-1 min-w-0">
        <p className="font-medium text-slate-900 truncate">{record.title || 'Sem título'}</p>
        <p className="text-sm text-slate-500 truncate">{record.author || '—'}</p>
      </div>
      <div className="flex items-center gap-3 shrink-0">
        <div className="text-right text-xs text-slate-500">
          <p>
            <span className="text-slate-900 font-medium">{available}</span> disp.
            {' / '}
            <span className="text-slate-700 font-medium">{total}</span> total
          </p>
          {record.holdings_lent > 0 && (
            <p className="text-slate-400">
              {record.holdings_lent} emprestado{record.holdings_lent === 1 ? '' : 's'}
            </p>
          )}
        </div>
        <AvailabilityBadge status={status} />
      </div>
    </div>
  )
}

function AvailabilityBadge({ status }: { status: 'available' | 'unavailable' | 'none' }) {
  if (status === 'available') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-medium border border-emerald-100">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
        Disponível
      </span>
    )
  }
  if (status === 'unavailable') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 text-xs font-medium border border-amber-100">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
        Emprestado
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 text-slate-500 text-xs font-medium border border-slate-200">
      Sem exemplar
    </span>
  )
}

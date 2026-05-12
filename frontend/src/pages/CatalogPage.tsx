import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { catalogApi, utilsApi, SimilarRecord } from '../services/api'
import cddRaw from '../data/cddPresets.csv?raw'

const CDD_PRESETS = cddRaw
  .split('\n')
  .map((l) => l.trim())
  .filter((l) => l && !l.startsWith('#'))
  .map((l) => {
    const comma = l.indexOf(',')
    return { code: l.slice(0, comma).trim(), label: l.slice(comma + 1).trim() }
  })

interface CatalogResponse {
  record_id: number
  title: string
  author_name: string
  cdd: string
  cutter_code: string
  volume: string
  holdings_requested: number
  details_url: string
}

interface AddCopiesResult {
  record_id: number
  copies_added: number
  message: string
}

type ResultBanner =
  | { kind: 'created'; data: CatalogResponse }
  | { kind: 'copies'; data: AddCopiesResult; matched: SimilarRecord }
  | null

export default function CatalogPage() {
  const [authorName, setAuthorName] = useState('')
  const [title, setTitle] = useState('')
  const [cdd, setCdd] = useState('')
  const [cutterCode, setCutterCode] = useState('')
  const [copies, setCopies] = useState(1)
  const [volume, setVolume] = useState('')
  const [error, setError] = useState('')
  const [result, setResult] = useState<ResultBanner>(null)
  const [duplicates, setDuplicates] = useState<SimilarRecord[] | null>(null)
  const [checkStatus, setCheckStatus] = useState<'not_found' | null>(null)

  const cutterMutation = useMutation({
    mutationFn: (name: string) => utilsApi.generateCutter(name),
    onSuccess: (data) => {
      let code = data.cutter_code
      const t = title.trim()
      if (t && !code[code.length - 1]?.match(/[a-z]/)) {
        const articles = ['o ', 'a ', 'os ', 'as ', 'um ', 'uma ', 'the ', 'an ', 'a ']
        let tl = t.toLowerCase()
        for (const art of articles) {
          if (tl.startsWith(art)) { tl = tl.slice(art.length); break }
        }
        if (tl) code = `${code}${tl[0]}`
      }
      setCutterCode(code)
    },
  })

  const similarMutation = useMutation({
    mutationFn: () => catalogApi.findSimilar(title.trim(), authorName.trim()),
    onError: (err: Error) => setError(err.message || 'Erro ao verificar duplicatas'),
  })

  const createBookMutation = useMutation({
    mutationFn: () =>
      catalogApi.createBook({
        author_name: authorName.trim(),
        title: title.trim(),
        cdd: cdd.trim(),
        copies,
        cutter_code: cutterCode.trim() || undefined,
        volume: volume.trim() || undefined,
      }),
    onSuccess: (data: CatalogResponse) => {
      setError('')
      setDuplicates(null)
      setResult({ kind: 'created', data })
      setTitle('')
    },
    onError: (err: Error) => {
      setResult(null)
      setError(err.message || 'Erro ao catalogar livro')
    },
  })

  const addCopiesMutation = useMutation({
    mutationFn: ({ record, qty }: { record: SimilarRecord; qty: number }) =>
      catalogApi.addCopies(record.id, qty),
    onSuccess: (data: AddCopiesResult, variables) => {
      setError('')
      setDuplicates(null)
      setResult({ kind: 'copies', data, matched: variables.record })
      setTitle('')
    },
    onError: (err: Error) => setError(err.message || 'Erro ao adicionar exemplares'),
  })

  const handleGenerateCutter = () => {
    const normalized = authorName.trim()
    if (normalized) cutterMutation.mutate(normalized)
  }

  const handleCheckExists = async () => {
    if (!title.trim()) return
    setCheckStatus(null)
    setError('')
    try {
      const similar = await similarMutation.mutateAsync()
      if (similar.matches.length > 0) {
        setDuplicates(similar.matches)
      } else {
        setCheckStatus('not_found')
      }
    } catch {
      // error handled by similarMutation.onError
    }
  }

  const handleClear = () => {
    setAuthorName('')
    setTitle('')
    setCdd('')
    setCutterCode('')
    setCopies(1)
    setVolume('')
    setError('')
    setResult(null)
    setDuplicates(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setResult(null)
    if (!authorName.trim() || !title.trim() || !cdd.trim() || copies < 1) return
    try {
      const similar = await similarMutation.mutateAsync()
      if (similar.matches.length > 0) {
        setDuplicates(similar.matches)
      } else {
        createBookMutation.mutate()
      }
    } catch {
      // error handled by similarMutation.onError
    }
  }

  const handleProceedAsNew = () => {
    setDuplicates(null)
    createBookMutation.mutate()
  }

  const isWorking =
    similarMutation.isPending ||
    createBookMutation.isPending ||
    addCopiesMutation.isPending

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
          Catalogar
        </h1>
        <p className="mt-1 text-slate-500">
          Antes de salvar, verificamos se o livro já existe no acervo.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-3 bg-white border border-surface-200 rounded-2xl p-7">
          <h2 className="text-base font-semibold text-slate-900 mb-1">
            Dados do livro
          </h2>
          <p className="text-sm text-slate-500 mb-6">
            Preencha autor, título e classificação. Cutter pode ser gerado.
          </p>

          <form className="space-y-5" onSubmit={handleSubmit}>
            <Field label="Nome do autor" required>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={authorName}
                  onChange={(e) => setAuthorName(e.target.value)}
                  placeholder="Machado de Assis"
                  className={inputClass}
                  required
                />
                <button
                  type="button"
                  onClick={handleGenerateCutter}
                  disabled={!authorName.trim() || cutterMutation.isPending}
                  className="px-3.5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg transition-colors disabled:opacity-60 disabled:cursor-not-allowed whitespace-nowrap"
                >
                  {cutterMutation.isPending ? 'Gerando…' : 'Gerar Cutter'}
                </button>
              </div>
            </Field>

            <Field label="Título do livro" required>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={title}
                  onChange={(e) => { setTitle(e.target.value); setCheckStatus(null) }}
                  placeholder="Dom Casmurro"
                  className={inputClass}
                  required
                />
                <button
                  type="button"
                  onClick={handleCheckExists}
                  disabled={!title.trim() || similarMutation.isPending}
                  className="px-3.5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg transition-colors disabled:opacity-60 disabled:cursor-not-allowed whitespace-nowrap"
                >
                  {similarMutation.isPending ? 'Buscando…' : 'Verificar'}
                </button>
              </div>
              {checkStatus === 'not_found' && (
                <p className="mt-1.5 text-sm text-slate-500 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 inline-block" />
                  Não encontrado no acervo — pode catalogar como novo.
                </p>
              )}
            </Field>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <Field label="Cutter">
                <input
                  type="text"
                  value={cutterCode}
                  onChange={(e) => setCutterCode(e.target.value)}
                  placeholder="M149"
                  className={inputClass}
                />
              </Field>

              <Field label="CDD" required>
                <CddSelect value={cdd} onChange={setCdd} />
              </Field>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <Field label="Quantos exemplares" required>
                <input
                  type="number"
                  min={1}
                  value={copies}
                  onChange={(e) => setCopies(Math.max(1, Number(e.target.value) || 1))}
                  className={inputClass}
                  required
                />
              </Field>

              <Field label="Volume (opcional)">
                <input
                  type="text"
                  value={volume}
                  onChange={(e) => setVolume(e.target.value)}
                  placeholder="v.1"
                  className={inputClass}
                />
              </Field>
            </div>

            <div className="pt-2 flex gap-3">
              <button
                type="button"
                onClick={handleClear}
                disabled={isWorking}
                className="px-4 py-3 bg-white border border-slate-300 hover:border-slate-400 text-slate-600 font-medium rounded-lg transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
              >
                Limpar
              </button>
              <button
                type="submit"
                disabled={
                  !authorName.trim() ||
                  !title.trim() ||
                  !cdd.trim() ||
                  copies < 1 ||
                  isWorking
                }
                className="flex-1 py-3 bg-primary-600 hover:bg-primary-700 active:bg-primary-800 text-white font-medium rounded-lg transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {similarMutation.isPending
                  ? 'Verificando…'
                  : createBookMutation.isPending
                  ? 'Catalogando…'
                  : 'Catalogar'}
              </button>
            </div>
          </form>
        </div>

        <aside className="lg:col-span-2 space-y-4">
          {error && (
            <div className="bg-rose-50 border border-rose-200 text-rose-700 rounded-xl p-4 text-sm">
              <p className="font-medium">Erro</p>
              <p className="mt-0.5 text-rose-600">{error}</p>
            </div>
          )}

          {result?.kind === 'created' && (
            <SuccessCard
              title="Livro catalogado"
              recordId={result.data.record_id}
              detailsUrl={result.data.details_url}
              fields={[
                ['Título', result.data.title],
                ['Autor', result.data.author_name],
                ['CDD', result.data.cdd],
                ['Cutter', result.data.cutter_code],
                ['Exemplares', String(result.data.holdings_requested)],
                ...(result.data.volume ? ([['Volume', result.data.volume]] as [string, string][]) : []),
              ]}
            />
          )}

          {result?.kind === 'copies' && (
            <SuccessCard
              title="Exemplares adicionados"
              recordId={result.matched.id}
              detailsUrl=""
              fields={[
                ['Registro', result.matched.title],
                ['Autor', result.matched.author],
                ['Adicionados agora', String(result.data.copies_added)],
              ]}
            />
          )}

          <div className="bg-primary-50/60 border border-primary-100 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-primary-900 mb-2">Como funciona</h3>
            <ul className="text-sm text-primary-900/80 space-y-1.5">
              <li>1. Preencha os dados e clique em <em>Catalogar</em>.</li>
              <li>2. Procuramos livros parecidos no acervo.</li>
              <li>3. Se encontrarmos, você pode adicionar exemplares ao registro existente — sem duplicar.</li>
            </ul>
          </div>
        </aside>
      </div>

      {duplicates && (
        <DuplicatesModal
          duplicates={duplicates}
          initialCopies={copies}
          onAddCopies={(record, qty) => addCopiesMutation.mutate({ record, qty })}
          onProceedAsNew={handleProceedAsNew}
          onClose={() => setDuplicates(null)}
          working={addCopiesMutation.isPending || createBookMutation.isPending}
        />
      )}
    </div>
  )
}

const inputClass =
  'w-full px-3.5 py-2.5 text-slate-900 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition'


function CddSelect({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const isPreset = CDD_PRESETS.some((p) => p.code === value)
  const [mode, setMode] = useState<'text' | 'list'>(isPreset ? 'list' : 'text')

  if (mode === 'list') {
    return (
      <div className="flex gap-2">
        <select
          value={value}
          onChange={(e) => {
            onChange(e.target.value)
          }}
          className={inputClass}
          required
        >
          <option value="">Selecione a categoria…</option>
          {CDD_PRESETS.map((p) => (
            <option key={p.code} value={p.code}>
              {p.code} — {p.label}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={() => { onChange(''); setMode('text') }}
          className="px-3.5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg transition-colors whitespace-nowrap"
        >
          ← Digitar
        </button>
      </div>
    )
  }

  const [open, setOpen] = useState(false)
  const suggestions = value.trim()
    ? CDD_PRESETS.filter(
        (p) =>
          p.code.toLowerCase().includes(value.toLowerCase()) ||
          p.label.toLowerCase().includes(value.toLowerCase())
      )
    : []

  return (
    <div className="flex gap-2">
      <div className="relative flex-1">
        <input
          type="text"
          value={value}
          onChange={(e) => { onChange(e.target.value); setOpen(true) }}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
          placeholder="Ex: 869.0(81)"
          className={inputClass}
          required
        />
        {open && suggestions.length > 0 && (
          <ul className="absolute z-20 mt-1 w-full bg-white border border-slate-200 rounded-lg shadow-lg max-h-56 overflow-auto">
            {suggestions.map((p) => (
              <li
                key={p.code}
                onMouseDown={() => { onChange(p.code); setOpen(false) }}
                className="px-3.5 py-2.5 cursor-pointer hover:bg-primary-50 flex items-baseline gap-2"
              >
                <span className="text-sm font-medium text-slate-900 shrink-0">{p.code}</span>
                <span className="text-xs text-slate-500 truncate">{p.label}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
      <button
        type="button"
        onClick={() => { onChange(''); setMode('list') }}
        className="px-3.5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg transition-colors whitespace-nowrap"
      >
        Ver lista
      </button>
    </div>
  )
}

function Field({
  label,
  required,
  children,
}: {
  label: string
  required?: boolean
  children: React.ReactNode
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-1.5">
        {label}
        {required && <span className="text-rose-500 ml-0.5">*</span>}
      </label>
      {children}
    </div>
  )
}

function SuccessCard({
  title,
  recordId,
  detailsUrl,
  fields,
}: {
  title: string
  recordId: number
  detailsUrl: string
  fields: [string, string][]
}) {
  return (
    <div className="bg-white border border-emerald-200 rounded-2xl p-5">
      <div className="flex items-center gap-2 mb-3">
        <span className="w-2 h-2 rounded-full bg-emerald-500" />
        <p className="text-sm font-semibold text-emerald-700">{title}</p>
        <span className="ml-auto text-xs text-slate-400">#{recordId}</span>
      </div>
      <dl className="text-sm space-y-1.5">
        {fields.map(([k, v]) => (
          <div key={k} className="flex gap-2">
            <dt className="text-slate-500 shrink-0 w-28">{k}</dt>
            <dd className="text-slate-900 truncate">{v || '—'}</dd>
          </div>
        ))}
      </dl>
      {detailsUrl && (
        <a
          href={detailsUrl}
          target="_blank"
          rel="noreferrer"
          className="inline-block mt-3 text-sm text-primary-700 hover:text-primary-800 font-medium"
        >
          Abrir no Biblivre →
        </a>
      )}
    </div>
  )
}

function DuplicatesModal({
  duplicates,
  initialCopies,
  onAddCopies,
  onProceedAsNew,
  onClose,
  working,
}: {
  duplicates: SimilarRecord[]
  initialCopies: number
  onAddCopies: (record: SimilarRecord, qty: number) => void
  onProceedAsNew: () => void
  onClose: () => void
  working: boolean
}) {
  const [qty, setQty] = useState(initialCopies)

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm"
      onClick={() => !working && onClose()}
    >
      <div
        className="bg-white w-full max-w-2xl rounded-2xl shadow-card-lg max-h-[85vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 pt-6 pb-4 border-b border-surface-200">
          <h2 className="text-lg font-semibold text-slate-900">
            Encontramos {duplicates.length} registro{duplicates.length === 1 ? '' : 's'} parecido{duplicates.length === 1 ? '' : 's'}
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Esse livro já está no acervo? Adicione exemplares ao registro existente em vez de duplicar.
          </p>
          <div className="mt-4 flex items-center gap-3">
            <span className="text-sm font-medium text-slate-700">Exemplares a adicionar:</span>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => setQty(q => Math.max(1, q - 1))}
                disabled={working || qty <= 1}
                className="w-8 h-8 flex items-center justify-center rounded-lg border border-slate-300 hover:bg-slate-50 text-slate-600 font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                −
              </button>
              <input
                type="number"
                min={1}
                max={999}
                value={qty}
                onChange={(e) => setQty(Math.max(1, Number(e.target.value) || 1))}
                disabled={working}
                className="w-16 text-center px-2 py-1.5 text-slate-900 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
              />
              <button
                type="button"
                onClick={() => setQty(q => q + 1)}
                disabled={working}
                className="w-8 h-8 flex items-center justify-center rounded-lg border border-slate-300 hover:bg-slate-50 text-slate-600 font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                +
              </button>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-auto px-3 py-2">
          <ul className="divide-y divide-surface-200">
            {duplicates.map((d) => (
              <li key={d.id} className="px-3 py-3 flex items-center gap-3">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-slate-900 truncate">{d.title || 'Sem título'}</p>
                  <p className="text-sm text-slate-500 truncate">{d.author || '—'}</p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Hoje: {d.holdings_available}/{d.holdings_count} exemplar{d.holdings_count === 1 ? '' : 'es'} disponíveis
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => onAddCopies(d, qty)}
                  disabled={working}
                  className="shrink-0 px-3.5 py-2 text-sm font-medium bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  + {qty} exemplar{qty === 1 ? '' : 'es'} aqui
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className="px-6 py-4 border-t border-surface-200 bg-surface-50 flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={working}
            className="text-sm text-slate-500 hover:text-slate-900 transition-colors"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={onProceedAsNew}
            disabled={working}
            className="px-3.5 py-2 text-sm font-medium bg-white border border-slate-300 hover:border-slate-400 text-slate-700 rounded-lg transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
          >
            Não — é livro diferente, catalogar como novo
          </button>
        </div>
      </div>
    </div>
  )
}

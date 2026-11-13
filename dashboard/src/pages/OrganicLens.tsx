import { useState } from 'react'
import { Leaf } from 'lucide-react'
import { num, pct, useNarrativas, useResumen } from '../data'
import type { Narrativa } from '../types'
import { Cargando, Encabezado, ErrorCarga, Tarjeta } from '../ui'

export function Serie({ serie, alto = 80 }: { serie: Narrativa['serie']; alto?: number }) {
  const max = Math.max(1, ...serie.map((d) => d.total))
  return (
    <div>
      <div className="flex items-end gap-1" style={{ height: alto }}>
        {serie.map((d) => (
          <div key={d.dia} className="relative flex-1" style={{ height: '100%' }} title={`${d.dia}: ${num(d.total)} total · ${num(d.organico)} sin coordinación detectada`}>
            <div className="absolute bottom-0 w-full rounded-t bg-rose-300" style={{ height: `${(100 * d.total) / max}%` }} />
            <div className="absolute bottom-0 w-full rounded-t bg-emerald-500" style={{ height: `${(100 * d.organico) / max}%` }} />
          </div>
        ))}
      </div>
      <div className="mt-1 flex justify-between text-xs text-slate-500"><span>{serie[0]?.dia.slice(5)}</span><span>{serie[serie.length - 1]?.dia.slice(5)}</span></div>
    </div>
  )
}

export default function OrganicLens() {
  const { data: datos, error: errorNarrativas, reintentar: reintentarNarrativas } = useNarrativas()
  const { data: r, error: errorResumen, reintentar: reintentarResumen } = useResumen()
  const [sel, setSel] = useState<string | null>(null)
  if (errorNarrativas || errorResumen) {
    return <ErrorCarga onRetry={() => {
      if (errorNarrativas) reintentarNarrativas()
      if (errorResumen) reintentarResumen()
    }} />
  }
  if (!datos || !r) return <Cargando />
  const lista = [...datos].sort((a, b) => b.coordinados / Math.max(b.total, 1) - a.coordinados / Math.max(a.total, 1))
  if (lista.length === 0) {
    return (
      <div className="mx-auto max-w-7xl space-y-6">
        <Encabezado titulo="Organic Lens" sub="Compará la conversación total con la conversación que queda al excluir cuentas con indicios de coordinación." icono={<Leaf className="h-7 w-7" />} />
        <Tarjeta className="p-8 text-lg">No hay narrativas para comparar.</Tarjeta>
      </div>
    )
  }
  const n = lista.find((x) => x.narrativa === sel) ?? lista[0]
  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <Encabezado titulo="Organic Lens" sub="Compará la conversación total con la conversación que queda al excluir cuentas con indicios de coordinación." icono={<Leaf className="h-7 w-7" />} />
      <div className="grid gap-6 lg:grid-cols-[380px_minmax(0,1fr)]">
        <Tarjeta className="p-4">
          <div className="space-y-2">
            {lista.map((x) => {
              const f = x.coordinados / Math.max(x.total, 1)
              return (
                <button key={x.narrativa} onClick={() => setSel(x.narrativa)} className={`w-full rounded-2xl p-3 text-left ring-1 transition ${n.narrativa === x.narrativa ? 'bg-emerald-50 ring-emerald-400' : 'ring-slate-200 hover:bg-slate-50'}`}>
                  <div className="line-clamp-2 font-semibold leading-snug">{x.titulo}</div>
                  <div className={`mt-1 text-sm ${f > 0.02 ? 'font-semibold text-rose-600' : 'text-slate-500'}`}>{pct(x.coordinados, x.total)} coordinado · {num(x.total)} comentarios</div>
                </button>
              )
            })}
          </div>
        </Tarjeta>
        <Tarjeta className="space-y-6 p-6">
          <h2 className="text-2xl font-bold leading-snug">«{n.titulo}»</h2>
          <div className="grid gap-4 sm:grid-cols-3">
            <Cifra t="Actividad total" v={num(n.total)} c="bg-slate-50" />
            <Cifra t="Actividad sin coordinación detectada" v={num(n.organico_total)} c="bg-emerald-50 text-emerald-800" />
            <Cifra t="De cuentas coordinadas" v={`${num(n.coordinados)} (${pct(n.coordinados, n.total)})`} c="bg-rose-50 text-rose-800" />
          </div>
          <div>
            <div className="mb-2 flex gap-4 text-sm"><span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded bg-emerald-500" />Sin coordinación detectada</span><span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded bg-rose-300" />Aporte coordinado</span></div>
            <Serie serie={n.serie} alto={220} />
          </div>
          <p className="text-lg text-slate-600">
            {n.coordinados / Math.max(n.total, 1) > 0.02
              ? 'Una parte visible proviene de cuentas coordinadas; sin ellas, el alcance es menor al que aparenta.'
              : 'NEXO ENGINE marcó poca o ninguna actividad coordinada en esta narrativa.'}
          </p>
          <p className="text-sm text-slate-500">Excluir la coordinación detectada no garantiza que el resto sea genuino: solo descuenta las cuentas que NEXO ENGINE marcó.</p>
          <p className="text-sm text-slate-500">En todo el dataset: {num(r.cuentas_coordinadas)} cuentas coordinadas en {num(r.grupos_coordinados)} operaciones.</p>
        </Tarjeta>
      </div>
    </div>
  )
}

function Cifra({ t, v, c }: { t: string; v: string; c: string }) {
  return (
    <div className={`rounded-2xl p-4 ${c}`}>
      <div className="text-sm font-medium opacity-80">{t}</div>
      <div className="mt-1 text-2xl font-bold">{v}</div>
    </div>
  )
}

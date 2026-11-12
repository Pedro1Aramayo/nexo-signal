import { Link } from 'react-router-dom'
import { Layers, ThumbsUp, ThumbsDown, Clock } from 'lucide-react'
import { fecha, num, pct, useNarrativas } from '../data'
import { Cargando, Encabezado, Tarjeta } from '../ui'
import { Serie } from './OrganicLens'

export default function Narrativas() {
  const { datos } = useNarrativas()
  if (!datos) return <Cargando />
  const lista = [...datos].sort((a, b) => b.total - a.total)
  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <Encabezado titulo="Narrativas" sub="Afirmaciones que se repiten con distintas palabras, detectadas automáticamente por NEXO ENGINE." icono={<Layers className="h-7 w-7" />} />
      <div className="grid gap-5 lg:grid-cols-2">
        {lista.map((n) => {
          const t = Math.max(n.apoya + n.rechaza, 1)
          return (
            <Tarjeta key={n.narrativa} className="space-y-4 p-6">
              <div className="flex items-start justify-between gap-4">
                <h2 className="text-xl font-bold leading-snug">«{n.titulo}»</h2>
                <span className="shrink-0 rounded-full bg-indigo-50 px-3 py-1 font-semibold text-indigo-700">{num(n.total)}</span>
              </div>
              <div className="flex flex-wrap gap-2">{n.frases_clave.slice(0, 5).map((f) => <span key={f} className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700">{f}</span>)}</div>
              <div>
                <div className="flex h-3 overflow-hidden rounded-full bg-slate-100">
                  <div className="bg-emerald-500" style={{ width: `${(100 * n.apoya) / t}%` }} />
                  <div className="bg-rose-500" style={{ width: `${(100 * n.rechaza) / t}%` }} />
                </div>
                <div className="mt-2 flex justify-between">
                  <span className="flex items-center gap-1.5 text-emerald-700"><ThumbsUp className="h-4 w-4" /> Apoya {pct(n.apoya, t)}</span>
                  <span className="flex items-center gap-1.5 text-rose-700">Rechaza {pct(n.rechaza, t)} <ThumbsDown className="h-4 w-4" /></span>
                </div>
              </div>
              <Serie serie={n.serie} />
              <div className="flex flex-wrap items-center justify-between gap-2 text-slate-600">
                <span className="flex items-center gap-1.5"><Clock className="h-4 w-4" /> Origen: {fecha(n.fecha_origen)}</span>
                {n.publicaciones_top[0] && <Link to={`/publicacion/${n.publicaciones_top[0].publicacion_id}`} className="font-semibold text-indigo-700 hover:underline">Publicación donde más aparece →</Link>}
              </div>
            </Tarjeta>
          )
        })}
      </div>
    </div>
  )
}

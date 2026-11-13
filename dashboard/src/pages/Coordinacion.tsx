import { Link } from 'react-router-dom'
import { Network, Users, Moon, CalendarClock, Quote } from 'lucide-react'
import { num, useGrupos, useNarrativas } from '../data'
import { Avatar, Cargando, Encabezado, ErrorCarga, Tarjeta } from '../ui'

const CANAL: Record<string, string> = {
  T: 'Actividad sincronizada: comentan las mismas publicaciones o repiten textos con minutos de diferencia',
  R: 'Red de respuestas: las mismas cuentas se responden entre sí de forma repetida',
}

export default function Coordinacion() {
  const { data, error, reintentar } = useGrupos()
  const { data: narrs, error: errorNarrs, reintentar: reintentarNarrs } = useNarrativas()
  if (error || errorNarrs) {
    return <ErrorCarga onRetry={() => {
      if (error) reintentar()
      if (errorNarrs) reintentarNarrs()
    }} />
  }
  if (!data || !narrs) return <Cargando />
  const titulos = new Map(narrs.map((n) => [n.narrativa, n.titulo]))
  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <Encabezado titulo="Coordinación" sub="Grupos de cuentas que actúan juntas de forma repetida, más allá de lo esperable por azar o viralidad." icono={<Network className="h-7 w-7" />} />
      {data.length === 0 && <Tarjeta className="p-10 text-lg">No se detectaron operaciones coordinadas.</Tarjeta>}
      {data.map((g) => (
        <Tarjeta key={g.grupo} className="space-y-5 p-6">
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-2xl bg-rose-600 px-4 py-2 text-xl font-bold text-white">Operación {g.grupo}</span>
            <span className="text-lg text-slate-600">{CANAL[g.canal] ?? g.canal}</span>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Cifra i={<Users className="h-5 w-5" />} t="Cuentas" v={num(g.n_cuentas)} />
            <Cifra i={<Network className="h-5 w-5" />} t="Comentarios" v={`${num(g.comentarios)} en ${num(g.n_publicaciones)} publicaciones`} />
            <Cifra i={<CalendarClock className="h-5 w-5" />} t="Antigüedad de las cuentas" v={g.mediana_dias_cuenta_al_primer_comentario == null ? '—' : `${num(Math.round(g.mediana_dias_cuenta_al_primer_comentario))} días (mediana)`} />
            <Cifra i={<Moon className="h-5 w-5" />} t="Actividad nocturna" v={g.frac_nocturna == null ? '—' : `${Math.round(100 * g.frac_nocturna)}%`} />
          </div>
          <div className="grid gap-5 lg:grid-cols-2">
            <div>
              <h3 className="mb-2 text-lg font-semibold">Mensajes típicos</h3>
              <div className="space-y-2">
                {g.ejemplos.slice(0, 4).map((e) => (
                  <p key={e} className="flex gap-2 rounded-2xl bg-slate-50 p-3 text-[16px]"><Quote className="mt-1 h-4 w-4 shrink-0 text-slate-400" />{e}</p>
                ))}
              </div>
              {g.narrativas.length > 0 && <p className="mt-3 text-slate-600">Impulsa sobre todo: <b>«{titulos.get(g.narrativas[0].narrativa) ?? g.narrativas[0].narrativa}»</b></p>}
            </div>
            <div>
              <h3 className="mb-2 text-lg font-semibold">Publicaciones donde más actúa</h3>
              <div className="space-y-2">
                {g.publicaciones_top.map((p) => (
                  <Link key={p.publicacion_id} to={`/publicacion/${p.publicacion_id}`} className="flex items-center justify-between gap-3 rounded-2xl p-3 ring-1 ring-slate-200 hover:bg-slate-50">
                    <span className="line-clamp-1">{p.titular}</span>
                    <span className="shrink-0 font-semibold text-rose-600">{num(p.n)}</span>
                  </Link>
                ))}
              </div>
            </div>
          </div>
          <div>
            <h3 className="mb-2 text-lg font-semibold">Cuentas del grupo</h3>
            <div className="flex flex-wrap gap-2">
              {g.cuentas.slice(0, 24).map((c) => (
                <span key={c.cuenta_id} className="flex items-center gap-2 rounded-full bg-white py-1 pl-1 pr-3 ring-1 ring-slate-200" title={`Creada ${c.fecha_creacion} · ${c.seguidores} seguidores`}>
                  <Avatar nombre={c.usuario} size="h-7 w-7 text-xs" /> @{c.usuario}
                </span>
              ))}
              {g.cuentas.length > 24 && <span className="px-3 py-1 text-slate-500">+{g.cuentas.length - 24} más</span>}
            </div>
          </div>
        </Tarjeta>
      ))}
    </div>
  )
}

function Cifra({ i, t, v }: { i: React.ReactNode; t: string; v: string }) {
  return (
    <div className="rounded-2xl bg-slate-50 p-4">
      <div className="flex items-center gap-2 text-sm font-medium text-slate-500">{i}{t}</div>
      <div className="mt-1 text-lg font-bold">{v}</div>
    </div>
  )
}

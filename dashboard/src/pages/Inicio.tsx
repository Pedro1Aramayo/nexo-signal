import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Search, MessageCircle, Heart, ShieldAlert, Sparkles, LayoutGrid, BarChart3, Calendar, Layers, Users, Bell, ChevronRight, PieChart, X as Cerrar } from 'lucide-react'
import { fecha, num, pct, useNarrativas, usePublicaciones, useResumen } from '../data'
import type { Narrativa, Plataforma, Publicacion } from '../types'
import { AvisoDemo, Avatar, CATEGORIAS, Cargando, Encabezado, LogoPlataforma, MarcaPlataforma, ORDEN_CATEGORIAS, ORDEN_PLATAFORMAS, PLATAFORMAS, Tarjeta } from '../ui'

type Orden = 'recientes' | 'comentadas' | 'coordinacion'
const POR_PAGINA = 20

export default function Inicio() {
  const { datos: pubs } = usePublicaciones()
  const { datos: resumen } = useResumen()
  const { datos: narrs } = useNarrativas()
  const [plataforma, setPlataforma] = useState<Plataforma | null>(null)
  const [texto, setTexto] = useState('')
  const [orden, setOrden] = useState<Orden>('recientes')
  const [soloCoord, setSoloCoord] = useState(false)
  const [narrativa, setNarrativa] = useState<string | null>(null)
  const [limite, setLimite] = useState(POR_PAGINA)
  const reiniciar = () => setLimite(POR_PAGINA)

  const conteo = useMemo(() => {
    const c: Partial<Record<Plataforma, number>> = {}
    for (const p of pubs ?? []) c[p.plataforma_demo] = (c[p.plataforma_demo] ?? 0) + 1
    return c
  }, [pubs])

  const lista = useMemo(() => {
    const q = texto.trim().toLowerCase()
    const r = (pubs ?? []).filter(
      (p) =>
        (!plataforma || p.plataforma_demo === plataforma) &&
        (!soloCoord || p.coordinados > 0) &&
        (!narrativa || p.narrativas.some((n) => n.narrativa === narrativa)) &&
        (!q || p.titular.toLowerCase().includes(q) || p.fuente_nombre.toLowerCase().includes(q) || p.narrativas.some((n) => n.titulo.toLowerCase().includes(q))),
    )
    if (orden === 'comentadas') r.sort((a, b) => b.comentarios - a.comentarios)
    if (orden === 'coordinacion') r.sort((a, b) => b.coordinados / Math.max(b.comentarios, 1) - a.coordinados / Math.max(a.comentarios, 1))
    return r
  }, [pubs, plataforma, texto, orden, soloCoord, narrativa])

  const titulos = useMemo(() => new Map((narrs ?? []).map((n) => [n.narrativa, n.titulo])), [narrs])

  return (
    <div className="mx-auto max-w-[1500px] space-y-6">
      <Encabezado titulo="Análisis de redes sociales" sub="Seguimos y analizamos lo que se dice sobre un tema en distintas redes." icono={<BarChart3 className="h-7 w-7" />}>
        <label className="relative w-full max-w-md">
          <Search className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
          <input value={texto} onChange={(e) => { setTexto(e.target.value); reiniciar() }} placeholder="Buscar tema, palabra o fuente…" className="w-full rounded-2xl border border-slate-200 bg-white py-3.5 pl-12 pr-4 text-lg shadow-sm outline-none focus:border-indigo-400 focus:ring-4 focus:ring-indigo-100" />
        </label>
        {resumen && (
          <span className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3.5 text-lg shadow-sm">
            <Calendar className="h-5 w-5 text-slate-500" /> {fecha(resumen.fecha_min, false)} – {fecha(resumen.fecha_max, false)} 2026
          </span>
        )}
        <span className="rounded-2xl bg-violet-100 px-4 py-3.5 text-base font-semibold text-violet-800">Modo demostración</span>
      </Encabezado>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_400px]">
        <div className="min-w-0 space-y-5">
          <section className="grid grid-cols-3 gap-3 sm:grid-cols-6">
            <BotonRed activo={plataforma === null} onClick={() => { setPlataforma(null); reiniciar() }} titulo="Todas" n={pubs?.length}>
              <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-600 text-white"><LayoutGrid className="h-6 w-6" /></span>
            </BotonRed>
            {ORDEN_PLATAFORMAS.map((p) => (
              <BotonRed key={p} activo={plataforma === p} onClick={() => { setPlataforma(p); reiniciar() }} titulo={PLATAFORMAS[p].nombre} n={conteo[p]}>
                <MarcaPlataforma p={p} />
              </BotonRed>
            ))}
          </section>

          <Tarjeta className="p-4 sm:p-6">
            <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
              <div>
                <h2 className="text-2xl font-bold">Publicaciones {plataforma ? `de ${PLATAFORMAS[plataforma].nombre}` : 'relacionadas'}</h2>
                <p className="text-slate-500">{pubs ? `Mostrando ${num(lista.length)} publicaciones.` : 'Cargando…'}</p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <button onClick={() => { setSoloCoord(!soloCoord); reiniciar() }} className={`rounded-xl px-4 py-2.5 font-medium ring-1 ${soloCoord ? 'bg-rose-600 text-white ring-rose-600' : 'bg-white text-slate-700 ring-slate-200 hover:bg-slate-50'}`}>Con coordinación</button>
                <span className="text-slate-500">Ordenar por:</span>
                <select value={orden} onChange={(e) => setOrden(e.target.value as Orden)} className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-base font-medium">
                  <option value="recientes">Más recientes</option>
                  <option value="comentadas">Más comentadas</option>
                  <option value="coordinacion">Más coordinación</option>
                </select>
              </div>
            </div>
            {narrativa && (
              <button onClick={() => { setNarrativa(null); reiniciar() }} className="mt-3 inline-flex items-center gap-2 rounded-full bg-indigo-50 px-4 py-2 font-medium text-indigo-800 ring-1 ring-indigo-200">
                Narrativa: «{titulos.get(narrativa)}» <Cerrar className="h-4 w-4" />
              </button>
            )}
            <div className="mt-5 space-y-4">
              {!pubs && <Cargando texto="Cargando publicaciones…" />}
              {pubs && lista.length === 0 && <p className="p-8 text-center text-lg text-slate-500">No hay publicaciones que coincidan.</p>}
              {lista.slice(0, limite).map((p) => <FilaPublicacion key={p.publicacion_id} p={p} />)}
              {limite < lista.length && (
                <div className="flex justify-center">
                  <button onClick={() => setLimite(limite + POR_PAGINA)} className="rounded-2xl bg-indigo-50 px-6 py-3.5 text-lg font-semibold text-indigo-700 hover:bg-indigo-100">Ver más publicaciones</button>
                </div>
              )}
            </div>
          </Tarjeta>
        </div>

        <aside className="space-y-5">
          {resumen && <ResumenAnalisis r={resumen} />}
          {narrs && resumen && <Postura narrs={narrs} />}
          {narrs && <Principales narrs={narrs} activa={narrativa} onElegir={(n) => { setNarrativa(n === narrativa ? null : n); reiniciar() }} />}
          <AvisoDemo />
        </aside>
      </div>
    </div>
  )
}

function BotonRed({ activo, onClick, titulo, n, children }: { activo: boolean; onClick: () => void; titulo: string; n?: number; children: React.ReactNode }) {
  return (
    <button onClick={onClick} aria-pressed={activo} className={`flex flex-col items-center gap-2 rounded-2xl px-2 py-4 shadow-sm ring-2 transition hover:-translate-y-0.5 hover:shadow-md ${activo ? 'bg-indigo-50 ring-indigo-500' : 'bg-white ring-transparent'}`}>
      {children}
      <span className="text-lg font-semibold leading-none">{titulo}</span>
      <span className="text-sm text-slate-500">{n == null ? '…' : `${num(n)} demo`}</span>
    </button>
  )
}

function postura(p: Publicacion) {
  const top = p.narrativas[0]
  if (!top || top.apoya + top.rechaza === 0) return null
  const a = top.apoya
  const r = top.rechaza
  const f = a / (a + r)
  if (f >= 0.6) return { texto: 'A favor', clase: 'bg-emerald-100 text-emerald-800', punto: 'bg-emerald-500' }
  if (f <= 0.4) return { texto: 'En contra', clase: 'bg-rose-100 text-rose-800', punto: 'bg-rose-500' }
  return { texto: 'Mixta', clase: 'bg-amber-100 text-amber-800', punto: 'bg-amber-500' }
}

function FilaPublicacion({ p }: { p: Publicacion }) {
  const plat = PLATAFORMAS[p.plataforma_demo]
  const top = p.narrativas[0]
  const pos = postura(p)
  return (
    <div className="grid gap-4 rounded-2xl border border-slate-200 p-4 transition hover:border-indigo-200 hover:shadow-md md:grid-cols-[auto_minmax(0,1fr)_170px_240px] md:items-center">
      <MarcaPlataforma p={p.plataforma_demo} size="h-12 w-12 hidden md:flex" />
      <div className="min-w-0 space-y-2">
        <div className="flex items-center gap-3">
          <Avatar nombre={p.fuente_nombre} />
          <div className="min-w-0">
            <div className="truncate text-lg font-semibold">{p.fuente_nombre}</div>
            <div className="text-sm text-slate-500">{plat.nombre} · {fecha(p.fecha)}</div>
          </div>
        </div>
        <p className="text-lg leading-snug">{p.titular}</p>
        <div className="flex flex-wrap items-center gap-x-5 gap-y-1 text-slate-600">
          <span className="flex items-center gap-1.5"><Heart className="h-5 w-5" /> {num(p.me_gusta_total)}</span>
          <span className="flex items-center gap-1.5"><MessageCircle className="h-5 w-5" /> {num(p.comentarios)}</span>
          {p.coordinados > 0 && <span className="flex items-center gap-1.5 font-medium text-rose-600"><ShieldAlert className="h-5 w-5" /> {num(p.coordinados)} coordinados</span>}
        </div>
      </div>
      <div className={`relative hidden h-32 overflow-hidden rounded-2xl md:block ${plat.fondo}`}>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(255,255,255,.4),transparent_60%)]" />
        <LogoPlataforma p={p.plataforma_demo} className="absolute right-3 top-3 h-6 w-6 text-white/80" />
        <div className="absolute inset-x-3 bottom-3">
          <div className="flex h-2 overflow-hidden rounded-full bg-white/30">
            {ORDEN_CATEGORIAS.map((c) => <div key={c} className={CATEGORIAS[c].punto} style={{ width: `${(100 * (p.categorias[c] ?? 0)) / Math.max(p.comentarios, 1)}%` }} />)}
          </div>
          <div className="mt-1.5 text-xs font-medium text-white">{pct(p.categorias.queja ?? 0, p.comentarios)} quejas · {pct(p.categorias.consulta ?? 0, p.comentarios)} consultas</div>
        </div>
      </div>
      <div className="space-y-2">
        <div className="rounded-xl bg-indigo-50 px-3 py-2">
          <div className="text-sm font-semibold text-indigo-900">Narrativa</div>
          <div className="line-clamp-2 text-[15px] text-slate-700">{top ? top.titulo : 'Conversación general'}</div>
        </div>
        <div className="rounded-xl bg-slate-50 px-3 py-2">
          <div className="text-sm font-semibold text-slate-800">Postura</div>
          {pos ? <span className={`mt-1 inline-flex items-center gap-1.5 rounded-lg px-2.5 py-0.5 text-[15px] font-semibold ${pos.clase}`}><span className={`h-2 w-2 rounded-full ${pos.punto}`} />{pos.texto}</span> : <span className="text-[15px] text-slate-500">Sin postura</span>}
        </div>
        <Link to={`/publicacion/${p.publicacion_id}`} className="flex items-center justify-center gap-2 rounded-xl bg-[#1b2f86] px-4 py-3 text-base font-semibold text-white shadow-md transition hover:bg-[#13246b]">
          <Sparkles className="h-5 w-5" /> Analizar publicación
        </Link>
      </div>
    </div>
  )
}

function ResumenAnalisis({ r }: { r: { comentarios: number; narrativas: number; cuentas_coordinadas: number; grupos_coordinados: number } }) {
  const items = [
    { i: <MessageCircle className="h-7 w-7 text-indigo-600" />, v: r.comentarios, t: 'Comentarios analizados', c: 'bg-indigo-50', a: '/' },
    { i: <Layers className="h-7 w-7 text-emerald-600" />, v: r.narrativas, t: 'Narrativas detectadas', c: 'bg-emerald-50', a: '/narrativas' },
    { i: <Users className="h-7 w-7 text-violet-600" />, v: r.cuentas_coordinadas, t: 'Cuentas coordinadas', c: 'bg-violet-50', a: '/coordinacion' },
    { i: <Bell className="h-7 w-7 text-rose-600" />, v: r.grupos_coordinados, t: 'Operaciones', c: 'bg-rose-50', a: '/coordinacion' },
  ]
  return (
    <Tarjeta className="p-5">
      <h2 className="flex items-center gap-3 text-xl font-bold"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-100 text-indigo-600"><BarChart3 className="h-5 w-5" /></span>Resumen del análisis</h2>
      <div className="mt-4 grid grid-cols-2 gap-3">
        {items.map((x) => (
          <Link key={x.t} to={x.a} className={`rounded-2xl p-4 text-center transition hover:shadow-md ${x.c}`}>
            <div className="flex justify-center">{x.i}</div>
            <div className="mt-2 text-2xl font-bold">{num(x.v)}</div>
            <div className="text-sm leading-tight text-slate-600">{x.t}</div>
          </Link>
        ))}
      </div>
    </Tarjeta>
  )
}

function Postura({ narrs }: { narrs: Narrativa[] }) {
  const a = narrs.reduce((s, n) => s + n.apoya, 0)
  const r = narrs.reduce((s, n) => s + n.rechaza, 0)
  const t = Math.max(a + r, 1)
  const fa = a / t
  return (
    <Tarjeta className="p-5">
      <h2 className="flex items-center gap-3 text-xl font-bold"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-100 text-indigo-600"><PieChart className="h-5 w-5" /></span>Postura de la conversación</h2>
      <div className="mt-4 flex items-center gap-6">
        <div className="relative h-36 w-36 shrink-0 rounded-full" style={{ background: `conic-gradient(#22c55e 0 ${fa * 360}deg, #f43f5e ${fa * 360}deg 360deg)` }}>
          <div className="absolute inset-4 flex flex-col items-center justify-center rounded-full bg-white">
            <span className="text-xl font-bold">{num(a + r)}</span>
            <span className="text-xs text-slate-500">con postura</span>
          </div>
        </div>
        <ul className="flex-1 space-y-3 text-lg">
          <li className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-emerald-500" /> A favor <b className="ml-auto">{pct(a, t)}</b></li>
          <li className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-rose-500" /> En contra <b className="ml-auto">{pct(r, t)}</b></li>
        </ul>
      </div>
      <p className="mt-3 text-sm text-slate-500">Postura respecto de cada narrativa, sin contar ruido.</p>
    </Tarjeta>
  )
}

function Principales({ narrs, activa, onElegir }: { narrs: Narrativa[]; activa: string | null; onElegir: (n: string) => void }) {
  const top = [...narrs].sort((a, b) => b.total - a.total).slice(0, 5)
  return (
    <Tarjeta className="p-5">
      <h2 className="flex items-center gap-3 text-xl font-bold"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-100 text-indigo-600"><Layers className="h-5 w-5" /></span>Principales narrativas</h2>
      <div className="mt-4 space-y-2">
        {top.map((n, i) => (
          <button key={n.narrativa} onClick={() => onElegir(n.narrativa)} className={`flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left ring-1 transition ${activa === n.narrativa ? 'bg-indigo-50 ring-indigo-400' : 'ring-slate-200 hover:bg-slate-50'}`}>
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-600 font-bold text-white">{i + 1}</span>
            <span className="min-w-0 flex-1">
              <span className="line-clamp-2 font-semibold leading-snug">{n.titulo}</span>
              <span className="text-sm text-slate-500">{num(n.total)} comentarios</span>
            </span>
            <ChevronRight className="h-5 w-5 shrink-0 text-slate-400" />
          </button>
        ))}
      </div>
      <Link to="/narrativas" className="mt-3 block text-center font-semibold text-indigo-700 hover:underline">Ver todas las narrativas</Link>
    </Tarjeta>
  )
}

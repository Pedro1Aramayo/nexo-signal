import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Heart, MessageCircle, CornerDownRight, ShieldAlert, Leaf, ThumbsUp, ThumbsDown, Network } from 'lucide-react'
import { fecha, num, pct, useComentarios, useNarrativas, usePublicaciones, useResumen } from '../data'
import type { Categoria, Comentario } from '../types'
import { AvisoDemo, Avatar, CATEGORIAS, Cargando, ErrorCarga, LogoPlataforma, ORDEN_CATEGORIAS, PLATAFORMAS, Tarjeta } from '../ui'

const POR_PAGINA = 30

export default function Detalle() {
  const { id } = useParams()
  const { data: pubs, error: errorPubs, reintentar: reintentarPubs } = usePublicaciones()
  const { data: narrs, error: errorNarrs, reintentar: reintentarNarrs } = useNarrativas()
  const { data: comentarios, error: errorComentarios, reintentar: reintentarComentarios } = useComentarios(id)
  const { data: resumenDataset, error: errorResumen, reintentar: reintentarResumen } = useResumen()
  const [categoria, setCategoria] = useState<Categoria | null>(null)
  const [narrativa, setNarrativa] = useState<string | null>(null)
  const [soloCoord, setSoloCoord] = useState(false)
  const [limite, setLimite] = useState(POR_PAGINA)

  const pub = pubs?.find((p) => p.publicacion_id === id)
  const titulos = useMemo(() => new Map((narrs ?? []).map((n) => [n.narrativa, n.titulo])), [narrs])
  const porId = useMemo(() => new Map((comentarios ?? []).map((c) => [c.id, c])), [comentarios])

  const resumen = useMemo(() => {
    const cat: Partial<Record<Categoria, number>> = {}
    const nar = new Map<string, { n: number; apoya: number; rechaza: number; coord: number }>()
    let coord = 0
    for (const c of comentarios ?? []) {
      cat[c.categoria] = (cat[c.categoria] ?? 0) + 1
      if (c.grupo) coord++
      if (c.narrativa) {
        const e = nar.get(c.narrativa) ?? { n: 0, apoya: 0, rechaza: 0, coord: 0 }
        e.n++
        if (c.postura === 'apoya') e.apoya++
        if (c.postura === 'rechaza') e.rechaza++
        if (c.grupo) e.coord++
        nar.set(c.narrativa, e)
      }
    }
    const grupos = [...new Set((comentarios ?? []).map((c) => c.grupo).filter(Boolean))] as string[]
    return { cat, coord, grupos: grupos.sort(), narrativas: [...nar.entries()].sort((a, b) => b[1].n - a[1].n) }
  }, [comentarios])

  const filtrados = useMemo(
    () =>
      (comentarios ?? []).filter(
        (c) => (!categoria || c.categoria === categoria) && (!narrativa || c.narrativa === narrativa) && (!soloCoord || c.grupo),
      ),
    [comentarios, categoria, narrativa, soloCoord],
  )

  if (errorPubs) {
    return <ErrorCarga onRetry={reintentarPubs} />
  }
  if (!pubs) return <Cargando texto="Analizando publicación…" />
  if (!pub) return <Tarjeta className="p-10 text-lg">No encontramos esta publicación. <Link className="font-semibold text-violet-700" to="/">Volver al inicio</Link></Tarjeta>
  if (errorNarrs || errorComentarios || errorResumen) {
    return (
      <ErrorCarga onRetry={() => {
        if (errorNarrs) reintentarNarrs()
        if (errorComentarios) reintentarComentarios()
        if (errorResumen) reintentarResumen()
      }} />
    )
  }
  if (!comentarios || !narrs || !resumenDataset) return <Cargando texto="Analizando publicación…" />

  const plat = PLATAFORMAS[pub.plataforma_demo]
  const total = comentarios.length
  const reiniciar = () => setLimite(POR_PAGINA)

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <Link to="/" className="inline-flex items-center gap-2 rounded-2xl px-3 py-2 text-lg font-medium text-slate-600 hover:bg-white">
        <ArrowLeft className="h-5 w-5" /> Volver a publicaciones
      </Link>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_380px]">
        <div className="min-w-0 space-y-6">
          <Tarjeta className="overflow-hidden">
            <div className={`flex items-center gap-3 px-6 py-4 text-white ${plat.fondo}`}>
              <LogoPlataforma p={pub.plataforma_demo} className="h-6 w-6" />
              <span className="text-lg font-semibold">{plat.nombre}</span>
              <span className="rounded-full bg-white/25 px-2.5 py-0.5 text-sm">demostración</span>
            </div>
            <div className="space-y-4 p-6">
              <div className="flex items-center gap-3">
                <Avatar nombre={pub.fuente_nombre} size="h-12 w-12 text-lg" />
                <div>
                  <div className="text-lg font-semibold">{pub.fuente_nombre}</div>
                  <div className="text-slate-500">{fecha(pub.fecha)} · {pub.fuente_tipo}</div>
                </div>
              </div>
              <h1 className="text-2xl font-bold leading-snug sm:text-3xl">{pub.titular}</h1>
              <div className="flex flex-wrap gap-5 text-lg text-slate-600">
                <span className="flex items-center gap-2"><MessageCircle className="h-5 w-5" /> {num(total)} comentarios</span>
                <span className="flex items-center gap-2"><Heart className="h-5 w-5" /> {num(pub.me_gusta_total)} me gusta</span>
                {resumen.coord > 0 && <span className="flex items-center gap-2 text-rose-600"><ShieldAlert className="h-5 w-5" /> {num(resumen.coord)} comentarios de cuentas coordinadas</span>}
              </div>
            </div>
          </Tarjeta>

          <section className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
            <BotonCategoria activo={!categoria} onClick={() => { setCategoria(null); reiniciar() }} titulo="Todos" n={total} total={total} punto="bg-violet-500" />
            {ORDEN_CATEGORIAS.map((c) => (
              <BotonCategoria key={c} activo={categoria === c} onClick={() => { setCategoria(categoria === c ? null : c); reiniciar() }} titulo={CATEGORIAS[c].nombre} n={resumen.cat[c] ?? 0} total={total} punto={CATEGORIAS[c].punto} />
            ))}
          </section>
          <p className="text-sm text-slate-500">Clasificación experimental · reglas heurísticas, precisión no medida</p>

          <div className="flex flex-wrap items-center gap-2">
            {narrativa && (
              <button onClick={() => { setNarrativa(null); reiniciar() }} className="rounded-full bg-violet-100 px-4 py-2 font-medium text-violet-800 hover:bg-violet-200">
                Narrativa: «{titulos.get(narrativa)}» ✕
              </button>
            )}
            {resumen.coord > 0 && (
              <button onClick={() => { setSoloCoord(!soloCoord); reiniciar() }} className={`rounded-full px-4 py-2 font-medium ring-1 ${soloCoord ? 'bg-rose-600 text-white ring-rose-600' : 'bg-white text-slate-700 ring-slate-200'}`}>
                Solo comentarios de cuentas coordinadas
              </button>
            )}
            <span className="ml-auto text-slate-500">{num(filtrados.length)} comentarios</span>
          </div>

          <div className="space-y-3">
            {filtrados.slice(0, limite).map((c) => (
              <TarjetaComentario key={c.id} c={c} padre={c.respuesta_a ? porId.get(c.respuesta_a) : undefined} titulo={c.narrativa ? titulos.get(c.narrativa) : undefined} />
            ))}
            {filtrados.length === 0 && <Tarjeta className="p-8 text-center text-lg text-slate-500">No hay comentarios con estos filtros.</Tarjeta>}
            {limite < filtrados.length && (
              <div className="flex justify-center pt-2">
                <button onClick={() => setLimite(limite + POR_PAGINA)} className="rounded-2xl bg-white px-6 py-4 text-lg font-semibold text-violet-700 shadow-sm ring-1 ring-slate-200 hover:bg-violet-50">
                  Ver más comentarios
                </button>
              </div>
            )}
          </div>
        </div>

        <aside className="space-y-6 lg:sticky lg:top-6 lg:self-start">
          <Tarjeta className="p-6">
            <h2 className="text-xl font-bold">Narrativas detectadas</h2>
            <p className="mt-1 text-slate-500">Tocá una para filtrar sus comentarios.</p>
            <div className="mt-4 space-y-3">
              {resumen.narrativas.length === 0 && <p className="text-slate-500">Esta publicación no tiene narrativas: sus comentarios son conversación general.</p>}
              {resumen.narrativas.slice(0, 6).map(([n, e]) => {
                const conPostura = Math.max(e.apoya + e.rechaza, 1)
                return (
                  <button key={n} onClick={() => { setNarrativa(narrativa === n ? null : n); reiniciar() }} className={`w-full rounded-2xl p-4 text-left ring-1 transition ${narrativa === n ? 'bg-violet-50 ring-violet-400' : 'ring-slate-200 hover:bg-slate-50'}`}>
                    <div className="font-semibold leading-snug">«{titulos.get(n)}»</div>
                    <div className="mt-1 text-sm text-slate-500">{num(e.n)} comentarios · {pct(e.n, total)}</div>
                    <div className="mt-3 flex h-3 overflow-hidden rounded-full bg-slate-100">
                      <div className="bg-emerald-500" style={{ width: `${(100 * e.apoya) / conPostura}%` }} />
                      <div className="bg-rose-500" style={{ width: `${(100 * e.rechaza) / conPostura}%` }} />
                    </div>
                    <div className="mt-2 flex justify-between text-sm">
                      <span className="flex items-center gap-1 text-emerald-700"><ThumbsUp className="h-4 w-4" /> Apoya {pct(e.apoya, conPostura)}</span>
                      <span className="flex items-center gap-1 text-rose-700">Rechaza {pct(e.rechaza, conPostura)} <ThumbsDown className="h-4 w-4" /></span>
                    </div>
                  </button>
                )
              })}
            </div>
          </Tarjeta>

          <Tarjeta className="p-6">
            <h2 className="flex items-center gap-2 text-xl font-bold"><Leaf className="h-6 w-6 text-emerald-600" /> Organic Lens</h2>
            <p className="mt-1 text-slate-500">Conversación total versus conversación sin cuentas coordinadas.</p>
            <div className="mt-4 space-y-3">
              <Barra texto="Total" n={total} max={total} color="bg-slate-400" />
              <Barra texto="Actividad sin coordinación detectada" n={total - resumen.coord} max={total} color="bg-emerald-500" />
            </div>
            <p className="mt-4 text-[15px] text-slate-600">
              {resumen.coord > 0 ? <>El <b>{pct(resumen.coord, total)}</b> de los comentarios proviene de operaciones coordinadas ({resumen.grupos.join(', ')}).</> : <>No se detectaron cuentas coordinadas en esta publicación.</>}
            </p>
            <div className="mt-5 grid gap-2">
              <Link to="/coordinacion" className="flex items-center justify-center gap-2 rounded-2xl bg-slate-900 px-4 py-3 text-lg font-semibold text-white hover:bg-slate-800"><Network className="h-5 w-5" /> Ver coordinación</Link>
              <Link to="/organic-lens" className="flex items-center justify-center gap-2 rounded-2xl bg-emerald-50 px-4 py-3 text-lg font-semibold text-emerald-800 ring-1 ring-emerald-200 hover:bg-emerald-100"><Leaf className="h-5 w-5" /> Abrir Organic Lens</Link>
            </div>
          </Tarjeta>
          <AvisoDemo dataset={resumenDataset.dataset} />
        </aside>
      </div>
    </div>
  )
}

function BotonCategoria({ activo, onClick, titulo, n, total, punto }: { activo: boolean; onClick: () => void; titulo: string; n: number; total: number; punto: string }) {
  return (
    <button onClick={onClick} aria-pressed={activo} className={`rounded-2xl p-4 text-left shadow-sm ring-2 transition ${activo ? 'bg-slate-900 text-white ring-slate-900' : 'bg-white ring-transparent hover:ring-slate-200'}`}>
      <span className="flex items-center gap-2 text-base font-medium"><span className={`h-2.5 w-2.5 rounded-full ${punto}`} /> {titulo}</span>
      <span className="mt-1 block text-2xl font-bold">{num(n)}</span>
      <span className={`text-sm ${activo ? 'text-slate-300' : 'text-slate-500'}`}>{pct(n, total)}</span>
    </button>
  )
}

function Barra({ texto, n, max, color }: { texto: string; n: number; max: number; color: string }) {
  return (
    <div>
      <div className="flex justify-between text-[15px]"><span className="font-medium">{texto}</span><span className="text-slate-500">{num(n)}</span></div>
      <div className="mt-1 h-3 overflow-hidden rounded-full bg-slate-100"><div className={`h-full ${color}`} style={{ width: `${(100 * n) / Math.max(max, 1)}%` }} /></div>
    </div>
  )
}

function TarjetaComentario({ c, padre, titulo }: { c: Comentario; padre?: Comentario; titulo?: string }) {
  const cat = CATEGORIAS[c.categoria]
  return (
    <Tarjeta className={`p-5 ${c.grupo ? 'ring-2 ring-rose-200' : ''}`}>
      {padre && (
        <div className="mb-3 flex items-start gap-2 rounded-2xl bg-slate-50 px-3 py-2 text-[15px] text-slate-500">
          <CornerDownRight className="mt-0.5 h-4 w-4 shrink-0" />
          <span className="line-clamp-1">Responde a <b>@{padre.usuario}</b>: {padre.texto}</span>
        </div>
      )}
      <div className="flex gap-3">
        <Avatar nombre={c.usuario || c.cuenta_id} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-2">
            <span className="font-semibold">@{c.usuario || c.cuenta_id}</span>
            <span className="text-sm text-slate-500">{fecha(c.fecha)}</span>
          </div>
          <p className="mt-1 whitespace-pre-line break-words text-[17px] leading-relaxed">{c.texto}</p>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
            <span className={`rounded-full px-3 py-1 font-medium ring-1 ${cat.chip}`}>{cat.singular}</span>
            {c.postura && (
              <span className={`rounded-full px-3 py-1 font-medium ring-1 ${c.postura === 'apoya' ? 'bg-emerald-50 text-emerald-700 ring-emerald-200' : 'bg-rose-50 text-rose-700 ring-rose-200'}`}>
                {c.postura === 'apoya' ? 'Apoya' : 'Rechaza'}
              </span>
            )}
            {titulo && <span className="line-clamp-1 max-w-xs rounded-full bg-violet-50 px-3 py-1 text-violet-700 ring-1 ring-violet-200">«{titulo}»</span>}
            {c.grupo && <span className="flex items-center gap-1 rounded-full bg-rose-600 px-3 py-1 font-semibold text-white"><ShieldAlert className="h-4 w-4" /> Operación {c.grupo}</span>}
            <span className="ml-auto flex items-center gap-1 text-slate-500"><Heart className="h-4 w-4" /> {num(c.me_gusta)}</span>
          </div>
        </div>
      </div>
    </Tarjeta>
  )
}

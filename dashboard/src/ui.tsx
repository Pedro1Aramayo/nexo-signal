import type { ReactNode } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { Home, Network, Leaf, PlugZap, Info, Layers } from 'lucide-react'
import type { Categoria, Plataforma } from './types'

export const PLATAFORMAS: Record<Plataforma, { nombre: string; fondo: string; texto: string }> = {
  instagram: { nombre: 'Instagram', fondo: 'bg-gradient-to-br from-amber-400 via-pink-500 to-purple-600', texto: 'text-pink-600' },
  tiktok: { nombre: 'TikTok', fondo: 'bg-gradient-to-br from-slate-900 to-slate-700', texto: 'text-slate-900' },
  facebook: { nombre: 'Facebook', fondo: 'bg-gradient-to-br from-blue-500 to-blue-700', texto: 'text-blue-600' },
  youtube: { nombre: 'YouTube', fondo: 'bg-gradient-to-br from-red-500 to-red-700', texto: 'text-red-600' },
  x: { nombre: 'X', fondo: 'bg-gradient-to-br from-neutral-800 to-black', texto: 'text-neutral-900' },
}
export const ORDEN_PLATAFORMAS: Plataforma[] = ['instagram', 'tiktok', 'facebook', 'youtube', 'x']

export function LogoPlataforma({ p, className = 'h-6 w-6' }: { p: Plataforma; className?: string }) {
  const props = { className, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 2, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const }
  switch (p) {
    case 'instagram':
      return (
        <svg {...props}>
          <rect x="3" y="3" width="18" height="18" rx="5" />
          <circle cx="12" cy="12" r="4" />
          <circle cx="17.5" cy="6.5" r="0.6" fill="currentColor" />
        </svg>
      )
    case 'facebook':
      return (
        <svg {...props}>
          <path d="M15 3h-2.5A3.5 3.5 0 0 0 9 6.5V10H6.5v3.5H9V21h3.5v-7.5H15l.5-3.5h-3V7a1 1 0 0 1 1-1H15z" />
        </svg>
      )
    case 'youtube':
      return (
        <svg {...props}>
          <rect x="2.5" y="5.5" width="19" height="13" rx="4" />
          <path d="M10 9.2v5.6l4.8-2.8z" fill="currentColor" />
        </svg>
      )
    case 'tiktok':
      return (
        <svg {...props}>
          <path d="M14 3v11.5a3.5 3.5 0 1 1-3.5-3.5" />
          <path d="M14 3c.5 2.6 2.3 4.3 5 4.5" />
        </svg>
      )
    case 'x':
      return (
        <svg {...props}>
          <path d="M4 4l16 16M20 4L4 20" />
        </svg>
      )
  }
}

export const CATEGORIAS: Record<Categoria, { nombre: string; singular: string; chip: string; punto: string }> = {
  consulta: { nombre: 'Consultas', singular: 'Consulta', chip: 'bg-sky-50 text-sky-700 ring-sky-200', punto: 'bg-sky-500' },
  queja: { nombre: 'Quejas', singular: 'Queja', chip: 'bg-rose-50 text-rose-700 ring-rose-200', punto: 'bg-rose-500' },
  elogio: { nombre: 'Elogios', singular: 'Elogio', chip: 'bg-emerald-50 text-emerald-700 ring-emerald-200', punto: 'bg-emerald-500' },
  sugerencia: { nombre: 'Sugerencias', singular: 'Sugerencia', chip: 'bg-amber-50 text-amber-800 ring-amber-200', punto: 'bg-amber-500' },
  otro: { nombre: 'Otros', singular: 'Otro', chip: 'bg-slate-100 text-slate-700 ring-slate-200', punto: 'bg-slate-400' },
}
export const ORDEN_CATEGORIAS: Categoria[] = ['consulta', 'queja', 'elogio', 'sugerencia', 'otro']

const COLORES_AVATAR = ['bg-violet-500', 'bg-sky-500', 'bg-emerald-500', 'bg-amber-500', 'bg-rose-500', 'bg-indigo-500', 'bg-teal-500', 'bg-fuchsia-500']
export function Avatar({ nombre, size = 'h-10 w-10 text-base' }: { nombre: string; size?: string }) {
  let h = 0
  for (const c of nombre) h = (h * 31 + c.charCodeAt(0)) >>> 0
  return (
    <div className={`${size} ${COLORES_AVATAR[h % COLORES_AVATAR.length]} flex shrink-0 items-center justify-center rounded-full font-semibold uppercase text-white`}>
      {nombre.slice(0, 1)}
    </div>
  )
}

export function Tarjeta({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-3xl border border-slate-200/70 bg-white shadow-sm ${className}`}>{children}</div>
}

export function Cargando({ texto = 'Cargando…' }: { texto?: string }) {
  return (
    <div className="flex items-center gap-3 p-10 text-lg text-slate-500">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-violet-500 border-t-transparent" />
      {texto}
    </div>
  )
}

export function AvisoDemo() {
  return (
    <div className="flex items-start gap-3 rounded-2xl bg-violet-50 px-4 py-3 text-[15px] text-violet-900 ring-1 ring-violet-200">
      <Info className="mt-0.5 h-5 w-5 shrink-0" />
      <p>
        <b>Modo demostración.</b> Ninguna cuenta de redes sociales está conectada. Las publicaciones son datos sintéticos de práctica de QualyData, asignadas a plataformas para ilustrar; el análisis es el resultado real de NEXO ENGINE.
      </p>
    </div>
  )
}

const MENU = [
  { a: '/', icono: Home, texto: 'Inicio' },
  { a: '/narrativas', icono: Layers, texto: 'Narrativas' },
  { a: '/coordinacion', icono: Network, texto: 'Coordinación' },
  { a: '/organic-lens', icono: Leaf, texto: 'Organic Lens' },
  { a: '/conexiones', icono: PlugZap, texto: 'Conexiones' },
]

export function Layout() {
  return (
    <div className="min-h-screen bg-[#f4f6fb] text-slate-900 lg:flex">
      <aside className="sticky top-0 z-20 flex items-center gap-2 bg-gradient-to-b from-[#0d1b4c] via-[#13246b] to-[#1b2f86] px-4 py-3 text-white lg:h-screen lg:w-64 lg:flex-col lg:items-stretch lg:gap-2 lg:px-4 lg:py-7">
        <div className="mr-auto flex shrink-0 items-center gap-3 lg:mb-8 lg:mr-0 lg:px-2">
          <svg viewBox="0 0 40 40" className="h-10 w-10 lg:h-12 lg:w-12">
            <defs>
              <linearGradient id="gn" x1="0" y1="1" x2="1" y2="0">
                <stop offset="0" stopColor="#38bdf8" />
                <stop offset="1" stopColor="#818cf8" />
              </linearGradient>
            </defs>
            <path d="M5 34V8l6-2 18 20V6h6v28l-6 2L11 16v18z" fill="url(#gn)" />
          </svg>
          <div className="hidden text-xl font-extrabold leading-[1.05] tracking-wide sm:block lg:text-2xl">NEXO<br />SIGNAL</div>
        </div>
        <nav className="flex min-w-0 gap-1 overflow-x-auto lg:flex-col lg:gap-2 lg:overflow-visible">
          {MENU.map(({ a, icono: Icono, texto }) => (
            <NavLink
              key={a}
              to={a}
              end={a === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-2xl px-3 py-3 text-lg font-medium transition lg:px-4 ${
                  isActive ? 'bg-gradient-to-r from-indigo-500 to-blue-500 shadow-lg shadow-indigo-900/40' : 'text-indigo-100 hover:bg-white/10'
                }`
              }
            >
              <Icono className="h-6 w-6 shrink-0" />
              <span className="hidden md:inline">{texto}</span>
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto hidden rounded-2xl bg-white/10 p-4 text-sm text-indigo-100 lg:block">
          <b className="text-white">NEXO ENGINE</b><br />Análisis local en CPU · USD 0 en IA
        </div>
      </aside>
      <main className="min-w-0 flex-1 px-4 py-6 sm:px-8 lg:py-8">
        <Outlet />
      </main>
    </div>
  )
}

export function Encabezado({ titulo, sub, icono, children }: { titulo: string; sub: string; icono: ReactNode; children?: ReactNode }) {
  return (
    <header className="flex flex-col gap-4 xl:flex-row xl:items-center">
      <div className="flex items-center gap-4">
        <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-indigo-100 text-indigo-600">{icono}</span>
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">{titulo}</h1>
          <p className="text-base text-slate-500 sm:text-lg">{sub}</p>
        </div>
      </div>
      <div className="flex flex-1 flex-wrap items-center gap-3 xl:justify-end">{children}</div>
    </header>
  )
}

export function MarcaPlataforma({ p, size = 'h-11 w-11' }: { p: Plataforma; size?: string }) {
  const caja: Record<Plataforma, string> = {
    instagram: 'rounded-xl bg-gradient-to-tr from-amber-400 via-pink-500 to-purple-600',
    facebook: 'rounded-full bg-[#1877f2]',
    youtube: 'rounded-xl bg-[#ff0000]',
    tiktok: 'rounded-xl bg-black',
    x: 'rounded-xl bg-black',
  }
  return (
    <span className={`flex shrink-0 items-center justify-center text-white ${size} ${caja[p]}`}>
      <LogoPlataforma p={p} className="h-3/5 w-3/5" />
    </span>
  )
}

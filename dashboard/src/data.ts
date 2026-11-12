import { useEffect, useState } from 'react'
import type { Comentario, Fuente, Grupo, Narrativa, Publicacion, Resumen } from './types'

const cache = new Map<string, Promise<unknown>>()

function cargar<T>(ruta: string): Promise<T> {
  if (!cache.has(ruta)) {
    cache.set(
      ruta,
      fetch(`${import.meta.env.BASE_URL}data/${ruta}`).then((r) => {
        if (!r.ok) throw new Error(`No se pudo cargar ${ruta}`)
        return r.json()
      }),
    )
  }
  return cache.get(ruta) as Promise<T>
}

export function useDatos<T>(ruta: string | null) {
  const [estado, setEstado] = useState<{ ruta: string | null; datos?: T; error?: string }>({ ruta: null })
  useEffect(() => {
    if (!ruta) return
    let vivo = true
    cargar<T>(ruta)
      .then((datos) => vivo && setEstado({ ruta, datos }))
      .catch((e: Error) => vivo && setEstado({ ruta, error: e.message }))
    return () => {
      vivo = false
    }
  }, [ruta])
  const actual = estado.ruta === ruta
  return { datos: actual ? estado.datos : undefined, error: actual ? estado.error : undefined }
}

export const useResumen = () => useDatos<Resumen>('resumen.json')
export const useFuentes = () => useDatos<Fuente[]>('fuentes.json')
export const usePublicaciones = () => useDatos<Publicacion[]>('publicaciones.json')
export const useNarrativas = () => useDatos<Narrativa[]>('narrativas.json')
export const useGrupos = () => useDatos<Grupo[]>('coordinacion.json')
export const useComentarios = (id: string | undefined) =>
  useDatos<Comentario[]>(id ? `comentarios/${id}.json` : null)

const fmt = new Intl.NumberFormat('es-AR')
export const num = (n: number | null | undefined) => (n == null ? '—' : fmt.format(n))
export const pct = (n: number, total: number) => (total ? `${Math.round((100 * n) / total)}%` : '0%')
export function fecha(iso: string, conHora = true) {
  const d = new Date(iso)
  return d.toLocaleString('es-AR', {
    timeZone: 'America/Argentina/Buenos_Aires',
    day: 'numeric',
    month: 'short',
    ...(conHora ? { hour: '2-digit', minute: '2-digit' } : {}),
  })
}

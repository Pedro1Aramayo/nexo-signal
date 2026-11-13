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
      }).catch((error: unknown) => {
        cache.delete(ruta)
        throw error
      }),
    )
  }
  return cache.get(ruta) as Promise<T>
}

export function useDatos<T>(ruta: string | null) {
  const [estado, setEstado] = useState<{ ruta: string | null; data?: T; error?: string }>({ ruta: null })
  const [intento, setIntento] = useState(0)
  useEffect(() => {
    if (!ruta) return
    let vivo = true
    cargar<T>(ruta)
      .then((data) => vivo && setEstado({ ruta, data }))
      .catch((error: unknown) => vivo && setEstado({
        ruta,
        error: error instanceof Error ? error.message : 'No se pudieron cargar los datos.',
      }))
    return () => {
      vivo = false
    }
  }, [ruta, intento])
  const actual = estado.ruta === ruta
  const reintentar = () => {
    if (!ruta) return
    cache.delete(ruta)
    setEstado({ ruta })
    setIntento((actual) => actual + 1)
  }
  return {
    data: actual ? estado.data : undefined,
    error: actual ? estado.error : undefined,
    reintentar,
  }
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

export function anio(iso: string) {
  const d = new Date(iso)
  return Number.isNaN(d.getTime())
    ? ''
    : d.toLocaleString('es-AR', {
        timeZone: 'America/Argentina/Buenos_Aires',
        year: 'numeric',
      })
}

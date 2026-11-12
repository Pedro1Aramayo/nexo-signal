export type Plataforma = 'instagram' | 'facebook' | 'x' | 'youtube' | 'tiktok'
export type Categoria = 'consulta' | 'queja' | 'elogio' | 'sugerencia' | 'otro'
export type Conteo = Partial<Record<Categoria, number>>

export interface Resumen {
  dataset: string
  comentarios: number
  publicaciones: number
  fuentes: number
  cuentas: number
  narrativas: number
  ruido_frac: number
  grupos_coordinados: number
  cuentas_coordinadas: number
  categorias: Conteo
  costo: { segundos: number; usd_ia: number; hardware: string; notas: string }
  fecha_min: string
  fecha_max: string
}

export interface Fuente {
  fuente_id: string
  nombre: string
  tipo: string
  plataforma_demo: Plataforma
  publicaciones: number
  comentarios: number
}

export interface NarrativaPub {
  narrativa: string
  titulo: string
  n: number
  apoya: number
  rechaza: number
}

export interface Publicacion {
  publicacion_id: string
  fuente_id: string
  fuente_nombre: string
  fuente_tipo: string
  plataforma_demo: Plataforma
  fecha: string
  titular: string
  comentarios: number
  coordinados: number
  ruido: number
  me_gusta_total: number
  categorias: Conteo
  narrativas: NarrativaPub[]
}

export interface Narrativa {
  narrativa: string
  titulo: string
  frases_clave: string[]
  fecha_origen: string
  total: number
  apoya: number
  rechaza: number
  organico_total: number
  coordinados: number
  serie: { dia: string; total: number; organico: number }[]
  publicaciones_top: { publicacion_id: string; titular?: string; n: number }[]
}

export interface Grupo {
  grupo: string
  canal: string
  comentarios: number
  n_cuentas: number
  n_publicaciones: number
  densidad: number | null
  ratio: number | null
  frac_nocturna: number | null
  mediana_seguidores: number | null
  mediana_dias_cuenta_al_primer_comentario: number | null
  cuentas: { cuenta_id: string; usuario: string; fecha_creacion: string; seguidores: number }[]
  narrativas: { narrativa: string; n: number }[]
  publicaciones_top: { publicacion_id: string; titular: string; n: number }[]
  ejemplos: string[]
}

export interface Comentario {
  id: string
  cuenta_id: string
  usuario: string
  fecha: string
  texto: string
  respuesta_a: string
  me_gusta: number
  narrativa: string | null
  postura: 'apoya' | 'rechaza' | null
  categoria: Categoria
  grupo: string | null
}

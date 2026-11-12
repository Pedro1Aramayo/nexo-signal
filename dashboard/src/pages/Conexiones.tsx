import { PlugZap, Lock, CheckCircle2 } from 'lucide-react'
import { Encabezado, MarcaPlataforma, ORDEN_PLATAFORMAS, PLATAFORMAS, Tarjeta } from '../ui'

const API: Record<string, string> = {
  instagram: 'Instagram Graph API (cuentas profesionales) · OAuth de Meta',
  facebook: 'Graph API de páginas · OAuth de Meta',
  tiktok: 'TikTok Login Kit + API de comentarios para cuentas autorizadas',
  youtube: 'YouTube Data API v3 · OAuth de Google',
  x: 'X API v2 · OAuth 2.0 con PKCE',
}

export default function Conexiones() {
  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <Encabezado titulo="Conexiones" sub="NEXO CONNECT: integración futura con cuentas autorizadas mediante APIs oficiales." icono={<PlugZap className="h-7 w-7" />} />
      <Tarjeta className="flex items-start gap-3 bg-amber-50 p-5 text-lg text-amber-900 ring-1 ring-amber-200">
        <Lock className="mt-1 h-5 w-5 shrink-0" /> Ninguna red está conectada. Esta versión usa solo datos sintéticos de QualyData; las conexiones están planificadas, no implementadas.
      </Tarjeta>
      <div className="grid gap-4 md:grid-cols-2">
        {ORDEN_PLATAFORMAS.map((p) => (
          <Tarjeta key={p} className="flex items-center gap-4 p-5">
            <MarcaPlataforma p={p} size="h-14 w-14" />
            <div className="min-w-0 flex-1">
              <div className="text-xl font-semibold">{PLATAFORMAS[p].nombre}</div>
              <div className="text-slate-500">{API[p]}</div>
            </div>
            <button disabled className="cursor-not-allowed rounded-xl bg-slate-100 px-4 py-2.5 font-semibold text-slate-400">Próximamente</button>
          </Tarjeta>
        ))}
      </div>
      <Tarjeta className="p-6">
        <h2 className="text-xl font-bold">Cómo funcionará</h2>
        <ol className="mt-4 space-y-3 text-lg">
          {[
            'La persona dueña de la cuenta inicia sesión en la red y autoriza a NEXO SIGNAL con OAuth oficial (solo permisos de lectura de publicaciones y comentarios).',
            'NEXO SIGNAL guarda el token cifrado y descarga publicaciones y comentarios por la API oficial, respetando límites y términos de uso.',
            'NEXO ENGINE clasifica los comentarios (consultas, quejas, elogios, sugerencias), detecta narrativas, posturas y coordinación, en CPU y sin IA paga.',
            'La cuenta puede revocar el acceso en cualquier momento; al revocar se borran sus datos.',
          ].map((t) => (
            <li key={t} className="flex gap-3"><CheckCircle2 className="mt-1 h-5 w-5 shrink-0 text-emerald-600" />{t}</li>
          ))}
        </ol>
      </Tarjeta>
    </div>
  )
}

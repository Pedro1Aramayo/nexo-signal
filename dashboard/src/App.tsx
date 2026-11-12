import { useEffect, useState } from 'react'

type Resumen = {
  comentarios: number
}

function App() {
  const [total, setTotal] = useState<number | null>(null)

  useEffect(() => {
    fetch('/data/resumen.json')
      .then((response) => {
        if (!response.ok) {
          throw new Error('No se pudo cargar el resumen')
        }
        return response.json() as Promise<Resumen>
      })
      .then((resumen) => setTotal(resumen.comentarios))
      .catch(() => setTotal(null))
  }, [])

  return (
    <main>
      <h1>NEXO Dashboard</h1>
      <p>Total de comentarios: {total ?? '—'}</p>
    </main>
  )
}

export default App

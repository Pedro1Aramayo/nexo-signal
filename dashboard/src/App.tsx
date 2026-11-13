import { HashRouter, Route, Routes } from 'react-router-dom'
import { Layout } from './ui'
import Inicio from './pages/Inicio'
import Detalle from './pages/Detalle'
import Coordinacion from './pages/Coordinacion'
import OrganicLens from './pages/OrganicLens'
import Conexiones from './pages/Conexiones'
import Narrativas from './pages/Narrativas'

export default function App() {
  return (
    <HashRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Inicio />} />
          <Route path="publicacion/:id" element={<Detalle />} />
          <Route path="narrativas" element={<Narrativas />} />
          <Route path="coordinacion" element={<Coordinacion />} />
          <Route path="organic-lens" element={<OrganicLens />} />
          <Route path="conexiones" element={<Conexiones />} />
        </Route>
      </Routes>
    </HashRouter>
  )
}

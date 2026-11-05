import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./componentes/Layout";
import { Alertas } from "./paginas/Alertas";
import { DetalleAlerta } from "./paginas/DetalleAlerta";
import { EnConstruccion } from "./paginas/EnConstruccion";
import { Inicio } from "./paginas/Inicio";
import { Login } from "./paginas/Login";
import { NoEncontrada } from "./paginas/NoEncontrada";
import { RutaModulo, RutaProtegida } from "./sesion/Rutas";
import { SesionProvider } from "./sesion/SesionContext";

export function App() {
  return (
    <BrowserRouter>
      <SesionProvider>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route element={<RutaProtegida />}>
            <Route element={<Layout />}>
              <Route index element={<Inicio />} />
              <Route path="perfil" element={<RutaModulo codigo="MI_PERFIL"><EnConstruccion titulo="Mi perfil" /></RutaModulo>} />
              <Route path="directorio" element={<RutaModulo codigo="DIRECTORIO"><EnConstruccion titulo="Directorio" /></RutaModulo>} />
              <Route path="estructura" element={<RutaModulo codigo="ESTRUCTURA"><EnConstruccion titulo="Estructura" /></RutaModulo>} />
              <Route path="cierres" element={<RutaModulo codigo="CIERRES"><EnConstruccion titulo="Cierres de caja" /></RutaModulo>} />
              <Route path="alertas" element={<RutaModulo codigo="ALERTAS"><Alertas /></RutaModulo>} />
              <Route path="alertas/:id" element={<RutaModulo codigo="ALERTAS"><DetalleAlerta /></RutaModulo>} />
              <Route path="*" element={<NoEncontrada />} />
            </Route>
          </Route>
        </Routes>
      </SesionProvider>
    </BrowserRouter>
  );
}

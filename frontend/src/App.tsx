import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./componentes/Layout";
import { Alertas } from "./paginas/Alertas";
import { Cierres } from "./paginas/Cierres";
import { Departamentos } from "./paginas/Departamentos";
import { DetalleAlerta } from "./paginas/DetalleAlerta";
import { Directorio } from "./paginas/Directorio";
import { Estructura } from "./paginas/Estructura";
import { FichaPersona } from "./paginas/FichaPersona";
import { Inicio } from "./paginas/Inicio";
import { Login } from "./paginas/Login";
import { NoEncontrada } from "./paginas/NoEncontrada";
import { Perfil } from "./paginas/Perfil";
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
              <Route path="perfil" element={<RutaModulo codigo="MI_PERFIL"><Perfil /></RutaModulo>} />
              <Route path="departamentos" element={<RutaModulo codigo="DEPARTAMENTOS"><Departamentos /></RutaModulo>} />
              <Route path="directorio" element={<RutaModulo codigo="DIRECTORIO"><Directorio /></RutaModulo>} />
              <Route path="directorio/:id" element={<RutaModulo codigo="DIRECTORIO"><FichaPersona /></RutaModulo>} />
              <Route path="estructura" element={<RutaModulo codigo="ESTRUCTURA"><Estructura /></RutaModulo>} />
              <Route path="cierres" element={<RutaModulo codigo="CIERRES"><Cierres /></RutaModulo>} />
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

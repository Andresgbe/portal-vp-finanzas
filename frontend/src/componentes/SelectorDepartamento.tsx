import type { DepartamentoResumen } from "../api/tipos";

/** Solo se muestra si hay más de uno: el backend le devuelve varios únicamente al Administrador. */
export function SelectorDepartamento({ departamentos, valor, alCambiar }: {
  departamentos: DepartamentoResumen[];
  valor: number;
  alCambiar: (id: number) => void;
}) {
  if (departamentos.length < 2) return null;

  return (
    <div className="campo selector-departamento">
      <label htmlFor="departamento">Departamento</label>
      <select id="departamento" value={valor} onChange={(e) => alCambiar(Number(e.target.value))}>
        {departamentos.map((d) => <option key={d.id} value={d.id}>{d.nombre}</option>)}
      </select>
    </div>
  );
}

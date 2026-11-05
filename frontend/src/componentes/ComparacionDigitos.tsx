import { compararMontos, formatMonto } from "../utils/formato";

function FilaDigitos({ titulo, monto, otro }: { titulo: string; monto: string; otro: string }) {
  return (
    <div>
      <div className="etiqueta">{titulo}</div>
      {/* Un lector de pantalla lee el monto completo, no dígito por dígito */}
      <div className="digitos" role="img" aria-label={monto}>
        {compararMontos(monto, otro).map(({ caracter, cambia }, i) => {
          const esSeparador = caracter === "." || caracter === ",";
          if (esSeparador) return <span key={i} className="digito-separador">{caracter}</span>;
          return <span key={i} className={cambia ? "digito digito-cambia" : "digito"}>{caracter}</span>;
        })}
      </div>
    </div>
  );
}

/** Los dos montos alineados, con los dígitos intercambiados resaltados. */
export function ComparacionDigitos({ declarado, sistema }: { declarado: string; sistema: string }) {
  const montoDeclarado = formatMonto(declarado);
  const montoSistema = formatMonto(sistema);

  return (
    <div className="comparacion">
      <FilaDigitos titulo="Declarado por el cajero" monto={montoDeclarado} otro={montoSistema} />
      <FilaDigitos titulo="Registrado en el sistema" monto={montoSistema} otro={montoDeclarado} />
    </div>
  );
}

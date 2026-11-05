import { describe, expect, it } from "vitest";
import {
  compararMontos,
  esNegativo,
  formatDiferencia,
  formatFecha,
  formatMonto,
  iniciales,
  normalizarMonto,
} from "./formato";

describe("formatMonto", () => {
  it("agrega separadores de miles y coma decimal", () => {
    expect(formatMonto("6765.86")).toBe("6.765,86");
    expect(formatMonto("1234567.50")).toBe("1.234.567,50");
    expect(formatMonto("800.50")).toBe("800,50");
  });

  it("completa decimales faltantes", () => {
    expect(formatMonto("3954.9")).toBe("3.954,90");
    expect(formatMonto("12")).toBe("12,00");
  });

  it("no pierde precisión con montos grandes", () => {
    expect(formatMonto("9999999999.99")).toBe("9.999.999.999,99");
  });
});

describe("formatDiferencia", () => {
  it("muestra el signo", () => {
    expect(formatDiferencia("9.00")).toBe("+9,00");
    expect(formatDiferencia("-150.00")).toBe("−150,00");
  });

  it("no le pone signo al cero", () => {
    expect(formatDiferencia("0.00")).toBe("0,00");
    expect(formatDiferencia("-0.00")).toBe("0,00");
  });
});

describe("esNegativo", () => {
  it("distingue faltantes de sobrantes y de cero", () => {
    expect(esNegativo("-1.01")).toBe(true);
    expect(esNegativo("3.84")).toBe(false);
    expect(esNegativo("-0.00")).toBe(false);
  });
});

describe("normalizarMonto", () => {
  it("acepta los formatos válidos", () => {
    expect(normalizarMonto("1520")).toBe("1520.00");
    expect(normalizarMonto("1520,5")).toBe("1520.50");
    expect(normalizarMonto("1.520,50")).toBe("1520.50");
    expect(normalizarMonto(" 12.345.678,90 ")).toBe("12345678.90");
  });

  it("rechaza los inválidos", () => {
    expect(normalizarMonto("1520.50")).toBeNull();
    expect(normalizarMonto("1,234,56")).toBeNull();
    expect(normalizarMonto("-5")).toBeNull();
    expect(normalizarMonto("abc")).toBeNull();
    expect(normalizarMonto("")).toBeNull();
  });
});

describe("compararMontos", () => {
  it("marca solo los dígitos intercambiados", () => {
    const resultado = compararMontos("3.954,90", "3.945,90");
    expect(resultado.filter((c) => c.cambia).map((c) => c.caracter)).toEqual(["5", "4"]);
  });
});

describe("otros formatos", () => {
  it("formatea la fecha sin correr el día", () => {
    expect(formatFecha("2026-06-10")).toBe("10/06/2026");
  });

  it("obtiene las iniciales", () => {
    expect(iniciales("Tomás Iriarte")).toBe("TI");
  });
});

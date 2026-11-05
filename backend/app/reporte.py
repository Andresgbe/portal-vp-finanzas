"""Genera el reporte de cierres de caja en PDF."""
from datetime import datetime, timezone
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .deteccion import _fmt
from .models import CierreCaja

AZUL = colors.HexColor("#0B3D91")
LINEA = colors.HexColor("#D9E0EC")
TENUE = colors.HexColor("#5B6577")
ROJO = colors.HexColor("#9B2A22")

TITULO = ParagraphStyle("titulo", fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=AZUL)
SUBTITULO = ParagraphStyle("subtitulo", fontName="Helvetica", fontSize=10, leading=14, textColor=TENUE)
CELDA = ParagraphStyle("celda", fontName="Helvetica", fontSize=9, leading=11)
CELDA_TENUE = ParagraphStyle("celda_tenue", parent=CELDA, textColor=TENUE)
NOTA = ParagraphStyle("nota", parent=CELDA, fontSize=8, leading=10, textColor=TENUE)
CABECERA = ParagraphStyle("cabecera", fontName="Helvetica-Bold", fontSize=9, leading=11, textColor=colors.white)
CABECERA_DERECHA = ParagraphStyle("cabecera_derecha", parent=CABECERA, alignment=TA_RIGHT)

ANCHOS = [0.85, 1.6, 1.65, 0.95, 0.95, 0.95, 0.65, 1.4]


def _texto(valor: object, estilo: ParagraphStyle = CELDA) -> Paragraph:
    # Paragraph interpreta etiquetas: lo que escribe un usuario (el motivo) debe ir escapado
    return Paragraph(escape(str(valor)), estilo)


def _diferencia(valor: Decimal) -> str:
    if valor == 0:
        return "0,00"
    return f"{'+' if valor > 0 else '-'}{_fmt(abs(valor))}"


def _pie(lienzo, documento) -> None:
    lienzo.saveState()
    lienzo.setFont("Helvetica", 8)
    lienzo.setFillColor(TENUE)
    lienzo.drawString(documento.leftMargin, 0.35 * inch, "Portal VP de Finanzas. Todos los datos son ficticios.")
    lienzo.drawRightString(documento.pagesize[0] - documento.rightMargin, 0.35 * inch, f"Página {documento.page}")
    lienzo.restoreState()


def _fila(c: CierreCaja) -> list:
    inhabilitado = c.estado == "inhabilitado"
    estilo = CELDA_TENUE if inhabilitado else CELDA

    estado = [_texto("Inhabilitado" if inhabilitado else "Activo", estilo)]
    if inhabilitado and c.historial:
        estado.append(_texto(c.historial[-1].motivo, NOTA))

    return [
        _texto(f"{c.fecha:%d/%m/%Y}", estilo), _texto(c.tienda.nombre, estilo), _texto(c.cajero.nombre, estilo),
        _fmt(c.monto_declarado), _fmt(c.monto_sistema), _diferencia(c.diferencia),
        str(len(c.alertas)), estado,
    ]


def generar_pdf_cierres(cierres: list[CierreCaja], generado_por: str, filtros: str) -> bytes:
    salida = BytesIO()
    documento = SimpleDocTemplate(
        salida, pagesize=landscape(letter), title="Reporte de cierres de caja", author="Portal VP de Finanzas",
        leftMargin=0.5 * inch, rightMargin=0.5 * inch, topMargin=0.5 * inch, bottomMargin=0.6 * inch,
    )

    con_alertas = sum(1 for c in cierres if c.alertas)
    inhabilitados = sum(1 for c in cierres if c.estado == "inhabilitado")
    ahora = datetime.now(timezone.utc)

    contenido = [
        Paragraph("Reporte de cierres de caja", TITULO),
        Spacer(1, 4),
        _texto(f"Generado por {generado_por} el {ahora:%d/%m/%Y %H:%M} UTC", SUBTITULO),
        _texto(f"Filtros: {filtros}", SUBTITULO),
        _texto(f"Cierres: {len(cierres)} · Con alertas: {con_alertas} · Inhabilitados: {inhabilitados}", SUBTITULO),
        Spacer(1, 12),
    ]

    if not cierres:
        contenido.append(_texto("No hay cierres con esos filtros."))
    else:
        cabecera = [Paragraph(t, CABECERA) for t in ("Fecha", "Tienda", "Cajero")]
        cabecera += [Paragraph(t, CABECERA_DERECHA) for t in ("Declarado", "Sistema", "Diferencia", "Alertas")]
        cabecera.append(Paragraph("Estado", CABECERA))

        tabla = Table([cabecera] + [_fila(c) for c in cierres],
                      colWidths=[a * inch for a in ANCHOS], repeatRows=1)
        estilos = [
            ("BACKGROUND", (0, 0), (-1, 0), AZUL),
            ("FONTNAME", (3, 1), (6, -1), "Helvetica"),
            ("FONTSIZE", (3, 1), (6, -1), 9),
            ("ALIGN", (3, 1), (6, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LINEBELOW", (0, 1), (-1, -1), 0.5, LINEA),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
        # El color acompaña al signo: un faltante se distingue también sin color
        for i, c in enumerate(cierres, start=1):
            if c.estado == "inhabilitado":
                estilos.append(("TEXTCOLOR", (3, i), (6, i), TENUE))
            elif c.diferencia < 0:
                estilos.append(("TEXTCOLOR", (5, i), (5, i), ROJO))
        tabla.setStyle(TableStyle(estilos))
        contenido.append(tabla)

    documento.build(contenido, onFirstPage=_pie, onLaterPages=_pie)
    return salida.getvalue()

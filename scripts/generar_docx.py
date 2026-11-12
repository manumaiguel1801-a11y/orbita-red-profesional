"""Convierte docs/documento_academico.md en docs/Documento_Academico_Orbita.docx con formato de informe académico.

Uso:  python scripts/generar_docx.py
En Windows con Microsoft Word instalado, al final se actualiza automáticamente la tabla de contenido.
"""
import re
import subprocess
import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_ROW_HEIGHT_RULE, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

RAIZ = Path(__file__).resolve().parent.parent
ORIGEN = RAIZ / "docs" / "documento_academico.md"
DESTINO = RAIZ / "docs" / "Documento_Academico_Orbita_final.docx"

# Paleta sobria (violeta institucional de Órbita)
OSCURO = RGBColor(0x2E, 0x10, 0x65)
PRIMARIO = RGBColor(0x5B, 0x21, 0xB6)
ACENTO = RGBColor(0x7C, 0x3A, 0xED)
TEXTO = RGBColor(0x1F, 0x29, 0x37)
GRIS = RGBColor(0x6B, 0x72, 0x80)
CODIGO = RGBColor(0x4C, 0x1D, 0x95)
HEX_PRIMARIO, HEX_SUAVE, HEX_BORDE, HEX_CODIGO = "5B21B6", "F5F3FF", "DDD6FE", "F7F7FB"
ANCHO_UTIL = 16.6  # cm (carta con márgenes de 2,5 cm)
FUENTE = "Calibri"


# ----------------------------------------------------------------------------- utilidades XML
def _el(tag, **attrs):
    e = OxmlElement(tag)
    for k, v in attrs.items():
        e.set(qn(k), v)
    return e


def sombrear(celda, color):
    celda._tc.get_or_add_tcPr().append(_el("w:shd", **{"w:val": "clear", "w:color": "auto", "w:fill": color}))


def bordes_celda(celda, color=HEX_BORDE, tam="4", estilo="single", lados=("top", "left", "bottom", "right")):
    b = _el("w:tcBorders")
    for lado in ("top", "left", "bottom", "right"):
        if lado in lados:
            b.append(_el(f"w:{lado}", **{"w:val": estilo, "w:sz": tam, "w:color": color}))
        else:
            b.append(_el(f"w:{lado}", **{"w:val": "nil"}))
    celda._tc.get_or_add_tcPr().append(b)


def margenes_celda(celda, sup=70, izq=110):
    m = _el("w:tcMar")
    for lado, v in (("top", sup), ("bottom", sup), ("left", izq), ("right", izq)):
        m.append(_el(f"w:{lado}", **{"w:w": str(v), "w:type": "dxa"}))
    celda._tc.get_or_add_tcPr().append(m)


def borde_parrafo(p, lado="bottom", color=HEX_BORDE, tam="8", espacio="4"):
    pPr = p._p.get_or_add_pPr()
    bdr = _el("w:pBdr")
    bdr.append(_el(f"w:{lado}", **{"w:val": "single", "w:sz": tam, "w:space": espacio, "w:color": color}))
    pPr.append(bdr)


def repetir_encabezado(fila):
    fila._tr.get_or_add_trPr().append(_el("w:tblHeader", **{"w:val": "true"}))


def no_partir(fila):
    fila._tr.get_or_add_trPr().append(_el("w:cantSplit", **{"w:val": "true"}))


def campo(run, instruccion):
    run._r.append(_el("w:fldChar", **{"w:fldCharType": "begin"}))
    it = _el("w:instrText", **{"xml:space": "preserve"}); it.text = instruccion; run._r.append(it)
    run._r.append(_el("w:fldChar", **{"w:fldCharType": "separate"}))
    t = OxmlElement("w:t"); t.text = "1"; run._r.append(t)
    run._r.append(_el("w:fldChar", **{"w:fldCharType": "end"}))


def formato(p, antes=0, despues=6, interlineado=1.15, alin=None, sangria=None, colgante=None, junto=False):
    f = p.paragraph_format
    f.space_before, f.space_after = Pt(antes), Pt(despues)
    f.line_spacing = interlineado
    if alin is not None:
        p.alignment = alin
    if sangria is not None:
        f.left_indent = Cm(sangria)
    if colgante is not None:
        f.first_line_indent = Cm(-colgante)
    if junto:
        f.keep_with_next = True
    return p


# ----------------------------------------------------------------------------- texto en línea
TOKEN = re.compile(r"(`[^`]+`|\*\*|\*)")


def en_linea(p, texto, tam=None, color=None, negrita=False, cursiva=False):
    """Interpreta **negrita**, *cursiva*, `código` (también anidados) y [texto](url)."""
    texto = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", texto)
    b, i = negrita, cursiva
    for parte in TOKEN.split(texto):
        if not parte:
            continue
        if parte == "**":
            b = not b; continue
        if parte == "*":
            i = not i; continue
        if parte.startswith("`") and parte.endswith("`") and len(parte) > 1:
            r = p.add_run(parte[1:-1]); r.font.name = "Consolas"
            r.font.size = Pt((tam.pt if tam else 11) - 1.5); r.font.color.rgb = CODIGO; r.bold = b
            continue
        r = p.add_run(parte); r.bold = b; r.italic = i
        if tam:
            r.font.size = tam
        if color:
            r.font.color.rgb = color
    return p


def sin_marcas(texto):
    return re.sub(r"[`*]", "", re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", texto))


# ----------------------------------------------------------------------------- estilos del documento
def configurar(doc):
    s = doc.sections[0]
    s.page_width, s.page_height = Cm(21.59), Cm(27.94)
    s.left_margin = s.right_margin = Cm(2.5); s.top_margin = Cm(2.5); s.bottom_margin = Cm(2.2)
    s.header_distance = s.footer_distance = Cm(1.2)

    normal = doc.styles["Normal"]
    normal.font.name = FUENTE; normal.font.size = Pt(11); normal.font.color.rgb = TEXTO
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), FUENTE)
    normal.paragraph_format.space_after = Pt(6); normal.paragraph_format.line_spacing = 1.15

    for nivel, tam, color, antes, despues in ((1, 20, OSCURO, 0, 10), (2, 14, PRIMARIO, 16, 6), (3, 12, OSCURO, 12, 4)):
        st = doc.styles[f"Heading {nivel}"]
        st.font.name = FUENTE; st.font.size = Pt(tam); st.font.bold = True; st.font.color.rgb = color
        st.font.italic = False
        rpr = st.element.get_or_add_rPr()
        rfonts = rpr.find(qn("w:rFonts"))
        if rfonts is None:
            rfonts = OxmlElement("w:rFonts"); rpr.append(rfonts)
        for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
            rfonts.set(qn(a), FUENTE)
        for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            if rfonts.get(qn(a)) is not None:
                del rfonts.attrib[qn(a)]
        pf = st.paragraph_format
        pf.space_before, pf.space_after = Pt(antes), Pt(despues); pf.keep_with_next = True

    for nivel in (1, 2):
        st = doc.styles[f"TOC {nivel}"] if f"TOC {nivel}" in [x.name for x in doc.styles] else None
        if st is not None:
            st.font.name = FUENTE; st.font.size = Pt(11 if nivel == 1 else 10.5)


def encabezado_pie(seccion):
    seccion.different_first_page_header_footer = False
    h = seccion.header.paragraphs[0]; h.text = ""
    formato(h, despues=0, alin=WD_ALIGN_PARAGRAPH.RIGHT)
    r = h.add_run("Bases de datos orientadas a grafos  ·  Órbita, red profesional")
    r.font.size = Pt(8.5); r.font.color.rgb = GRIS
    borde_parrafo(h, "bottom", HEX_BORDE, "6", "4")

    f = seccion.footer.paragraphs[0]; f.text = ""
    formato(f, despues=0, alin=WD_ALIGN_PARAGRAPH.CENTER)
    for txt, ins in (("Página ", None), (None, "PAGE"), (" de ", None), (None, "NUMPAGES")):
        r = f.add_run(txt or "")
        if ins:
            campo(r, ins)
        r.font.size = Pt(8.5); r.font.color.rgb = GRIS


# ----------------------------------------------------------------------------- portada e índice
def portada(doc, lineas):
    titulo = next(l[2:] for l in lineas if l.startswith("# "))
    datos = {}
    integrantes = []
    for l in lineas:
        m = re.match(r"^\*\*(.+?):\*\*\s*(.*)$", l.strip())
        if m and m.group(2):
            datos[m.group(1)] = m.group(2)
        elif l.strip().startswith("- "):
            integrantes.append(l.strip()[2:])
    curso = next((sin_marcas(l) for l in lineas if l.startswith("**Bases de Datos")), "")
    fecha = next((sin_marcas(l) for l in lineas if re.match(r"^\*\*\w+ de \d{4}\*\*$", l.strip())), "")

    # Franja superior
    t = doc.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = t.cell(0, 0); c.width = Cm(ANCHO_UTIL); sombrear(c, HEX_PRIMARIO); bordes_celda(c, lados=())
    margenes_celda(c, 260, 300)
    p = formato(c.paragraphs[0], despues=2)
    r = p.add_run("PROYECTO DE INVESTIGACIÓN Y DESARROLLO (I+D)"); r.bold = True; r.font.size = Pt(9.5)
    r.font.color.rgb = RGBColor(0xED, 0xE9, 0xFE)
    p = formato(c.add_paragraph(), despues=0)
    r = p.add_run(curso.split("—")[0].strip()); r.font.size = Pt(12); r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for _ in range(4):
        formato(doc.add_paragraph(), despues=0)
    p = formato(doc.add_paragraph(), despues=14, interlineado=1.05)
    r = p.add_run(titulo); r.bold = True; r.font.size = Pt(26); r.font.color.rgb = OSCURO
    p = formato(doc.add_paragraph(), despues=4)
    borde_parrafo(p, "top", "7C3AED", "18", "1")
    p = formato(doc.add_paragraph(), despues=2)
    r = p.add_run("Órbita"); r.bold = True; r.font.size = Pt(15); r.font.color.rgb = ACENTO
    r = p.add_run("  ·  Red profesional construida sobre Neo4j"); r.font.size = Pt(15); r.font.color.rgb = GRIS
    p = formato(doc.add_paragraph(), despues=0)
    r = p.add_run(sin_marcas(datos.get("Tema", ""))); r.font.size = Pt(11); r.font.color.rgb = GRIS

    for _ in range(7):
        formato(doc.add_paragraph(), despues=0)

    # Bloque de integrantes y datos
    t = doc.add_table(rows=1, cols=2); t.alignment = WD_TABLE_ALIGNMENT.LEFT; t.autofit = False
    izq, der = t.cell(0, 0), t.cell(0, 1)
    izq.width, der.width = Cm(8.3), Cm(8.3)
    for celda in (izq, der):
        bordes_celda(celda, lados=()); margenes_celda(celda, 40, 0)
    bordes_celda(izq, "7C3AED", "18", lados=("left",)); margenes_celda(izq, 40, 220)

    def bloque(celda, etiqueta, valores, primero=True):
        p = celda.paragraphs[0] if primero else celda.add_paragraph()
        formato(p, antes=0 if primero else 10, despues=3)
        r = p.add_run(etiqueta.upper()); r.bold = True; r.font.size = Pt(8.5); r.font.color.rgb = ACENTO
        for v in valores:
            p = formato(celda.add_paragraph(), despues=1)
            r = p.add_run(v); r.font.size = Pt(12); r.font.color.rgb = TEXTO

    bloque(izq, "Integrantes", integrantes)
    bloque(der, "Asignatura", ["Bases de Datos", "Grupo 202630-2424"])
    bloque(der, "Tecnologías", ["Neo4j AuraDB · Cypher", "Python · Streamlit"], primero=False)
    bloque(der, "Fecha", [fecha], primero=False)

    p = doc.add_paragraph(); p.add_run().add_break(WD_BREAK.PAGE)


def tabla_contenido(doc):
    p = formato(doc.add_paragraph(), despues=10)
    r = p.add_run("Contenido"); r.bold = True; r.font.size = Pt(20); r.font.color.rgb = OSCURO
    borde_parrafo(p, "bottom", "7C3AED", "12", "6")
    p = formato(doc.add_paragraph(), despues=0)
    campo(p.add_run(), r'TOC \o "1-2" \h \z \u')
    p.runs[0]._r.findall(qn("w:t"))[0].text = "Clic derecho → «Actualizar campo» para generar el índice."
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# ----------------------------------------------------------------------------- bloques
def bloque_codigo(doc, lineas):
    t = doc.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = t.cell(0, 0); c.width = Cm(ANCHO_UTIL); sombrear(c, HEX_CODIGO)
    bordes_celda(c, "7C3AED", "18", lados=("left",)); margenes_celda(c, 90, 180)
    for k, l in enumerate(lineas):
        p = c.paragraphs[0] if k == 0 else c.add_paragraph()
        formato(p, despues=0, interlineado=1.0)
        r = p.add_run(l if l else " "); r.font.name = "Consolas"; r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(0x37, 0x41, 0x51) if not l.strip().startswith("//") else GRIS
    formato(doc.add_paragraph(), despues=2)


def anchos(filas):
    """Cada columna recibe al menos el ancho de su palabra más larga; el resto se reparte según el contenido."""
    n = len(filas[0])
    cm_por_car = 0.19
    minimos, pesos = [], []
    for i in range(n):
        celdas = [sin_marcas(f[i]) if i < len(f) else "" for f in filas]
        palabra = max((len(w) for c in celdas for w in re.split(r"[\s/]+", c)), default=4)
        minimos.append(min(max(palabra, 5) * cm_por_car + 0.45, 5.5))
        pesos.append(max(min(max(len(c) for c in celdas), 70), 6))
    libre = max(ANCHO_UTIL - sum(minimos), 0)
    extra = [libre * (p_ - m / cm_por_car) / max(sum(pesos) - sum(mm / cm_por_car for mm in minimos), 1)
             if p_ * cm_por_car > m else 0 for p_, m in zip(pesos, minimos)]
    w = [m + max(e, 0) for m, e in zip(minimos, extra)]
    escala = ANCHO_UTIL / sum(w)
    return [x * escala for x in w]


def tabla(doc, filas):
    n = len(filas[0])
    t = doc.add_table(rows=len(filas), cols=n); t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
    w = anchos(filas)
    for fi, fila in enumerate(filas):
        no_partir(t.rows[fi])
        if fi == 0:
            repetir_encabezado(t.rows[0])
        for ci in range(n):
            celda = t.cell(fi, ci); celda.width = Cm(w[ci])
            celda.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            margenes_celda(celda)
            bordes_celda(celda, HEX_BORDE, "4", lados=("bottom",) if fi else ())
            val = fila[ci] if ci < len(fila) else ""
            p = formato(celda.paragraphs[0], despues=0, interlineado=1.05)
            if fi == 0:
                sombrear(celda, HEX_PRIMARIO)
                en_linea(p, sin_marcas(val), Pt(9), RGBColor(0xFF, 0xFF, 0xFF), negrita=True)
            else:
                if fi % 2 == 0:
                    sombrear(celda, HEX_SUAVE)
                en_linea(p, val, Pt(9))
    formato(doc.add_paragraph(), despues=4)


def espacio_imagen(doc, leyenda):
    t = doc.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    fila = t.rows[0]; fila.height = Cm(8); fila.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST; no_partir(fila)
    c = fila.cells[0]; c.width = Cm(ANCHO_UTIL); sombrear(c, "FAFAFF")
    bordes_celda(c, "A78BFA", "8", "dashed"); c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    p = formato(c.paragraphs[0], despues=0, alin=WD_ALIGN_PARAGRAPH.CENTER)
    r = p.add_run("Insertar imagen aquí"); r.font.size = Pt(11); r.bold = True; r.font.color.rgb = RGBColor(0xA7, 0x8B, 0xFA)
    p.paragraph_format.keep_with_next = True
    leyenda_figura(doc, leyenda)


def leyenda_figura(doc, texto):
    p = formato(doc.add_paragraph(), antes=4, despues=12, alin=WD_ALIGN_PARAGRAPH.CENTER)
    m = re.match(r"^(Figura \d+\.)\s*(.*)$", texto)
    if m:
        r = p.add_run(m.group(1) + " "); r.bold = True; r.font.size = Pt(9); r.font.color.rgb = PRIMARIO
        texto = m.group(2)
    r = p.add_run(texto); r.italic = True; r.font.size = Pt(9); r.font.color.rgb = GRIS


def cita(doc, texto):
    t = doc.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = t.cell(0, 0); c.width = Cm(ANCHO_UTIL); sombrear(c, HEX_SUAVE)
    bordes_celda(c, "7C3AED", "18", lados=("left",)); margenes_celda(c, 80, 180)
    en_linea(formato(c.paragraphs[0], despues=0), texto, Pt(10.5))
    formato(doc.add_paragraph(), despues=2)


# ----------------------------------------------------------------------------- programa
def main():
    doc = Document()
    configurar(doc)
    lineas = ORIGEN.read_text(encoding="utf-8").splitlines()
    fin_portada = lineas.index("---")
    portada(doc, lineas[:fin_portada])

    sec = doc.add_section(WD_SECTION.CONTINUOUS)  # el contenido lleva encabezado y pie; la portada no
    sec.header.is_linked_to_previous = False; sec.footer.is_linked_to_previous = False
    encabezado_pie(sec)
    doc.sections[0].different_first_page_header_footer = True
    tabla_contenido(doc)

    primera_h2 = True
    i = fin_portada + 1
    while i < len(lineas):
        l = lineas[i]
        if l.startswith("```"):
            lang = l[3:].strip(); bloque = []; i += 1
            while i < len(lineas) and not lineas[i].startswith("```"):
                bloque.append(lineas[i]); i += 1
            i += 1
            if lang != "mermaid":
                bloque_codigo(doc, bloque)
            continue
        if l.startswith("|"):
            filas = []
            while i < len(lineas) and lineas[i].startswith("|"):
                if not re.match(r"^\|[\s:|-]+\|$", lineas[i]):
                    filas.append([c.strip() for c in lineas[i].strip().strip("|").split("|")])
                i += 1
            tabla(doc, filas)
            continue
        m = re.match(r"^(#{1,3}) (.*)", l)
        if m:
            nivel = len(m.group(1)) - 1
            if nivel == 1:
                if not primera_h2:
                    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
                primera_h2 = False
                p = doc.add_paragraph(style="Heading 1"); p.add_run(sin_marcas(m.group(2)))
                borde_parrafo(p, "bottom", "7C3AED", "12", "6")
            elif nivel >= 2:
                p = doc.add_paragraph(style=f"Heading {nivel}"); p.add_run(sin_marcas(m.group(2)))
        elif (img := re.match(r"!\[([^\]]*)\]\(([^)]+)\)", l)):
            doc.add_picture(str(RAIZ / "docs" / img.group(2)), width=Cm(15))
            formato(doc.paragraphs[-1], antes=6, despues=0, alin=WD_ALIGN_PARAGRAPH.CENTER, junto=True)
            leyenda_figura(doc, img.group(1))
        elif l.startswith("> **[Espacio para imagen]** "):
            espacio_imagen(doc, l.split("** ", 1)[1])
        elif l.startswith("> "):
            cita(doc, l[2:])
        elif (b := re.match(r"^(\s*)- (.*)", l)):
            nivel = len(b.group(1)) // 2
            p = doc.add_paragraph(style="List Bullet" if nivel == 0 else "List Bullet 2")
            formato(p, despues=3, alin=WD_ALIGN_PARAGRAPH.JUSTIFY)
            en_linea(p, b.group(2))
        elif (n := re.match(r"^(\d+)\. (.*)", l)):
            p = formato(doc.add_paragraph(), despues=3, sangria=0.75, colgante=0.6, alin=WD_ALIGN_PARAGRAPH.JUSTIFY)
            r = p.add_run(f"{n.group(1)}.\t"); r.bold = True; r.font.color.rgb = PRIMARIO
            p.paragraph_format.tab_stops.add_tab_stop(Cm(0.75))
            en_linea(p, n.group(2))
        elif l.strip() in ("---", ""):
            pass
        else:
            en_linea(formato(doc.add_paragraph(), despues=6, alin=WD_ALIGN_PARAGRAPH.JUSTIFY), l)
        i += 1

    doc.save(DESTINO)
    print(DESTINO)
    actualizar_indice()


def actualizar_indice():
    """Con Word instalado (Windows), rellena la tabla de contenido y los números de página."""
    if sys.platform != "win32":
        return
    ps = f"""
$w = New-Object -ComObject Word.Application; $w.Visible = $false; $w.DisplayAlerts = 0
try {{ $d = $w.Documents.Open('{DESTINO}'); $d.TablesOfContents | ForEach-Object {{ $_.Update() }}; $d.Save(); $d.Close(0) }}
finally {{ $w.Quit(); [Runtime.InteropServices.Marshal]::ReleaseComObject($w) | Out-Null }}
"""
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True, timeout=180, capture_output=True)
        print("Tabla de contenido actualizada con Word.")
    except Exception:  # noqa: BLE001
        print("Abra el documento en Word: clic derecho en el índice → Actualizar campo.")


if __name__ == "__main__":
    main()

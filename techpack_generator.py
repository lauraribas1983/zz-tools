#!/usr/bin/env python3
"""
ZZ TechPack Generator
Genera fichas técnicas PDF profesionales para producción en Bangladesh
Sin IA. Sin esperas. Funciona siempre.
"""

import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle,
    Spacer, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import date
import os

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ZZ TechPack Generator",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── STYLES ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background: #0f0f0f; color: #e8e8e8; }
    .main .block-container { padding: 2rem 2rem; max-width: 1100px; }
    h1 { color: #c8ff00 !important; font-size: 1.6rem !important; letter-spacing: 3px; }
    h2 { color: #c8ff00 !important; font-size: 1rem !important; font-weight: 700; letter-spacing: 2px; border-bottom: 1px solid #2c2c2c; padding-bottom: 8px; }
    h3 { color: #e8e8e8 !important; font-size: 0.9rem !important; font-weight: 600; }
    label { color: #999 !important; font-size: 0.82rem !important; }
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stTextArea > div > div > textarea {
        background: #1e1e1e !important;
        border: 1px solid #2c2c2c !important;
        color: #e8e8e8 !important;
        border-radius: 6px !important;
    }
    .stButton > button {
        background: #c8ff00 !important;
        color: #000 !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 12px 28px !important;
        border-radius: 6px !important;
        font-size: 0.9rem !important;
        width: 100%;
    }
    .stButton > button:hover { opacity: 0.85 !important; }
    .stDownloadButton > button {
        background: #1e1e1e !important;
        color: #c8ff00 !important;
        border: 1px solid #c8ff00 !important;
        font-weight: 700 !important;
        border-radius: 6px !important;
        width: 100%;
        padding: 12px !important;
    }
    .stNumberInput > div > div > input { background: #1e1e1e !important; color: #e8e8e8 !important; border: 1px solid #2c2c2c !important; }
    div[data-testid="stExpander"] { background: #161616; border: 1px solid #2c2c2c; border-radius: 8px; }
    .field-hint { font-size: 0.75rem; color: #666; margin-top: 2px; }
    .preview-box { background: #161616; border: 1px solid #2c2c2c; border-radius: 8px; padding: 16px; margin-top: 8px; }
</style>
""", unsafe_allow_html=True)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("# ZZ · TECHPACK GENERATOR")
st.markdown("<p style='color:#888;font-size:0.85rem;margin-top:-12px;'>Ficha técnica profesional para producción Bangladesh · Sin IA · Sin esperas</p>", unsafe_allow_html=True)
st.markdown("---")

# ── FORM ─────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    # DATOS BÁSICOS
    st.markdown("## 01 · DATOS BÁSICOS")
    c1, c2, c3 = st.columns(3)
    with c1:
        ref_id = st.text_input("Referencia ZZ", placeholder="ZZ-TPK-26-001")
        temporada = st.selectbox("Temporada", ["SS26", "AW26", "SS27", "AW27"])
    with c2:
        nombre_prenda = st.text_input("Nombre prenda", placeholder="Hoodie Oversize SC")
        cliente = st.selectbox("Cliente destino", ["Zara", "Pull&Bear", "Bershka", "Mango", "Stradivarius", "Otro"])
    with c3:
        fecha_tp = st.text_input("Fecha", value=str(date.today()))
        categoria = st.selectbox("Categoría", [
            "Hoodie / Sudadera capucha", "Crewneck / Sudadera", "Camiseta manga corta",
            "Camiseta tirantes", "Jersey punto", "Vestido punto", "Jogger",
            "Legging", "Falda punto", "Co-ord top", "Co-ord bottom",
            "Body", "Cárdigan", "Chaqueta punto", "Top canalé"
        ])

    st.markdown("---")

    # DESCRIPCIÓN
    st.markdown("## 02 · DESCRIPCIÓN Y ESTILO")
    c1, c2 = st.columns(2)
    with c1:
        perfil = st.selectbox("Perfil C1·C2·C3", ["C1 — Minimal/Sophisticated", "C2 — Feminine/Romantic", "C3 — Young/Streetwear"])
        estilo_zz = st.selectbox("Estilo ZZ", ["SC — Streetwear Cultural", "SG — Streetwear Gráfico", "SM — Streetwear Minimal", "RD — Retro Deportivo", "QL — Quiet Luxury", "PM — Preppy Moderno"])
    with c2:
        fit = st.selectbox("Fit / Silueta", [
            "OS — Oversize (hombro caído 4-6cm)", "BX — Boxy (hombro cuadrado)",
            "RX — Relaxed", "RG — Regular", "FT — Fitted / Ajustado",
            "CR — Crop (44-52cm)", "MX — Maxi", "BC — Bodycon"
        ])
        largo = st.text_input("Largo total (cm)", placeholder="68")
    descripcion = st.text_area("Descripción libre (opcional)", placeholder="Hoodie oversize con gráfica lettering en espalda, dobladillo cortado a navaja, sin costuras laterales visibles...", height=80)

    st.markdown("---")

    # TEJIDO
    st.markdown("## 03 · TEJIDO Y COMPOSICIÓN")
    c1, c2, c3 = st.columns(3)
    with c1:
        tipo_tejido = st.selectbox("Tipo tejido", [
            "Felpa French Terry", "Felpa rizo", "Jersey punto liso",
            "Canalé / Rib", "Knitwear galga 7-12", "Knitwear galga 3-5",
            "Interlock", "Piqué", "Otro"
        ])
        gramaje = st.text_input("Gramaje (g/m²)", placeholder="320")
    with c2:
        composicion = st.text_input("Composición %", placeholder="80% CO / 20% PES")
        acabado = st.text_input("Acabado / Lavado", placeholder="Enzimático, Stone wash")
    with c3:
        color_principal = st.text_input("Color principal", placeholder="Off-Black")
        pantone = st.text_input("Pantone TCX", placeholder="19-0303 TCX")

    st.markdown("---")

    # GRÁFICA
    st.markdown("## 04 · GRÁFICA / ESTAMPADO (si aplica)")
    tiene_grafica = st.checkbox("Esta prenda lleva gráfica o estampado")
    if tiene_grafica:
        c1, c2, c3 = st.columns(3)
        with c1:
            tecnica_grafica = st.selectbox("Técnica", [
                "Serigrafía (SP)", "DTG Direct to Garment", "Bordado (EM)",
                "Puff 3D", "Foil metálico", "Flock terciopelo",
                "Discharge / Blanqueo", "Cracked ink", "Jacquard tejido"
            ])
        with c2:
            posicion_grafica = st.selectbox("Posición", [
                "Pecho izquierdo", "Pecho centro", "Pecho derecho",
                "Espalda superior", "Espalda completa", "Manga izquierda",
                "Manga derecha", "Bajo delantero", "Cuello interior"
            ])
        with c3:
            colores_grafica = st.text_input("Colores gráfica", placeholder="2 tintas: BLK + WHT")
        desc_grafica = st.text_area("Descripción gráfica", placeholder="Lettering 'OFFLINE' estilo naive, caja, serif gruesa, aprox 22cm ancho...", height=60)

    st.markdown("---")

    # MEDIDAS
    st.markdown("## 05 · TABLA DE MEDIDAS")
    st.markdown("<p style='color:#666;font-size:0.8rem;'>Talla base M. Las demás tallas escalan +/- 2cm por talla.</p>", unsafe_allow_html=True)

    medidas_nombres = ["Ancho pecho (1/2)", "Largo total centro delantero", "Ancho hombro", "Largo manga desde hombro", "Ancho bajo (1/2)", "Ancho puño (1/2)", "Alto cuello"]
    medidas_data = {}

    cols = st.columns(7)
    defaults = [57, 68, 47, 63, 55, 12, 8]
    for i, (nombre, default) in enumerate(zip(medidas_nombres, defaults)):
        with cols[i % 7]:
            medidas_data[nombre] = st.number_input(
                nombre.split("(")[0].strip()[:18],
                min_value=0, max_value=200, value=default,
                help=nombre
            )

    st.markdown("---")

    # CONSTRUCCIÓN
    st.markdown("## 06 · CONSTRUCCIÓN Y ACABADOS")
    c1, c2 = st.columns(2)
    with c1:
        costura_principal = st.selectbox("Costura principal", [
            "Overlock 4 hilos", "Overlock 5 hilos", "Flatlock",
            "Costura plana doble aguja", "Unión tejida (seamless)", "Remallado"
        ])
        costura_cuello = st.selectbox("Cuello / escote", [
            "Ribete canalé 1x1 (2cm)", "Ribete canalé 2x2 (2cm)",
            "Escote vuelto cosido", "Cuello capucha simple", "Sin acabado (cortado a navaja)"
        ])
    with c2:
        costura_bajo = st.selectbox("Bajo prenda", [
            "Dobladillo cosido 2cm", "Dobladillo cosido 3cm",
            "Cortado a navaja sin doblar", "Ribete canalé 5cm", "Puño elástico"
        ])
        costura_manga = st.selectbox("Bajo manga / puño", [
            "Dobladillo 2cm", "Puño canalé 1x1 7cm", "Puño canalé 2x2 7cm",
            "Cortado a navaja", "Sin manga"
        ])
    notas_construccion = st.text_area("Notas adicionales construcción", placeholder="Sin costuras laterales, pieza entera. Capucha: 2 piezas con cordón plano. Bolsillo canguro doble capa...", height=60)

    st.markdown("---")

    # TALLAS Y ETIQUETADO
    st.markdown("## 07 · TALLAS, ETIQUETA Y PACKAGING")
    c1, c2, c3 = st.columns(3)
    with c1:
        rango_tallas = st.multiselect("Rango de tallas", ["XXS", "XS", "S", "M", "L", "XL", "XXL", "3XL"], default=["XS", "S", "M", "L", "XL"])
        talla_base = st.selectbox("Talla base muestra", ["XS", "S", "M", "L"])
    with c2:
        etiqueta_composicion = st.text_input("Etiqueta composición", placeholder="80% Algodón 20% Poliéster")
        instrucciones_lavado = st.text_input("Instrucciones lavado", placeholder="30°C, no centrifugar, no secar en secadora")
    with c3:
        pais_origen = st.text_input("País de origen etiqueta", value="MADE IN BANGLADESH")
        packaging = st.text_input("Packaging / Embalaje", placeholder="Individual polybag + cartón plano, 12uds/caja")

    st.markdown("---")

    # NOTAS FINALES
    st.markdown("## 08 · NOTAS Y CONTROL DE CALIDAD")
    notas_qc = st.text_area(
        "Puntos de control de calidad",
        placeholder="• Verificar simetría capucha\n• Tensión hilo uniforme en gráfica\n• Pantone exacto: tolerancia delta E < 2\n• Sin hilos sueltos visibles\n• Comprobación medidas en 3 prendas por lote",
        height=100
    )
    notas_generales = st.text_area("Notas generales / observaciones", height=60, placeholder="Referencia cliente: ZX-001. Muestra aprobada el...")


# ── PREVIEW ───────────────────────────────────────────────────────────────────
with col_right:
    st.markdown("## RESUMEN")
    st.markdown(f"""
    <div class='preview-box'>
    <p style='color:#666;font-size:0.75rem;font-weight:700;letter-spacing:2px;'>REFERENCIA</p>
    <p style='color:#c8ff00;font-family:monospace;font-size:1.1rem;font-weight:700;'>{ref_id or '—'}</p>
    <hr style='border-color:#2c2c2c;margin:10px 0;'>
    <p style='color:#666;font-size:0.75rem;'>PRENDA</p>
    <p style='color:#e8e8e8;font-size:0.9rem;font-weight:600;'>{nombre_prenda or '—'}</p>
    <p style='color:#666;font-size:0.75rem;margin-top:8px;'>CLIENTE · TEMPORADA</p>
    <p style='color:#e8e8e8;font-size:0.9rem;'>{cliente} · {temporada}</p>
    <p style='color:#666;font-size:0.75rem;margin-top:8px;'>TEJIDO · GRAMAJE</p>
    <p style='color:#e8e8e8;font-size:0.9rem;'>{tipo_tejido} · {gramaje or '—'} g/m²</p>
    <p style='color:#666;font-size:0.75rem;margin-top:8px;'>COMPOSICIÓN</p>
    <p style='color:#e8e8e8;font-size:0.9rem;'>{composicion or '—'}</p>
    <p style='color:#666;font-size:0.75rem;margin-top:8px;'>COLOR · PANTONE</p>
    <p style='color:#e8e8e8;font-size:0.9rem;'>{color_principal or '—'} · {pantone or '—'}</p>
    <p style='color:#666;font-size:0.75rem;margin-top:8px;'>FIT</p>
    <p style='color:#e8e8e8;font-size:0.9rem;'>{fit.split("—")[0].strip()}</p>
    <p style='color:#666;font-size:0.75rem;margin-top:8px;'>TALLAS</p>
    <p style='color:#e8e8e8;font-size:0.9rem;'>{' / '.join(rango_tallas) if rango_tallas else '—'}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    generar = st.button("⚡ GENERAR TECHPACK PDF")

    if generar:
        if not nombre_prenda or not ref_id:
            st.error("Completa al menos la Referencia ZZ y el Nombre de prenda.")
        else:
            with st.spinner("Generando ficha técnica..."):

                # ── PDF GENERATION ────────────────────────────────────────────
                buffer = BytesIO()
                doc = SimpleDocTemplate(
                    buffer,
                    pagesize=A4,
                    rightMargin=15*mm, leftMargin=15*mm,
                    topMargin=15*mm, bottomMargin=15*mm
                )

                styles = getSampleStyleSheet()
                c_black = colors.HexColor('#0d0d0d')
                c_accent = colors.HexColor('#c8ff00')
                c_white = colors.white
                c_gray = colors.HexColor('#888888')
                c_light = colors.HexColor('#f5f5f5')
                c_border = colors.HexColor('#dddddd')

                def sty(name, **kw):
                    base = styles[name] if name in styles.getSampleStyleSheet() else styles['Normal']
                    return ParagraphStyle(name + str(id(kw)), parent=base, **kw)

                H1 = ParagraphStyle('H1', fontName='Helvetica-Bold', fontSize=18, textColor=c_black, spaceAfter=4)
                H2 = ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=10, textColor=c_white, spaceAfter=2)
                H3 = ParagraphStyle('H3', fontName='Helvetica-Bold', fontSize=9, textColor=c_black, spaceAfter=2)
                NORMAL = ParagraphStyle('NRM', fontName='Helvetica', fontSize=8, textColor=c_black, spaceAfter=2)
                SMALL = ParagraphStyle('SML', fontName='Helvetica', fontSize=7, textColor=c_gray)
                MONO = ParagraphStyle('MNO', fontName='Courier-Bold', fontSize=10, textColor=c_accent)

                story = []

                # HEADER BAR
                header_data = [[
                    Paragraph(f'<b>ZZ STUDIO</b><br/><font size="7" color="#888888">FICHA TÉCNICA DE PRODUCCIÓN</font>', H1),
                    Paragraph(f'<font color="#888888" size="7">REF</font><br/><b>{ref_id}</b>', MONO),
                    Paragraph(f'<font color="#888888" size="7">CLIENTE</font><br/><b>{cliente}</b>', H3),
                    Paragraph(f'<font color="#888888" size="7">TEMPORADA</font><br/><b>{temporada}</b>', H3),
                    Paragraph(f'<font color="#888888" size="7">FECHA</font><br/>{fecha_tp}', NORMAL),
                ]]
                header_table = Table(header_data, colWidths=[55*mm, 40*mm, 35*mm, 30*mm, 25*mm])
                header_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), c_black),
                    ('TEXTCOLOR', (0,0), (-1,-1), c_white),
                    ('PADDING', (0,0), (-1,-1), 8),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('ROWBACKGROUNDS', (0,0), (-1,-1), [c_black]),
                ]))
                story.append(header_table)
                story.append(Spacer(1, 4*mm))

                # SECTION helper
                def section_header(title):
                    t = Table([[Paragraph(f'<b>{title}</b>', H2)]], colWidths=[185*mm])
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,-1), c_black),
                        ('PADDING', (0,0), (-1,-1), 6),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                    ]))
                    return t

                def data_row(label, value, w1=45, w2=95):
                    return [Paragraph(f'<font color="#888888">{label}</font>', SMALL),
                            Paragraph(str(value) if value else '—', NORMAL)]

                # 01 DESCRIPCIÓN GENERAL
                story.append(section_header("01 · DESCRIPCIÓN GENERAL"))
                story.append(Spacer(1, 2*mm))

                desc_data = [
                    data_row("PRENDA", f"{categoria} — {nombre_prenda}"),
                    data_row("FIT / SILUETA", fit),
                    data_row("ESTILO ZZ", estilo_zz),
                    data_row("PERFIL", perfil),
                    data_row("LARGO TOTAL", f"{largo} cm" if largo else "—"),
                ]
                if descripcion:
                    desc_data.append(data_row("DESCRIPCIÓN", descripcion))

                dt = Table(desc_data, colWidths=[45*mm, 140*mm])
                dt.setStyle(TableStyle([
                    ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
                    ('FONTSIZE', (0,0), (-1,-1), 8),
                    ('BACKGROUND', (0,0), (0,-1), c_light),
                    ('GRID', (0,0), (-1,-1), 0.3, c_border),
                    ('PADDING', (0,0), (-1,-1), 5),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ]))
                story.append(dt)
                story.append(Spacer(1, 3*mm))

                # 02 TEJIDO
                story.append(section_header("02 · TEJIDO Y COMPOSICIÓN"))
                story.append(Spacer(1, 2*mm))

                tej_data = [
                    data_row("TIPO TEJIDO", tipo_tejido),
                    data_row("COMPOSICIÓN", composicion),
                    data_row("GRAMAJE", f"{gramaje} g/m²" if gramaje else "—"),
                    data_row("COLOR PRINCIPAL", color_principal),
                    data_row("PANTONE TCX", pantone),
                    data_row("ACABADO / LAVADO", acabado if acabado else "Sin acabado especial"),
                ]
                tej_t = Table(tej_data, colWidths=[45*mm, 140*mm])
                tej_t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (0,-1), c_light),
                    ('GRID', (0,0), (-1,-1), 0.3, c_border),
                    ('PADDING', (0,0), (-1,-1), 5),
                    ('FONTSIZE', (0,0), (-1,-1), 8),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ]))
                story.append(tej_t)
                story.append(Spacer(1, 3*mm))

                # 03 MEDIDAS
                story.append(section_header("03 · TABLA DE MEDIDAS (cm)"))
                story.append(Spacer(1, 2*mm))

                tallas_sel = rango_tallas if rango_tallas else ["XS", "S", "M", "L", "XL"]
                # Build size table with ±2cm gradation
                medidas_header = ['MEDIDA'] + tallas_sel + ['TOL.']
                base_idx = tallas_sel.index(talla_base) if talla_base in tallas_sel else 0

                size_rows = [medidas_header]
                for nombre_med, val_base in medidas_data.items():
                    row = [Paragraph(f'<font size="7">{nombre_med}</font>', SMALL)]
                    for i, t in enumerate(tallas_sel):
                        diff = (i - base_idx) * 2
                        row.append(Paragraph(f'<b>{val_base + diff}</b>', NORMAL))
                    row.append(Paragraph('<font color="#888888">±0.5</font>', SMALL))
                    size_rows.append(row)

                col_w = [60*mm] + [20*mm] * len(tallas_sel) + [14*mm]
                size_t = Table(size_rows, colWidths=col_w[:len(col_w)])
                size_t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), c_black),
                    ('TEXTCOLOR', (0,0), (-1,0), c_white),
                    ('BACKGROUND', (0,1), (0,-1), c_light),
                    ('GRID', (0,0), (-1,-1), 0.3, c_border),
                    ('PADDING', (0,0), (-1,-1), 5),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,-1), 8),
                    ('ALIGN', (1,0), (-1,-1), 'CENTER'),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [c_white, colors.HexColor('#fafafa')]),
                ]))
                story.append(size_t)
                story.append(Spacer(1, 3*mm))

                # 04 GRÁFICA (si aplica)
                if tiene_grafica:
                    story.append(section_header("04 · GRÁFICA / ESTAMPADO"))
                    story.append(Spacer(1, 2*mm))
                    graf_data = [
                        data_row("TÉCNICA", tecnica_grafica),
                        data_row("POSICIÓN", posicion_grafica),
                        data_row("COLORES", colores_grafica if colores_grafica else "—"),
                        data_row("DESCRIPCIÓN", desc_grafica if desc_grafica else "Ver boceto adjunto"),
                    ]
                    graf_t = Table(graf_data, colWidths=[45*mm, 140*mm])
                    graf_t.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (0,-1), c_light),
                        ('GRID', (0,0), (-1,-1), 0.3, c_border),
                        ('PADDING', (0,0), (-1,-1), 5),
                        ('FONTSIZE', (0,0), (-1,-1), 8),
                        ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ]))
                    story.append(graf_t)
                    story.append(Spacer(1, 3*mm))

                # 05 CONSTRUCCIÓN
                story.append(section_header("05 · CONSTRUCCIÓN Y ACABADOS"))
                story.append(Spacer(1, 2*mm))
                const_data = [
                    data_row("COSTURA PRINCIPAL", costura_principal),
                    data_row("CUELLO / ESCOTE", costura_cuello),
                    data_row("BAJO PRENDA", costura_bajo),
                    data_row("BAJO MANGA / PUÑO", costura_manga),
                ]
                if notas_construccion:
                    const_data.append(data_row("NOTAS", notas_construccion))
                const_t = Table(const_data, colWidths=[45*mm, 140*mm])
                const_t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (0,-1), c_light),
                    ('GRID', (0,0), (-1,-1), 0.3, c_border),
                    ('PADDING', (0,0), (-1,-1), 5),
                    ('FONTSIZE', (0,0), (-1,-1), 8),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ]))
                story.append(const_t)
                story.append(Spacer(1, 3*mm))

                # 06 ETIQUETADO Y PACKAGING
                story.append(section_header("06 · ETIQUETADO Y PACKAGING"))
                story.append(Spacer(1, 2*mm))
                label_data = [
                    data_row("TALLAS", ' / '.join(rango_tallas) if rango_tallas else "—"),
                    data_row("COMPOSICIÓN ETIQUETA", etiqueta_composicion),
                    data_row("INSTRUCCIONES LAVADO", instrucciones_lavado),
                    data_row("PAÍS DE ORIGEN", pais_origen),
                    data_row("PACKAGING", packaging),
                ]
                label_t = Table(label_data, colWidths=[45*mm, 140*mm])
                label_t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (0,-1), c_light),
                    ('GRID', (0,0), (-1,-1), 0.3, c_border),
                    ('PADDING', (0,0), (-1,-1), 5),
                    ('FONTSIZE', (0,0), (-1,-1), 8),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ]))
                story.append(label_t)
                story.append(Spacer(1, 3*mm))

                # 07 QC
                story.append(section_header("07 · CONTROL DE CALIDAD"))
                story.append(Spacer(1, 2*mm))
                qc_text = notas_qc if notas_qc else "• Verificar medidas en 3 prendas por lote\n• Comprobar color vs. Pantone (delta E < 2)\n• Sin hilos sueltos visibles\n• Costuras simétricas\n• Etiquetado correcto"
                qc_t = Table([[Paragraph(qc_text.replace('\n', '<br/>'), NORMAL)]], colWidths=[185*mm])
                qc_t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fafafa')),
                    ('GRID', (0,0), (-1,-1), 0.3, c_border),
                    ('PADDING', (0,0), (-1,-1), 8),
                ]))
                story.append(qc_t)

                if notas_generales:
                    story.append(Spacer(1, 3*mm))
                    story.append(section_header("08 · NOTAS GENERALES"))
                    story.append(Spacer(1, 2*mm))
                    ng_t = Table([[Paragraph(notas_generales, NORMAL)]], colWidths=[185*mm])
                    ng_t.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,-1), c_light),
                        ('GRID', (0,0), (-1,-1), 0.3, c_border),
                        ('PADDING', (0,0), (-1,-1), 8),
                    ]))
                    story.append(ng_t)

                # FOOTER
                story.append(Spacer(1, 5*mm))
                footer_data = [[
                    Paragraph(f'<font color="#888888" size="7">ZIG ZAG STUDIO · TECHPACK · {ref_id} · {temporada}</font>', SMALL),
                    Paragraph(f'<font color="#888888" size="7">Documento generado el {fecha_tp}</font>', ParagraphStyle('F2', parent=SMALL, alignment=TA_RIGHT))
                ]]
                ft = Table(footer_data, colWidths=[100*mm, 85*mm])
                ft.setStyle(TableStyle([
                    ('LINEABOVE', (0,0), (-1,-1), 0.5, c_border),
                    ('PADDING', (0,0), (-1,-1), 5),
                ]))
                story.append(ft)

                doc.build(story)
                buffer.seek(0)

            filename = f"{ref_id.replace('/', '-')}_{temporada}_{nombre_prenda.replace(' ', '_')}.pdf"
            st.success("✅ TechPack generado correctamente")
            st.download_button(
                label="⬇️  DESCARGAR TECHPACK PDF",
                data=buffer,
                file_name=filename,
                mime="application/pdf"
            )

            st.markdown(f"""
            <div style='background:#161616;border:1px solid #2c2c2c;border-radius:8px;padding:14px;margin-top:8px;'>
            <p style='color:#666;font-size:0.75rem;font-weight:700;letter-spacing:2px;'>FICHERO GENERADO</p>
            <p style='color:#c8ff00;font-family:monospace;font-size:0.85rem;'>{filename}</p>
            </div>
            """, unsafe_allow_html=True)

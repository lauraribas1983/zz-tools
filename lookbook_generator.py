"""
ZZ Studio — Lookbook Generator
Carpeta de renders → PDF lookbook profesional en segundos
Formato: A4 landscape · Portada + layouts 1/2/3/4 prendas · Índice
"""

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Spacer
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.utils import ImageReader
import io
import zipfile
import json
from datetime import datetime
from pathlib import Path
import math

st.set_page_config(
    page_title="ZZ · Lookbook Generator",
    page_icon="📖",
    layout="wide"
)

st.markdown("""
<style>
    .stButton > button { background: #FFD700; color: #000; font-weight: bold; border: none; padding: 0.6em 2em; }
    .stButton > button:hover { background: #FFC200; }
    .preview-card {
        background: #1a1a1a;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ─── PALETAS DE COLOR PARA EL LOOKBOOK ───────────────────────────────────
PALETAS = {
    "ZZ Negro Clásico": {
        "fondo": (10, 10, 10),
        "texto": (255, 255, 255),
        "acento": (255, 215, 0),
        "secundario": (180, 180, 180),
        "gris_suave": (30, 30, 30)
    },
    "Luxury Blanco": {
        "fondo": (252, 250, 247),
        "texto": (26, 26, 26),
        "acento": (180, 140, 80),
        "secundario": (100, 100, 100),
        "gris_suave": (235, 232, 228)
    },
    "Slate Moderno": {
        "fondo": (28, 35, 45),
        "texto": (230, 230, 230),
        "acento": (100, 160, 220),
        "secundario": (150, 160, 170),
        "gris_suave": (40, 50, 65)
    },
    "Beige Editorial": {
        "fondo": (245, 240, 230),
        "texto": (40, 35, 30),
        "acento": (160, 80, 50),
        "secundario": (120, 110, 100),
        "gris_suave": (220, 215, 205)
    },
}

def cargar_imagen_segura(fuente, max_size=(2000, 2000)):
    """Carga imagen desde BytesIO o path, normaliza a RGB"""
    if isinstance(fuente, (str, Path)):
        img = Image.open(fuente)
    else:
        fuente.seek(0)
        img = Image.open(fuente)

    if img.mode == 'RGBA':
        fondo = Image.new('RGB', img.size, (255, 255, 255))
        fondo.paste(img, mask=img.split()[3])
        img = fondo
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    img.thumbnail(max_size, Image.LANCZOS)
    return img

def imagen_con_fondo_cuadrado(img, size=800, padding_pct=0.08, bg_color=(255, 255, 255)):
    """Coloca imagen centrada en cuadrado con margen uniforme"""
    padding = int(size * padding_pct)
    area = size - 2 * padding

    img_copy = img.copy()
    img_copy.thumbnail((area, area), Image.LANCZOS)

    canvas = Image.new('RGB', (size, size), bg_color)
    x = (size - img_copy.width) // 2
    y = (size - img_copy.height) // 2
    canvas.paste(img_copy, (x, y))
    return canvas

def pil_a_bytes(img, formato='PNG', calidad=92):
    buf = io.BytesIO()
    if formato == 'JPEG':
        img.save(buf, format='JPEG', quality=calidad, optimize=True)
    else:
        img.save(buf, format='PNG', optimize=True)
    buf.seek(0)
    return buf

def generar_lookbook_pdf(
    imagenes_info,       # lista de dicts: {img, nombre, ref, descripcion, precio}
    config,              # dict con título, marca, temporada, etc.
    paleta               # dict de colores
):
    """Genera el PDF completo del lookbook"""

    buf = io.BytesIO()
    W_mm, H_mm = landscape(A4)  # 297 × 210 mm
    W = W_mm * mm
    H = H_mm * mm

    c = rl_canvas.Canvas(buf, pagesize=(W, H))

    col = paleta

    def color_rlab(rgb_tuple):
        return colors.Color(rgb_tuple[0]/255, rgb_tuple[1]/255, rgb_tuple[2]/255)

    # ════════════════════════════════════════════════════════
    # PÁGINA 1: PORTADA
    # ════════════════════════════════════════════════════════

    # Fondo completo
    c.setFillColor(color_rlab(col["fondo"]))
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Imagen de fondo (primera prenda, grande y con overlay)
    if imagenes_info:
        try:
            img_portada = imagenes_info[0]['img'].copy()
            # Agrandar para llenar mitad derecha
            img_portada = imagen_con_fondo_cuadrado(img_portada, 900,
                                                     padding_pct=0.05,
                                                     bg_color=col["fondo"])
            # Oscurecer ligeramente para que el texto sea legible
            if col["fondo"][0] < 100:  # tema oscuro
                img_portada = ImageEnhance.Brightness(img_portada).enhance(0.7)

            img_buf = pil_a_bytes(img_portada, 'JPEG', 88)
            img_reader = ImageReader(img_buf)
            # Colocar en mitad derecha
            c.drawImage(img_reader, W * 0.42, 0, width=W * 0.58, height=H,
                       preserveAspectRatio=False, anchor='c')
        except Exception:
            pass

    # Franja izquierda con texto
    c.setFillColor(color_rlab(col["fondo"]))
    c.rect(0, 0, W * 0.44, H, fill=1, stroke=0)

    # Línea vertical acento
    c.setStrokeColor(color_rlab(col["acento"]))
    c.setLineWidth(2.5)
    c.line(W * 0.42, H * 0.1, W * 0.42, H * 0.9)

    # Logo / Marca
    c.setFillColor(color_rlab(col["acento"]))
    c.setFont("Helvetica-Bold", 11)
    marca_upper = config.get('marca', 'ZZ STUDIO').upper()
    c.drawString(40, H - 55, marca_upper)

    # Separador
    c.setStrokeColor(color_rlab(col["acento"]))
    c.setLineWidth(1)
    c.line(40, H - 65, 40 + len(marca_upper) * 6.5, H - 65)

    # Título colección
    titulo = config.get('titulo', 'COLLECTION')
    c.setFillColor(color_rlab(col["texto"]))
    c.setFont("Helvetica-Bold", 38)

    # Ajustar si es largo
    while len(titulo) > 14 and c.stringWidth(titulo, "Helvetica-Bold", 38) > W * 0.38:
        titulo_parts = titulo.split()
        if len(titulo_parts) > 1:
            titulo = titulo  # dejamos como está para el wrap manual
            break

    # Wrapping manual para titulo
    palabras = titulo.split()
    lineas_titulo = []
    linea_actual = ""
    for p in palabras:
        prueba = linea_actual + " " + p if linea_actual else p
        if c.stringWidth(prueba, "Helvetica-Bold", 38) < W * 0.35:
            linea_actual = prueba
        else:
            if linea_actual:
                lineas_titulo.append(linea_actual)
            linea_actual = p
    if linea_actual:
        lineas_titulo.append(linea_actual)

    y_titulo = H * 0.55
    for linea in lineas_titulo[:3]:
        c.drawString(40, y_titulo, linea.upper())
        y_titulo -= 48

    # Temporada
    c.setFont("Helvetica", 14)
    c.setFillColor(color_rlab(col["acento"]))
    c.drawString(40, y_titulo - 10, config.get('temporada', 'SS26'))

    # Descripción
    if config.get('subtitulo'):
        c.setFont("Helvetica", 10)
        c.setFillColor(color_rlab(col["secundario"]))
        c.drawString(40, y_titulo - 35, config['subtitulo'][:80])

    # Número de looks
    total = len(imagenes_info)
    c.setFont("Helvetica", 9)
    c.setFillColor(color_rlab(col["secundario"]))
    c.drawString(40, 50, f"{total} LOOKS · {config.get('cliente', '')} · CONFIDENTIAL")

    # Línea inferior
    c.setStrokeColor(color_rlab(col["acento"]))
    c.setLineWidth(0.5)
    c.line(40, 42, W * 0.40, 42)

    c.showPage()

    # ════════════════════════════════════════════════════════
    # PÁGINAS DE PRODUCTOS
    # ════════════════════════════════════════════════════════

    margen = 18 * mm
    layout_tipo = config.get('layout', '2x2')

    layout_configs = {
        '1x1': {'cols': 1, 'rows': 1},
        '1x2': {'cols': 2, 'rows': 1},
        '2x2': {'cols': 2, 'rows': 2},
        '3x1': {'cols': 3, 'rows': 1},
        '2x3': {'cols': 3, 'rows': 2},
    }

    lc = layout_configs.get(layout_tipo, {'cols': 2, 'rows': 2})
    cols_n = lc['cols']
    rows_n = lc['rows']
    por_pagina = cols_n * rows_n

    area_w = W - 2 * margen
    area_h = H - 2 * margen

    header_h = 22 * mm
    footer_h = 12 * mm

    celda_w = area_w / cols_n
    celda_h = (area_h - header_h - footer_h) / rows_n

    info_h = 20 * mm  # espacio para ref/nombre debajo de la imagen

    pagina_num = 2

    for page_start in range(0, len(imagenes_info), por_pagina):
        batch = imagenes_info[page_start:page_start + por_pagina]

        # Fondo
        c.setFillColor(color_rlab(col["fondo"]))
        c.rect(0, 0, W, H, fill=1, stroke=0)

        # Header
        c.setFillColor(color_rlab(col["gris_suave"]))
        c.rect(0, H - header_h - margen, W, header_h + margen, fill=1, stroke=0)

        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(color_rlab(col["acento"]))
        c.drawString(margen, H - margen - 10, config.get('marca', 'ZZ STUDIO').upper())

        c.setFont("Helvetica", 9)
        c.setFillColor(color_rlab(col["secundario"]))
        titulo_corto = config.get('titulo', '')[:40]
        c.drawCentredString(W / 2, H - margen - 10, f"{titulo_corto} · {config.get('temporada', 'SS26')}")

        c.drawRightString(W - margen, H - margen - 10, f"— {pagina_num} —")

        # Línea separador header
        c.setStrokeColor(color_rlab(col["acento"]))
        c.setLineWidth(0.5)
        c.line(margen, H - margen - 14, W - margen, H - margen - 14)

        y_start = H - margen - header_h

        for idx, item in enumerate(batch):
            col_idx = idx % cols_n
            row_idx = idx // cols_n

            x = margen + col_idx * celda_w
            y = y_start - (row_idx + 1) * celda_h

            img_area_h = celda_h - info_h
            img_area_w = celda_w - 8 * mm

            padding_img = 4 * mm

            try:
                img = item['img']
                img_sq = imagen_con_fondo_cuadrado(
                    img,
                    size=600,
                    padding_pct=0.06,
                    bg_color=(255, 255, 255)
                )
                img_sq.thumbnail((int(img_area_w - padding_img * 2),
                                   int(img_area_h - padding_img * 2)),
                                  Image.LANCZOS)

                img_buf = pil_a_bytes(img_sq, 'JPEG', 88)
                img_reader = ImageReader(img_buf)

                img_x = x + padding_img + (img_area_w - img_sq.width) / 2
                img_y = y + info_h + (img_area_h - img_sq.height) / 2

                c.drawImage(img_reader, img_x, img_y,
                           width=img_sq.width, height=img_sq.height,
                           preserveAspectRatio=True)

            except Exception:
                pass

            # Info producto
            info_y = y + info_h - 5
            nombre = item.get('nombre', '')[:28]
            ref = item.get('ref', '')

            c.setFont("Helvetica-Bold", 8)
            c.setFillColor(color_rlab(col["texto"]))
            c.drawString(x + padding_img, info_y, nombre.upper())

            c.setFont("Helvetica", 7)
            c.setFillColor(color_rlab(col["secundario"]))
            c.drawString(x + padding_img, info_y - 11, ref)

            if item.get('descripcion'):
                c.setFont("Helvetica", 6.5)
                c.setFillColor(color_rlab(col["secundario"]))
                c.drawString(x + padding_img, info_y - 21, item['descripcion'][:45])

            # Divisor entre celdas (sutil)
            if col_idx < cols_n - 1:
                c.setStrokeColor(color_rlab(col["gris_suave"]))
                c.setLineWidth(0.3)
                c.line(x + celda_w - 2 * mm, y + footer_h, x + celda_w - 2 * mm, y + celda_h - 2 * mm)

        # Footer
        c.setFillColor(color_rlab(col["gris_suave"]))
        c.rect(0, 0, W, footer_h + margen * 0.5, fill=1, stroke=0)

        c.setFont("Helvetica", 7)
        c.setFillColor(color_rlab(col["secundario"]))
        fecha = datetime.now().strftime('%Y · %m · %d')
        c.drawString(margen, margen * 0.4, f"{config.get('marca','ZZ STUDIO')} · CONFIDENTIAL · {fecha}")
        c.drawRightString(W - margen, margen * 0.4, f"PÁGINA {pagina_num}")

        c.showPage()
        pagina_num += 1

    # ════════════════════════════════════════════════════════
    # ÚLTIMA PÁGINA: ÍNDICE / THUMBNAILS
    # ════════════════════════════════════════════════════════

    if config.get('incluir_indice', True) and len(imagenes_info) > 0:

        c.setFillColor(color_rlab(col["fondo"]))
        c.rect(0, 0, W, H, fill=1, stroke=0)

        # Título índice
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(color_rlab(col["texto"]))
        c.drawString(margen, H - margen - 15, "ÍNDICE DE COLECCIÓN")

        c.setStrokeColor(color_rlab(col["acento"]))
        c.setLineWidth(1.5)
        c.line(margen, H - margen - 22, margen + 80 * mm, H - margen - 22)

        # Grid de thumbnails
        thumb_size = 55 * mm
        cols_idx = min(5, len(imagenes_info))
        rows_idx = math.ceil(len(imagenes_info) / cols_idx)

        thumb_w = (W - 2 * margen) / cols_idx
        y_inicio_grid = H - margen - 35 * mm

        for idx, item in enumerate(imagenes_info):
            col_idx = idx % cols_idx
            row_idx = idx // cols_idx

            x = margen + col_idx * thumb_w
            y = y_inicio_grid - row_idx * (thumb_size + 18 * mm)

            if y < margen + 15 * mm:
                break

            try:
                img_th = item['img'].copy()
                img_th = imagen_con_fondo_cuadrado(img_th, 200, 0.05, (255, 255, 255))
                img_th.thumbnail((int(thumb_size - 4 * mm), int(thumb_size - 4 * mm)), Image.LANCZOS)

                img_buf = pil_a_bytes(img_th, 'JPEG', 80)
                img_reader = ImageReader(img_buf)

                ix = x + (thumb_w - img_th.width) / 2
                c.drawImage(img_reader, ix, y,
                           width=img_th.width, height=img_th.height)

                c.setFont("Helvetica-Bold", 6)
                c.setFillColor(color_rlab(col["texto"]))
                nombre_short = item.get('nombre', f'Prenda {idx+1}')[:18]
                c.drawCentredString(x + thumb_w / 2, y - 9, nombre_short.upper())

                c.setFont("Helvetica", 6)
                c.setFillColor(color_rlab(col["secundario"]))
                c.drawCentredString(x + thumb_w / 2, y - 18, item.get('ref', '')[:15])

            except Exception:
                pass

        # Footer
        c.setFillColor(color_rlab(col["gris_suave"]))
        c.rect(0, 0, W, footer_h + margen * 0.5, fill=1, stroke=0)
        c.setFont("Helvetica", 7)
        c.setFillColor(color_rlab(col["secundario"]))
        c.drawString(margen, margen * 0.4,
                    f"{config.get('marca', 'ZZ STUDIO')} · CONFIDENTIAL · {datetime.now().strftime('%Y')}")
        c.drawRightString(W - margen, margen * 0.4, "FIN DE CATÁLOGO")

        c.showPage()

    c.save()
    buf.seek(0)
    return buf

# ─── UI ───────────────────────────────────────────────────────────────────

st.title("📖 ZZ · Lookbook Generator")
st.caption("Renders → PDF lookbook profesional · Portada + layouts + índice · Listo para cliente en segundos")

col_izq, col_der = st.columns([1, 1.2], gap="large")

with col_izq:
    st.subheader("📁 Imágenes")

    archivos = st.file_uploader(
        "Sube los renders de la colección",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="Sube todos los renders. Puedes reordenarlos editando los datos."
    )

    if archivos:
        st.success(f"✅ {len(archivos)} imagen(es) cargadas")

        # Tabla de metadatos editable
        st.subheader("📋 Datos de producto")
        st.caption("Edita nombres y referencias para el lookbook")

        imagenes_data = []
        for i, archivo in enumerate(archivos):
            with st.expander(f"✏️ {archivo.name}", expanded=(i == 0)):
                col_a, col_b = st.columns(2)
                with col_a:
                    nombre = st.text_input("Nombre prenda", f"Look {i+1:02d}", key=f"nom_{i}")
                    ref = st.text_input("Ref / SKU", f"REF-{(i+1):03d}", key=f"ref_{i}")
                with col_b:
                    desc = st.text_input("Descripción breve", "", key=f"desc_{i}",
                                        placeholder="ej: Jersey oversized ribbed navy")
                    precio = st.text_input("Precio / Info extra", "", key=f"prec_{i}",
                                           placeholder="ej: €29.99")

                imagenes_data.append({
                    "archivo": archivo,
                    "nombre": nombre,
                    "ref": ref,
                    "descripcion": desc,
                    "precio": precio
                })

with col_der:
    st.subheader("🎨 Diseño del lookbook")

    # ── Datos de portada ──
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        titulo = st.text_input("Título colección", "SUMMER ESSENTIALS", placeholder="ej: SUMMER ESSENTIALS 2026")
        marca = st.text_input("Marca / Studio", "ZZ STUDIO")
    with col_c2:
        temporada = st.selectbox("Temporada", ["SS26", "AW26", "SS27", "AW27", "Evergreen"])
        cliente = st.text_input("Para (cliente)", "ZARA", placeholder="ej: ZARA / PULL&BEAR")

    subtitulo = st.text_input("Subtítulo / tagline", "",
                              placeholder="ej: Core Collection · Knitwear & Jersey")

    st.divider()

    # ── Diseño visual ──
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        paleta_nombre = st.selectbox("Paleta de color", list(PALETAS.keys()))
        layout_tipo = st.selectbox("Layout páginas", {
            "2x2 (4 prendas/página)": "2x2",
            "1x2 (2 prendas/página)": "1x2",
            "3x1 (3 prendas/fila)": "3x1",
            "1x1 (1 prenda/página)": "1x1",
            "2x3 (6 prendas/página)": "2x3",
        }.keys())
        layout_map = {
            "2x2 (4 prendas/página)": "2x2",
            "1x2 (2 prendas/página)": "1x2",
            "3x1 (3 prendas/fila)": "3x1",
            "1x1 (1 prenda/página)": "1x1",
            "2x3 (6 prendas/página)": "2x3",
        }
        layout_sel = layout_map[layout_tipo]

    with col_d2:
        incluir_indice = st.checkbox("Incluir página índice/thumbnails", value=True)
        mostrar_refs = st.checkbox("Mostrar referencias en ficha", value=True)
        st.caption("Formato: A4 landscape · 297×210mm")

    # ── Preview paleta ──
    paleta_sel = PALETAS[paleta_nombre]
    cols_prev = st.columns(5)
    pal_labels = ["Fondo", "Texto", "Acento", "Secundario", "Gris suave"]
    pal_keys = ["fondo", "texto", "acento", "secundario", "gris_suave"]
    for i, (label, key) in enumerate(zip(pal_labels, pal_keys)):
        rgb = paleta_sel[key]
        hex_c = '#{:02x}{:02x}{:02x}'.format(*rgb)
        with cols_prev[i]:
            st.markdown(
                f'<div style="background:{hex_c};height:30px;border-radius:4px;'
                f'border:1px solid #444;"></div>'
                f'<p style="font-size:10px;text-align:center;margin-top:3px;color:#aaa;">{label}</p>',
                unsafe_allow_html=True
            )

# ── BOTÓN GENERAR ──────────────────────────────────────────────────────────
st.divider()

if st.button("🚀 GENERAR LOOKBOOK PDF", use_container_width=True):

    if not archivos:
        st.error("⚠️ Sube al menos una imagen")
    else:
        progreso = st.progress(0)
        estado = st.empty()

        estado.info("Cargando imágenes...")

        # Preparar datos
        imagenes_info = []
        for i, item_data in enumerate(imagenes_data if 'imagenes_data' in dir() else []):
            progreso.progress((i + 1) / (len(archivos) * 2))
            try:
                img = cargar_imagen_segura(item_data["archivo"])
                imagenes_info.append({
                    "img": img,
                    "nombre": item_data["nombre"],
                    "ref": item_data["ref"],
                    "descripcion": item_data["descripcion"],
                    "precio": item_data["precio"]
                })
            except Exception as e:
                st.warning(f"Error con {item_data['archivo'].name}: {e}")

        if not imagenes_info:
            # Fallback si imagenes_data no está definido en este contexto
            for i, archivo in enumerate(archivos):
                try:
                    img = cargar_imagen_segura(archivo)
                    imagenes_info.append({
                        "img": img,
                        "nombre": f"Look {i+1:02d}",
                        "ref": f"REF-{i+1:03d}",
                        "descripcion": "",
                        "precio": ""
                    })
                except:
                    pass

        estado.info(f"Generando PDF con {len(imagenes_info)} productos...")
        progreso.progress(0.6)

        config_lb = {
            "titulo": titulo,
            "marca": marca,
            "temporada": temporada,
            "cliente": cliente,
            "subtitulo": subtitulo,
            "layout": layout_sel,
            "incluir_indice": incluir_indice,
        }

        try:
            pdf_buf = generar_lookbook_pdf(imagenes_info, config_lb, paleta_sel)

            progreso.progress(1.0)
            estado.success(f"✅ Lookbook generado — {len(imagenes_info)} productos · {math.ceil(len(imagenes_info) / {'2x2':4,'1x2':2,'3x1':3,'1x1':1,'2x3':6}[layout_sel]) + 2} páginas")

            nombre_pdf = f"ZZ_LOOKBOOK_{titulo.replace(' ', '_')[:20]}_{temporada}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

            st.download_button(
                label=f"⬇️ DESCARGAR LOOKBOOK PDF",
                data=pdf_buf.getvalue(),
                file_name=nombre_pdf,
                mime="application/pdf",
                use_container_width=True
            )

        except Exception as e:
            estado.error(f"Error generando PDF: {e}")
            import traceback
            st.code(traceback.format_exc())

# ── GUÍA ──────────────────────────────────────────────────────────────────
with st.expander("💡 Flujo de trabajo"):
    st.markdown("""
    **Cómo usarlo en 60 segundos:**

    1. Sube todos los renders de la colección (PNG/JPG, fondo blanco ideal)
    2. Edita nombres y referencias si los necesitas
    3. Pon el título de colección, temporada y cliente
    4. Elige paleta (ZZ Negro para presentaciones internas, Luxury Blanco para cliente premium)
    5. Clic en GENERAR → descarga el PDF

    **Layouts recomendados:**
    - 2x2 → colecciones amplias, visión general
    - 1x2 → colecciones seleccionadas, más detalle
    - 1x1 → productos hero, presentaciones ejecutivas

    **Consejos:**
    - Los fondos blancos quedan mejor que los transparentes
    - Pasa antes por Image Processor para normalizar tamaños y fondos
    - El índice/thumbnails al final facilita la navegación al cliente
    """)

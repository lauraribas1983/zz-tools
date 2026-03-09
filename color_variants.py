"""
ZZ Studio — Color Variants Generator
Genera variantes de color de renders/fichas de producto
Modo: rebranding, cambio de colorways, colecciones cápsula
"""

import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import io
import zipfile
import json
from datetime import datetime

st.set_page_config(
    page_title="ZZ · Variantes de Color",
    page_icon="🎨",
    layout="wide"
)

# ─── PALETAS PREDEFINIDAS ZZ ───────────────────────────────────────────────
PALETAS_ZZ = {
    "Neutros Luxury": [
        {"nombre": "Ecru", "hex": "#F5F0E8"},
        {"nombre": "Marfil", "hex": "#FFFFF0"},
        {"nombre": "Camel", "hex": "#C19A6B"},
        {"nombre": "Topo", "hex": "#8B7355"},
        {"nombre": "Grafito", "hex": "#4A4A4A"},
        {"nombre": "Negro", "hex": "#1A1A1A"},
    ],
    "SS26 Tendencia": [
        {"nombre": "Butter Yellow", "hex": "#F5D76E"},
        {"nombre": "Sage Green", "hex": "#8FAF8F"},
        {"nombre": "Dusty Rose", "hex": "#D4A5A5"},
        {"nombre": "Powder Blue", "hex": "#B0C4DE"},
        {"nombre": "Rust", "hex": "#B7410E"},
        {"nombre": "Terracota", "hex": "#CC6644"},
    ],
    "AW26 Tendencia": [
        {"nombre": "Burgundy", "hex": "#800020"},
        {"nombre": "Forest Green", "hex": "#2D5016"},
        {"nombre": "Slate Blue", "hex": "#5B7EA6"},
        {"nombre": "Chocolate", "hex": "#5C3317"},
        {"nombre": "Midnight", "hex": "#191970"},
        {"nombre": "Oatmeal", "hex": "#D4C5A9"},
    ],
    "Básicos Inditex": [
        {"nombre": "Blanco", "hex": "#FFFFFF"},
        {"nombre": "Negro", "hex": "#1A1A1A"},
        {"nombre": "Gris Claro", "hex": "#D3D3D3"},
        {"nombre": "Gris Medio", "hex": "#808080"},
        {"nombre": "Navy", "hex": "#1B2A4A"},
        {"nombre": "Azul Medio", "hex": "#4169A0"},
    ]
}

# ─── FUNCIONES ─────────────────────────────────────────────────────────────

def hex_to_rgb(hex_color):
    """Convierte hex a RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    """Convierte RGB tuple a hex"""
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def detectar_color_dominante(img_array, mask=None):
    """Detecta el color más dominante de la prenda (excluyendo fondo)"""
    if mask is not None:
        pixels = img_array[mask]
    else:
        pixels = img_array.reshape(-1, 3)

    # Excluir blancos y muy claros (fondo)
    no_fondo = pixels[np.mean(pixels, axis=1) < 240]
    if len(no_fondo) == 0:
        no_fondo = pixels

    # Promedio ponderado
    color_medio = np.mean(no_fondo, axis=0)
    return color_medio

def reemplazar_color(imagen_pil, color_origen_hex, color_destino_hex, tolerancia=45, suavizado=True):
    """
    Reemplaza un color específico en la imagen manteniendo texturas y sombras
    Preserva las variaciones de luz/sombra del original
    """
    # Convertir a RGBA para preservar transparencia
    if imagen_pil.mode != 'RGBA':
        img = imagen_pil.convert('RGBA')
    else:
        img = imagen_pil.copy()

    img_array = np.array(img, dtype=np.float32)
    rgb = img_array[:, :, :3]
    alpha = img_array[:, :, 3]

    origen = np.array(hex_to_rgb(color_origen_hex), dtype=np.float32)
    destino = np.array(hex_to_rgb(color_destino_hex), dtype=np.float32)

    # Calcular distancia de cada pixel al color origen
    diff = rgb - origen
    distancia = np.sqrt(np.sum(diff**2, axis=2))

    # Máscara de pixels a reemplazar
    mascara = (distancia < tolerancia) & (alpha > 10)

    if not np.any(mascara):
        return imagen_pil, 0  # No se encontró el color

    # Para cada pixel en la máscara, preservar la luminosidad relativa
    # (esto mantiene sombras, pliegues, texturas)
    resultado = rgb.copy()

    # Luminosidad del pixel original vs color origen
    lum_origen = np.mean(origen)

    for i in range(3):
        # Factor de variación respecto al color origen
        factor = (rgb[:, :, i] - origen[i]) / max(lum_origen, 1)
        # Aplicar la misma variación al color destino
        nuevo_valor = destino[i] + (factor * lum_origen * 0.8)
        nuevo_valor = np.clip(nuevo_valor, 0, 255)

        resultado[:, :, i] = np.where(mascara, nuevo_valor, rgb[:, :, i])

    # Reconstruir imagen con alpha
    resultado_con_alpha = np.dstack([resultado, alpha])
    img_resultado = Image.fromarray(resultado_con_alpha.astype(np.uint8), 'RGBA')

    # Opcional: suavizar bordes de la máscara
    if suavizado:
        img_resultado = img_resultado.filter(ImageFilter.SMOOTH_MORE)

    pixeles_cambiados = np.sum(mascara)
    return img_resultado, pixeles_cambiados

def cambio_tono_global(imagen_pil, tono_hex, intensidad=0.75):
    """
    Método alternativo: cambia el tono global de toda la prenda
    Útil para renders de un solo color donde el método de reemplazo puede fallar
    """
    if imagen_pil.mode != 'RGBA':
        img = imagen_pil.convert('RGBA')
    else:
        img = imagen_pil.copy()

    img_array = np.array(img, dtype=np.float32)
    rgb = img_array[:, :, :3]
    alpha = img_array[:, :, 3]

    destino = np.array(hex_to_rgb(tono_hex), dtype=np.float32)

    # Máscara: solo pixels no-transparentes y no-blancos (fondo)
    mascara_prenda = (alpha > 10) & (np.mean(rgb, axis=2) < 245)

    resultado = rgb.copy()

    # Calcular luminosidad relativa de cada pixel
    lum_pixel = np.mean(rgb, axis=2, keepdims=True) / 128.0

    for i in range(3):
        nuevo_valor = destino[i] * lum_pixel[:, :, 0] * intensidad + rgb[:, :, i] * (1 - intensidad)
        nuevo_valor = np.clip(nuevo_valor, 0, 255)
        resultado[:, :, i] = np.where(mascara_prenda, nuevo_valor, rgb[:, :, i])

    resultado_con_alpha = np.dstack([resultado, alpha])
    return Image.fromarray(resultado_con_alpha.astype(np.uint8), 'RGBA')

def pegar_sobre_blanco(imagen_rgba):
    """Pega imagen RGBA sobre fondo blanco para export JPG"""
    fondo = Image.new('RGB', imagen_rgba.size, (255, 255, 255))
    if imagen_rgba.mode == 'RGBA':
        fondo.paste(imagen_rgba, mask=imagen_rgba.split()[3])
    else:
        fondo.paste(imagen_rgba)
    return fondo

def generar_swatch(color_hex, tamaño=60):
    """Genera un cuadrado de color para preview"""
    swatch = Image.new('RGB', (tamaño, tamaño), hex_to_rgb(color_hex))
    return swatch

# ─── UI PRINCIPAL ──────────────────────────────────────────────────────────

st.markdown("""
<style>
    .main { background: #0d0d0d; }
    .block-container { max-width: 1100px; }
    .swatch-box {
        display: inline-block;
        width: 40px; height: 40px;
        border-radius: 4px;
        border: 1px solid #444;
        margin-right: 8px;
        vertical-align: middle;
    }
    h1, h2, h3 { color: #f5f5f5; }
    .stButton > button {
        background: #FFD700;
        color: #000;
        font-weight: bold;
        border: none;
        padding: 0.5em 2em;
    }
    .stButton > button:hover { background: #FFC200; }
</style>
""", unsafe_allow_html=True)

st.title("🎨 ZZ · Generador de Variantes de Color")
st.caption("Crea colorways de producto • Rebranding • Colecciones cápsula")

# ── COLUMNAS PRINCIPALES ──
col_izq, col_der = st.columns([1, 1], gap="large")

with col_izq:
    st.subheader("📁 Imagen de Producto")

    archivos = st.file_uploader(
        "Sube renders (PNG con transparencia recomendado)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="Funciona mejor con renders PNG. Para fotos usa PNG con fondo transparente."
    )

    if archivos:
        # Mostrar preview de la primera imagen
        img_preview = Image.open(archivos[0])
        st.image(img_preview, caption=archivos[0].name, use_container_width=True)

        st.markdown(f"**{len(archivos)} imagen(es) cargadas**")

    st.divider()

    # ── DATOS DEL ARTÍCULO ──
    st.subheader("📋 Datos del Artículo")

    col_a, col_b = st.columns(2)
    with col_a:
        ref_base = st.text_input("Referencia base", "HOO-001", placeholder="HOO-001")
        temporada = st.selectbox("Temporada", ["SS26", "AW26", "SS27", "AW27"])
    with col_b:
        categoria = st.selectbox("Categoría", [
            "HOO", "SWT", "TEE", "DRS", "JGR", "LEG", "CRD", "BOD", "CRD", "CAP"
        ])
        cliente = st.selectbox("Cliente", ["Zara", "Pull&Bear", "Bershka", "ZZ Internal", "Otro"])

with col_der:
    st.subheader("🎨 Selección de Colores")

    # ── MÉTODO ──
    metodo = st.radio(
        "Método de colorización",
        ["🎯 Reemplazar color específico", "🌈 Cambio de tono global"],
        help="Reemplazar: para colores planos específicos. Tono global: para prendas de un solo color.",
        horizontal=True
    )

    if "Reemplazar" in metodo:
        color_origen = st.color_picker(
            "🎯 Color a reemplazar (pícalo del render)",
            "#1A1A1A",
            help="Selecciona el color principal de la prenda que quieres cambiar"
        )

        tolerancia = st.slider(
            "Tolerancia (qué tan similar debe ser el color)",
            10, 80, 45,
            help="Mayor tolerancia = reemplaza más tonos similares. Menor = más exacto."
        )
    else:
        intensidad = st.slider(
            "Intensidad del cambio de tono",
            0.3, 1.0, 0.75,
            help="0.3 = tinte sutil, 1.0 = colorización completa"
        )

    st.divider()

    # ── PALETA DE COLORES DESTINO ──
    st.subheader("Colores destino (colorways)")

    paleta_nombre = st.selectbox(
        "Paleta predefinida ZZ",
        ["Personalizada"] + list(PALETAS_ZZ.keys())
    )

    if paleta_nombre != "Personalizada":
        st.markdown("**Preview paleta:**")
        paleta_seleccionada = PALETAS_ZZ[paleta_nombre]
        cols_pal = st.columns(len(paleta_seleccionada))
        for i, color in enumerate(paleta_seleccionada):
            with cols_pal[i]:
                st.markdown(
                    f'<div style="background:{color["hex"]};width:40px;height:40px;'
                    f'border-radius:4px;border:1px solid #555;margin:auto;"></div>'
                    f'<p style="font-size:10px;text-align:center;margin-top:4px;">{color["nombre"]}</p>',
                    unsafe_allow_html=True
                )

        colores_finales = paleta_seleccionada
        usar_todos = st.checkbox("Usar todos los colores de la paleta", value=True)

        if not usar_todos:
            nombres_selec = st.multiselect(
                "Selecciona colores específicos",
                [c["nombre"] for c in paleta_seleccionada],
                default=[c["nombre"] for c in paleta_seleccionada]
            )
            colores_finales = [c for c in paleta_seleccionada if c["nombre"] in nombres_selec]

    else:
        # Colores personalizados
        num_colores = st.number_input("Número de variantes", 1, 12, 4)
        colores_finales = []

        st.markdown("**Define tus colorways:**")
        cols_custom = st.columns(min(num_colores, 4))
        for i in range(num_colores):
            col_idx = i % 4
            with cols_custom[col_idx]:
                nombre = st.text_input(f"Nombre {i+1}", f"Color {i+1}", key=f"nom_{i}")
                hex_val = st.color_picker(f"Color {i+1}", "#808080", key=f"col_{i}")
                colores_finales.append({"nombre": nombre, "hex": hex_val})

    st.divider()

    # ── OPCIONES EXPORT ──
    st.subheader("📦 Export")

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        formato_export = st.selectbox("Formato", ["JPG (blanco)", "PNG (transparente)"])
        calidad_jpg = st.slider("Calidad", 70, 100, 90) if "JPG" in formato_export else 100
    with col_e2:
        incluir_swatch = st.checkbox("Incluir hoja de swatches", value=True)
        tamaño_export = st.selectbox("Tamaño", ["Original", "Web (1200px)", "Catálogo (2400px)", "Techpack (800px)"])

# ── BOTÓN GENERAR ──────────────────────────────────────────────────────────
st.divider()

if st.button("🚀 GENERAR TODAS LAS VARIANTES", use_container_width=True):

    if not archivos:
        st.error("⚠️ Primero sube al menos una imagen")
    elif not colores_finales:
        st.error("⚠️ Selecciona al menos un color destino")
    else:

        progreso = st.progress(0)
        estado = st.empty()

        zip_buffer = io.BytesIO()
        total_generadas = 0
        errores = []

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:

            # ── Hoja de swatches ──
            if incluir_swatch:
                estado.info("Generando hoja de swatches...")
                ancho_swatch = 120
                alto_swatch = 150
                padding = 20

                total_swatches = len(colores_finales)
                cols_sw = min(total_swatches, 6)
                rows_sw = (total_swatches + cols_sw - 1) // cols_sw

                ancho_total = cols_sw * (ancho_swatch + padding) + padding
                alto_total = rows_sw * (alto_swatch + padding) + padding + 60

                hoja = Image.new('RGB', (ancho_total, alto_total), (250, 250, 250))

                try:
                    from PIL import ImageDraw, ImageFont
                    draw = ImageDraw.Draw(hoja)

                    # Título
                    draw.rectangle([0, 0, ancho_total, 50], fill=(26, 26, 26))
                    draw.text((20, 15), f"ZZ Studio · {ref_base} · {temporada} · Colorways",
                             fill=(255, 215, 0))

                    for idx, color in enumerate(colores_finales):
                        col_pos = idx % cols_sw
                        row_pos = idx // cols_sw

                        x = padding + col_pos * (ancho_swatch + padding)
                        y = 60 + padding + row_pos * (alto_swatch + padding)

                        rgb = hex_to_rgb(color["hex"])
                        draw.rectangle([x, y, x + ancho_swatch, y + ancho_swatch], fill=rgb)
                        draw.rectangle([x-1, y-1, x + ancho_swatch+1, y + ancho_swatch+1],
                                      outline=(180, 180, 180), width=1)
                        draw.text((x, y + ancho_swatch + 5), color["nombre"][:15], fill=(50, 50, 50))
                        draw.text((x, y + ancho_swatch + 20), color["hex"].upper(), fill=(120, 120, 120))

                    swatch_buffer = io.BytesIO()
                    hoja.save(swatch_buffer, format='PNG')
                    zf.writestr(f"SWATCHES_{ref_base}_{temporada}.png", swatch_buffer.getvalue())

                except Exception as e:
                    pass  # Continuar sin swatch si hay error de fuente

            # ── Procesar cada imagen ──
            total_ops = len(archivos) * len(colores_finales)
            op_actual = 0

            for archivo in archivos:
                nombre_base = archivo.name.rsplit('.', 1)[0]

                try:
                    img_original = Image.open(archivo)

                    for color in colores_finales:
                        op_actual += 1
                        progreso.progress(op_actual / total_ops)
                        estado.info(f"Generando: {nombre_base} → {color['nombre']}...")

                        # ── Aplicar colorización ──
                        if "Reemplazar" in metodo:
                            img_resultado, pixeles = reemplazar_color(
                                img_original,
                                color_origen,
                                color["hex"],
                                tolerancia=tolerancia
                            )
                            if pixeles < 100:
                                # Fallback a tono global si no encontró el color
                                img_resultado = cambio_tono_global(img_original, color["hex"], 0.7)
                        else:
                            img_resultado = cambio_tono_global(img_original, color["hex"], intensidad)

                        # ── Redimensionar si aplica ──
                        if tamaño_export != "Original":
                            if "1200" in tamaño_export:
                                max_size = 1200
                            elif "2400" in tamaño_export:
                                max_size = 2400
                            elif "800" in tamaño_export:
                                max_size = 800
                            else:
                                max_size = None

                            if max_size:
                                img_resultado.thumbnail((max_size, max_size), Image.LANCZOS)

                        # ── Nombre del archivo output ──
                        nombre_color = color["nombre"].replace(" ", "_").lower()
                        nombre_output = f"{temporada}_{categoria}_{ref_base}_{nombre_color}"

                        # ── Export ──
                        img_buffer = io.BytesIO()

                        if "PNG" in formato_export:
                            if img_resultado.mode != 'RGBA':
                                img_resultado = img_resultado.convert('RGBA')
                            img_resultado.save(img_buffer, format='PNG', optimize=True)
                            ext = "png"
                        else:
                            img_final = pegar_sobre_blanco(img_resultado)
                            img_final.save(img_buffer, format='JPEG', quality=calidad_jpg)
                            ext = "jpg"

                        carpeta = color["nombre"].replace(" ", "_")
                        zf.writestr(f"{carpeta}/{nombre_output}.{ext}", img_buffer.getvalue())
                        total_generadas += 1

                except Exception as e:
                    errores.append(f"{archivo.name}: {str(e)}")

        progreso.progress(1.0)
        estado.success(f"✅ {total_generadas} variantes generadas")

        if errores:
            st.warning(f"⚠️ Algunos errores: {', '.join(errores)}")

        # ── PREVIEW DE RESULTADOS ──
        st.subheader("👁️ Preview de Variantes")

        # Re-procesar para mostrar preview (primera imagen, primeros 6 colores)
        if archivos and colores_finales:
            img_prev = Image.open(archivos[0])
            cols_preview = st.columns(min(len(colores_finales), 6))

            for i, color in enumerate(colores_finales[:6]):
                with cols_preview[i]:
                    try:
                        if "Reemplazar" in metodo:
                            img_p, _ = reemplazar_color(img_prev, color_origen, color["hex"], tolerancia)
                        else:
                            img_p = cambio_tono_global(img_prev, color["hex"], intensidad)

                        img_display = pegar_sobre_blanco(img_p)
                        img_display.thumbnail((300, 300))
                        st.image(img_display, caption=color["nombre"], use_container_width=True)

                        st.markdown(
                            f'<div style="background:{color["hex"]};height:20px;border-radius:3px;'
                            f'border:1px solid #444;"></div>',
                            unsafe_allow_html=True
                        )
                    except:
                        st.error(f"Error en {color['nombre']}")

        # ── DESCARGA ──
        st.divider()
        nombre_zip = f"ZZ_VARIANTES_{ref_base}_{temporada}_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"

        st.download_button(
            label=f"⬇️ DESCARGAR TODO ({total_generadas} variantes)",
            data=zip_buffer.getvalue(),
            file_name=nombre_zip,
            mime="application/zip",
            use_container_width=True
        )

# ── INFO RÁPIDA ────────────────────────────────────────────────────────────
with st.expander("💡 Cómo funciona mejor"):
    st.markdown("""
    **Para mejores resultados:**

    - ✅ **PNG con transparencia** → resultado perfecto (renders de Illustrator/Photoshop)
    - ✅ **Render de color plano** → excelente con "Reemplazar color específico"
    - ✅ **Un color dominante** → usa "Cambio de tono global" (más rápido)
    - ⚠️ **Foto de estudio JPG** → primero pasa por Ghost Mannequin para quitar fondo

    **Tolerancia recomendada:**
    - Negros/muy oscuros → 35-45
    - Grises medios → 40-55
    - Colores vivos → 30-40
    - Blancos/muy claros → 20-30

    **Métodos:**
    - 🎯 *Reemplazar color específico*: pícalo con el selector de color — preserva texturas y sombras
    - 🌈 *Cambio de tono global*: tiñe toda la prenda — ideal para básicos de un color
    """)

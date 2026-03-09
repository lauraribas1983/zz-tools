"""
ZZ Studio — Generador de Rayas y Patrones
Crea swatches de rayas, cuadros y estampados geométricos para presentación y fabrica
Export en PNG de alta resolución listo para ficha técnica
"""

import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
import io
import zipfile
from datetime import datetime

st.set_page_config(
    page_title="ZZ · Rayas & Patrones",
    page_icon="🪡",
    layout="wide"
)

st.markdown("""
<style>
    .stButton > button { background: #FFD700; color: #000; font-weight: bold; border: none; }
    .stButton > button:hover { background: #FFC200; }
</style>
""", unsafe_allow_html=True)

# ─── FUNCIONES GENERACIÓN ─────────────────────────────────────────────────

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def generar_rayas_verticales(colores_rgb, anchos_px, alto_px=800, repeticiones=1):
    """Genera patrón de rayas verticales con anchos personalizados"""
    ancho_patron = sum(anchos_px)
    ancho_total = ancho_patron * repeticiones
    img = Image.new('RGB', (ancho_total, alto_px), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    for rep in range(repeticiones):
        x_offset = rep * ancho_patron
        x_actual = x_offset
        for i, (color, ancho) in enumerate(zip(colores_rgb, anchos_px)):
            draw.rectangle([x_actual, 0, x_actual + ancho - 1, alto_px], fill=color)
            x_actual += ancho

    return img

def generar_rayas_horizontales(colores_rgb, alturas_px, ancho_px=800, repeticiones=1):
    """Genera patrón de rayas horizontales"""
    alto_patron = sum(alturas_px)
    alto_total = alto_patron * repeticiones
    img = Image.new('RGB', (ancho_px, alto_total), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    for rep in range(repeticiones):
        y_offset = rep * alto_patron
        y_actual = y_offset
        for color, alto in zip(colores_rgb, alturas_px):
            draw.rectangle([0, y_actual, ancho_px, y_actual + alto - 1], fill=color)
            y_actual += alto

    return img

def generar_rayas_diagonales(colores_rgb, ancho_banda, tamaño=800, angulo=45):
    """Genera rayas diagonales"""
    img = Image.new('RGB', (tamaño * 2, tamaño * 2), colores_rgb[0])
    draw = ImageDraw.Draw(img)

    num_bandas = (tamaño * 4) // ancho_banda + 2
    n_colores = len(colores_rgb)

    for i in range(num_bandas):
        x_start = i * ancho_banda - tamaño
        color = colores_rgb[i % n_colores]
        # Banda diagonal (45 grados)
        puntos = [
            (x_start, 0),
            (x_start + ancho_banda, 0),
            (x_start + ancho_banda + tamaño * 2, tamaño * 2),
            (x_start + tamaño * 2, tamaño * 2)
        ]
        draw.polygon(puntos, fill=color)

    # Recortar al tamaño final
    img = img.crop((tamaño//2, tamaño//2, tamaño + tamaño//2, tamaño + tamaño//2))
    return img

def generar_cuadros(colores_rgb, tamaño_celda, dimensiones=800, estilo="cuadro"):
    """Genera patrón de cuadros (vichy, príncipe de gales, etc)"""
    img = Image.new('RGB', (dimensiones, dimensiones), colores_rgb[0])
    draw = ImageDraw.Draw(img)

    if estilo == "vichy":
        # Cuadros simples alternos
        for y in range(0, dimensiones, tamaño_celda):
            for x in range(0, dimensiones, tamaño_celda):
                fila = (y // tamaño_celda) % len(colores_rgb)
                col_idx = (x // tamaño_celda) % len(colores_rgb)
                color = colores_rgb[(fila + col_idx) % len(colores_rgb)]
                draw.rectangle([x, y, x + tamaño_celda, y + tamaño_celda], fill=color)

    elif estilo == "principe_gales":
        # Fondo base
        for y in range(0, dimensiones, tamaño_celda):
            for x in range(0, dimensiones, tamaño_celda):
                fila = (y // tamaño_celda) % 2
                col_idx = (x // tamaño_celda) % 2
                color = colores_rgb[(fila + col_idx) % len(colores_rgb)]
                draw.rectangle([x, y, x + tamaño_celda, y + tamaño_celda], fill=color)
        # Añadir líneas finas de contraste
        if len(colores_rgb) > 2:
            for i in range(0, dimensiones, tamaño_celda * 2):
                draw.line([(i, 0), (i, dimensiones)], fill=colores_rgb[2], width=1)
                draw.line([(0, i), (dimensiones, i)], fill=colores_rgb[2], width=1)

    elif estilo == "buffalo":
        # Cuadros grandes, alto contraste
        tamaño_grande = tamaño_celda * 2
        for y in range(0, dimensiones, tamaño_grande):
            for x in range(0, dimensiones, tamaño_grande):
                fila = (y // tamaño_grande) % 2
                col_idx = (x // tamaño_grande) % 2
                # Cuarto superior izquierdo
                draw.rectangle([x, y, x + tamaño_grande//2, y + tamaño_grande//2],
                               fill=colores_rgb[0])
                # Cuarto superior derecho
                draw.rectangle([x + tamaño_grande//2, y, x + tamaño_grande, y + tamaño_grande//2],
                               fill=colores_rgb[1 % len(colores_rgb)])
                # Cuarto inferior izquierdo
                draw.rectangle([x, y + tamaño_grande//2, x + tamaño_grande//2, y + tamaño_grande],
                               fill=colores_rgb[1 % len(colores_rgb)])
                # Cuarto inferior derecho
                draw.rectangle([x + tamaño_grande//2, y + tamaño_grande//2, x + tamaño_grande, y + tamaño_grande],
                               fill=colores_rgb[0])

    return img

def generar_estampado_geometrico(colores_rgb, forma, tamaño_px, dimensiones=800):
    """Genera estampado con formas geométricas repetidas"""
    img = Image.new('RGB', (dimensiones, dimensiones), colores_rgb[0])
    draw = ImageDraw.Draw(img)

    paso = tamaño_px * 2
    n_colores = len(colores_rgb)

    for row_idx, y in enumerate(range(0, dimensiones + paso, paso)):
        for col_idx, x in enumerate(range(0, dimensiones + paso, paso)):
            # Offset en filas alternas
            x_real = x + (tamaño_px if row_idx % 2 == 1 else 0)
            color = colores_rgb[(row_idx + col_idx) % max(n_colores - 1, 1) + 0]
            if len(colores_rgb) > 1:
                color = colores_rgb[1 + (row_idx + col_idx) % (n_colores - 1)]

            cx, cy = x_real + tamaño_px//2, y + tamaño_px//2

            if forma == "círculos":
                r = tamaño_px // 2 - 2
                draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)

            elif forma == "cuadrados":
                d = tamaño_px // 2 - 2
                draw.rectangle([cx - d, cy - d, cx + d, cy + d], fill=color)

            elif forma == "rombos":
                d = tamaño_px // 2 - 2
                draw.polygon([
                    (cx, cy - d), (cx + d, cy),
                    (cx, cy + d), (cx - d, cy)
                ], fill=color)

            elif forma == "triángulos":
                d = tamaño_px // 2 - 2
                draw.polygon([
                    (cx, cy - d),
                    (cx + d, cy + d),
                    (cx - d, cy + d)
                ], fill=color)

    return img

def añadir_marco_referencia(img, texto_ref, color_bg=(26, 26, 26)):
    """Añade un marco con info de referencia al swatch"""
    from PIL import ImageDraw, ImageFont
    ancho, alto = img.size
    margen = 60
    img_con_marco = Image.new('RGB', (ancho, alto + margen), color_bg)
    img_con_marco.paste(img, (0, margen))

    draw = ImageDraw.Draw(img_con_marco)
    draw.text((10, 18), texto_ref, fill=(255, 215, 0))

    return img_con_marco

# ─── UI ───────────────────────────────────────────────────────────────────

st.title("🪡 ZZ · Rayas & Patrones")
st.caption("Genera swatches de tejido • Rayas, cuadros, estampados • Export PNG para fichas")

col_izq, col_der = st.columns([1.2, 1], gap="large")

with col_izq:
    # ── TIPO DE PATRÓN ──
    tipo_patron = st.selectbox("Tipo de patrón", [
        "Rayas Verticales",
        "Rayas Horizontales",
        "Rayas Diagonales",
        "Cuadros Vichy",
        "Príncipe de Gales",
        "Buffalo Check",
        "Estampado Puntos",
        "Estampado Rombos",
        "Estampado Cuadros",
        "Estampado Triángulos",
    ])

    st.divider()

    # ── COLORES ──
    st.subheader("🎨 Colores del patrón")

    num_colores = st.slider("Número de colores", 2, 6, 3)

    COLORES_PRESET = {
        "Negro/Blanco": ["#1A1A1A", "#FFFFFF"],
        "Navy/Blanco": ["#1B2A4A", "#FFFFFF"],
        "Navy/Rojo": ["#1B2A4A", "#CC1111"],
        "Camel/Crema": ["#C19A6B", "#F5F0E8"],
        "Breton (Navy/Blanco/Rojo)": ["#1B2A4A", "#FFFFFF", "#CC1111"],
        "Sage/Ecru": ["#8FAF8F", "#F5F0E8"],
        "Burgundy/Camel": ["#800020", "#C19A6B"],
        "SS26 (Butter/Sage/Ecru)": ["#F5D76E", "#8FAF8F", "#F5F0E8"],
    }

    preset_sel = st.selectbox("Preset de colores", ["Personalizado"] + list(COLORES_PRESET.keys()))

    colores_finales = []
    if preset_sel != "Personalizado":
        preset_cols = COLORES_PRESET[preset_sel]
        num_colores = len(preset_cols)

    cols_color = st.columns(min(num_colores, 3))
    for i in range(num_colores):
        col_idx = i % 3
        with cols_color[col_idx]:
            if preset_sel != "Personalizado" and i < len(preset_cols):
                default_hex = preset_cols[i]
            else:
                defaults = ["#1A1A1A", "#FFFFFF", "#808080", "#C19A6B", "#8FAF8F", "#CC1111"]
                default_hex = defaults[i % len(defaults)]

            col_val = st.color_picker(f"Color {i+1}", default_hex, key=f"pat_col_{i}")
            nombre = st.text_input(f"Nombre {i+1}", f"Col{i+1}", key=f"pat_nom_{i}")
            colores_finales.append({"hex": col_val, "nombre": nombre})

    st.divider()

    # ── PARÁMETROS DEL PATRÓN ──
    st.subheader("📐 Parámetros")

    if "Rayas" in tipo_patron:
        if tipo_patron == "Rayas Verticales":
            st.markdown("**Anchos de cada raya (mm):**")
            anchos = []
            cols_anchos = st.columns(num_colores)
            for i in range(num_colores):
                with cols_anchos[i]:
                    ancho = st.number_input(f"Raya {i+1}", 5, 100,
                                          [10, 10, 5, 5, 5, 5][i] if i < 6 else 10,
                                          key=f"ancho_{i}")
                    anchos.append(ancho * 4)  # px (4px = ~1mm a 96dpi)
            repeticiones = st.slider("Repeticiones del patrón", 1, 10, 4)

        elif tipo_patron == "Rayas Horizontales":
            st.markdown("**Alturas de cada raya (mm):**")
            alturas = []
            for i in range(num_colores):
                alt = st.number_input(f"Raya {i+1} (mm)", 5, 100, 15, key=f"alt_{i}")
                alturas.append(alt * 4)
            repeticiones = st.slider("Repeticiones", 1, 10, 3)

        elif tipo_patron == "Rayas Diagonales":
            ancho_banda = st.slider("Ancho de banda (px)", 10, 150, 40)

    elif "Cuadros" in tipo_patron or "Príncipe" in tipo_patron or "Buffalo" in tipo_patron:
        tamaño_celda = st.slider("Tamaño de celda (px)", 15, 120, 40)

    elif "Estampado" in tipo_patron:
        tamaño_forma = st.slider("Tamaño de la forma (px)", 10, 100, 30)

    # ── DIMENSIONES EXPORT ──
    st.divider()
    st.subheader("📦 Export")

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        dim_export = st.selectbox("Resolución", [
            "800×800 (web/preview)",
            "1600×1600 (ficha técnica)",
            "3200×3200 (impresión)",
        ])
        dim_map = {"800×800": 800, "1600×1600": 1600, "3200×3200": 3200}
        dim_px = dim_map[dim_export.split(" ")[0]]
    with col_d2:
        ref_label = st.text_input("Referencia (para el marco)", "ZZ-PTR-001 · SS26")
        añadir_marco = st.checkbox("Añadir marco con referencia", value=True)

    # ── VARIANTES ──
    st.divider()
    generar_variantes = st.checkbox("Generar variantes de color automáticas", value=False)
    if generar_variantes:
        num_variantes = st.slider("Número de variantes de color", 2, 8, 4)
        st.caption("Generará el mismo patrón rotando los colores")

with col_der:
    st.subheader("👁️ Preview en vivo")

    # Generar preview en tiempo real
    colores_rgb = [tuple(int(c["hex"].lstrip('#')[i:i+2], 16) for i in (0,2,4)) for c in colores_finales]

    try:
        # Preview más pequeño para velocidad
        preview_dim = 400

        if tipo_patron == "Rayas Verticales":
            anchos_preview = [a // 2 for a in anchos] if 'anchos' in dir() else [40, 40, 20] * 2
            img_preview = generar_rayas_verticales(colores_rgb, anchos_preview, preview_dim, min(repeticiones if 'repeticiones' in dir() else 4, 6))

        elif tipo_patron == "Rayas Horizontales":
            alturas_preview = [a // 2 for a in alturas] if 'alturas' in dir() else [40, 40, 20]
            img_preview = generar_rayas_horizontales(colores_rgb, alturas_preview, preview_dim, min(repeticiones if 'repeticiones' in dir() else 3, 5))

        elif tipo_patron == "Rayas Diagonales":
            ancho_b = ancho_banda if 'ancho_banda' in dir() else 40
            img_preview = generar_rayas_diagonales(colores_rgb, ancho_b, preview_dim)

        elif tipo_patron == "Cuadros Vichy":
            cel = tamaño_celda if 'tamaño_celda' in dir() else 40
            img_preview = generar_cuadros(colores_rgb, cel, preview_dim, "vichy")

        elif tipo_patron == "Príncipe de Gales":
            cel = tamaño_celda if 'tamaño_celda' in dir() else 40
            img_preview = generar_cuadros(colores_rgb, cel, preview_dim, "principe_gales")

        elif tipo_patron == "Buffalo Check":
            cel = tamaño_celda if 'tamaño_celda' in dir() else 40
            img_preview = generar_cuadros(colores_rgb, cel, preview_dim, "buffalo")

        elif tipo_patron == "Estampado Puntos":
            tam = tamaño_forma if 'tamaño_forma' in dir() else 30
            img_preview = generar_estampado_geometrico(colores_rgb, "círculos", tam, preview_dim)

        elif tipo_patron == "Estampado Rombos":
            tam = tamaño_forma if 'tamaño_forma' in dir() else 30
            img_preview = generar_estampado_geometrico(colores_rgb, "rombos", tam, preview_dim)

        elif tipo_patron == "Estampado Cuadros":
            tam = tamaño_forma if 'tamaño_forma' in dir() else 30
            img_preview = generar_estampado_geometrico(colores_rgb, "cuadrados", tam, preview_dim)

        elif tipo_patron == "Estampado Triángulos":
            tam = tamaño_forma if 'tamaño_forma' in dir() else 30
            img_preview = generar_estampado_geometrico(colores_rgb, "triángulos", tam, preview_dim)

        else:
            img_preview = Image.new('RGB', (preview_dim, preview_dim), (200, 200, 200))

        st.image(img_preview, caption="Preview (baja resolución)", use_container_width=True)

        # ── Paleta de colores usados ──
        st.markdown("**Paleta:**")
        cols_pal = st.columns(num_colores)
        for i, color in enumerate(colores_finales):
            with cols_pal[i]:
                st.markdown(
                    f'<div style="background:{color["hex"]};height:35px;border-radius:4px;'
                    f'border:1px solid #555;"></div>'
                    f'<p style="font-size:11px;text-align:center;margin-top:3px;">{color["nombre"]}</p>',
                    unsafe_allow_html=True
                )

    except Exception as e:
        st.error(f"Error en preview: {e}")

# ── BOTÓN GENERAR ──────────────────────────────────────────────────────────
st.divider()

if st.button("🚀 GENERAR SWATCHES EN ALTA RESOLUCIÓN", use_container_width=True):

    zip_buffer = io.BytesIO()
    generados = []

    progreso = st.progress(0)
    estado = st.empty()

    # Definir qué variantes generar
    variantes_colores = [colores_rgb]
    variantes_nombres = ["original"]

    if generar_variantes:
        for v in range(1, num_variantes):
            # Rotar colores
            rotado = colores_rgb[v:] + colores_rgb[:v]
            variantes_colores.append(rotado)
            variantes_nombres.append(f"var{v}")

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        total = len(variantes_colores)
        for idx, (v_colores, v_nombre) in enumerate(zip(variantes_colores, variantes_nombres)):
            progreso.progress((idx + 1) / total)
            estado.info(f"Generando {v_nombre}...")

            try:
                if tipo_patron == "Rayas Verticales":
                    img_final = generar_rayas_verticales(v_colores, anchos, dim_px, repeticiones)
                elif tipo_patron == "Rayas Horizontales":
                    img_final = generar_rayas_horizontales(v_colores, alturas, dim_px, repeticiones)
                elif tipo_patron == "Rayas Diagonales":
                    img_final = generar_rayas_diagonales(v_colores, ancho_banda, dim_px)
                elif tipo_patron == "Cuadros Vichy":
                    img_final = generar_cuadros(v_colores, tamaño_celda, dim_px, "vichy")
                elif tipo_patron == "Príncipe de Gales":
                    img_final = generar_cuadros(v_colores, tamaño_celda, dim_px, "principe_gales")
                elif tipo_patron == "Buffalo Check":
                    img_final = generar_cuadros(v_colores, tamaño_celda, dim_px, "buffalo")
                elif "Puntos" in tipo_patron:
                    img_final = generar_estampado_geometrico(v_colores, "círculos", tamaño_forma, dim_px)
                elif "Rombos" in tipo_patron:
                    img_final = generar_estampado_geometrico(v_colores, "rombos", tamaño_forma, dim_px)
                elif "Cuadros" in tipo_patron and "Estampado" in tipo_patron:
                    img_final = generar_estampado_geometrico(v_colores, "cuadrados", tamaño_forma, dim_px)
                elif "Triángulos" in tipo_patron:
                    img_final = generar_estampado_geometrico(v_colores, "triángulos", tamaño_forma, dim_px)
                else:
                    img_final = img_preview.resize((dim_px, dim_px))

                if añadir_marco:
                    img_final = añadir_marco_referencia(img_final, f"{ref_label} · {v_nombre}")

                buf = io.BytesIO()
                img_final.save(buf, format='PNG', optimize=True)
                nombre_archivo = f"ZZ_PATRON_{tipo_patron.replace(' ', '_')}_{v_nombre}.png"
                zf.writestr(nombre_archivo, buf.getvalue())
                generados.append(nombre_archivo)

            except Exception as e:
                estado.error(f"Error en {v_nombre}: {e}")

    progreso.progress(1.0)
    estado.success(f"✅ {len(generados)} swatch(s) generado(s)")

    nombre_zip = f"ZZ_PATRONES_{tipo_patron.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
    st.download_button(
        label=f"⬇️ DESCARGAR SWATCHES ({len(generados)} archivos)",
        data=zip_buffer.getvalue(),
        file_name=nombre_zip,
        mime="application/zip",
        use_container_width=True
    )

with st.expander("💡 Usos en ZZ Studio"):
    st.markdown("""
    **Cómo usar estos swatches:**

    - 📋 **Ficha Técnica** → pega el swatch en la sección "Gráfica/Estampado" del TechPack Generator
    - 📧 **Confirmación cliente** → envía PNG directamente por WhatsApp/email para aprobación colorway
    - 🏭 **Fábrica** → referencia visual exacta de colores y proporciones de raya
    - 🎨 **Variantes** → genera toda la gama de colorways con un solo clic

    **Tipos más usados en knitwear:**
    - Rayas Verticales → camisetas rayas clásicas, cárdigans
    - Rayas Horizontales → jerseys, sudaderas náuticas
    - Cuadros Vichy → camisas, dresses casuales
    - Buffalo Check → outerwear, camisas leñadoras
    - Estampado Puntos → bodies, leggings, dresses
    """)

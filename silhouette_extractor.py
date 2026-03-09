#!/usr/bin/env python3
"""
ZZ · Silhouette Extractor Pro
Foto modelo / prenda → Silueta limpia sobre fondo blanco
Usa rembg para eliminación de fondo + PIL para limpiar y perfeccionar
"""
import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageOps
import numpy as np
import io

# rembg opcional — si no está en cloud, avisa
try:
    from rembg import remove as rembg_remove
    REMBG_OK = True
except ImportError:
    REMBG_OK = False

st.set_page_config(page_title="ZZ Silhouette Extractor", page_icon="✂️", layout="wide")

st.markdown("""
<style>
    .stApp { background: #0f0f0f; color: #e8e8e8; }
    .main .block-container { padding: 2rem; max-width: 1100px; }
    h1 { color: #c8ff00 !important; font-size: 1.4rem !important; letter-spacing: 3px; }
    h2 { color: #c8ff00 !important; font-size: 0.9rem !important; font-weight:700;
         letter-spacing:2px; border-bottom:1px solid #2c2c2c; padding-bottom:6px; }
    label { color: #999 !important; font-size: 0.82rem !important; }
    .stButton > button {
        background: #c8ff00 !important; color: #000 !important;
        font-weight: 700 !important; border: none !important;
        padding: 10px 24px !important; border-radius: 6px !important; width:100%;
    }
    .stDownloadButton > button {
        background: #1e1e1e !important; color: #c8ff00 !important;
        border: 1px solid #c8ff00 !important; font-weight: 700 !important;
        border-radius: 6px !important; width:100%; padding:10px !important;
    }
    .stFileUploader { background:#161616; border:1px dashed #2c2c2c; border-radius:8px; }
    div[data-testid="stImage"] img { border-radius:8px; border:1px solid #2c2c2c; }
</style>
""", unsafe_allow_html=True)

st.markdown("# ✂️ ZZ · SILHOUETTE EXTRACTOR PRO")
st.markdown("<p style='color:#888;font-size:0.85rem;margin-top:-12px;'>Foto modelo / cliente → Prenda limpia sobre fondo blanco · Exporta PNG transparente + JPG</p>", unsafe_allow_html=True)
st.markdown("---")

if not REMBG_OK:
    st.error("⚠️ rembg no disponible en este entorno. Contacta con el equipo ZZ para activarlo.")

# ── Parámetros por tipo de prenda ──
PRENDAS = {
    "Camiseta / Top":       {"edge_smooth": 2,   "crop_padding": 0.08, "auto_center": True},
    "Sudadera / Hoodie":    {"edge_smooth": 2.5, "crop_padding": 0.07, "auto_center": True},
    "Pantalón / Short":     {"edge_smooth": 2,   "crop_padding": 0.06, "auto_center": True},
    "Vestido / Falda":      {"edge_smooth": 1.5, "crop_padding": 0.07, "auto_center": True},
    "Chaqueta / Abrigo":    {"edge_smooth": 2.5, "crop_padding": 0.08, "auto_center": True},
    "Accesorio / Bolso":    {"edge_smooth": 1.5, "crop_padding": 0.10, "auto_center": True},
    "Calzado":              {"edge_smooth": 1.5, "crop_padding": 0.10, "auto_center": False},
}

FONDOS = {
    "Blanco puro (#FFF)":   (255, 255, 255),
    "Blanco cálido (#FAF9F6)": (250, 249, 246),
    "Gris claro (#F4F4F0)": (244, 244, 240),
    "Gris neutro (#E8E8E8)": (232, 232, 232),
    "Negro (#0A0A0A)":       (10, 10, 10),
}

def remove_background(img_pil):
    """Elimina fondo con rembg IA"""
    buf = io.BytesIO()
    img_pil.save(buf, format="PNG")
    buf.seek(0)
    result_bytes = rembg_remove(buf.getvalue())
    return Image.open(io.BytesIO(result_bytes)).convert("RGBA")

def auto_crop(img_rgba, padding=0.08):
    """Recorta automáticamente al bounding box de la prenda + padding"""
    alpha = np.array(img_rgba.split()[3])
    rows = np.any(alpha > 10, axis=1)
    cols = np.any(alpha > 10, axis=0)
    if not rows.any() or not cols.any():
        return img_rgba

    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]

    w, h = img_rgba.size
    pad_x = int((cmax - cmin) * padding)
    pad_y = int((rmax - rmin) * padding)

    left   = max(0, cmin - pad_x)
    right  = min(w, cmax + pad_x)
    top    = max(0, rmin - pad_y)
    bottom = min(h, rmax + pad_y)

    return img_rgba.crop((left, top, right, bottom))

def smooth_edges(img_rgba, radius=2.0):
    """Suaviza bordes de la silueta"""
    alpha = img_rgba.split()[3]
    alpha_smooth = alpha.filter(ImageFilter.GaussianBlur(radius=radius))
    # Reforzar alpha: threshold para mantener bordes definidos
    alpha_arr = np.array(alpha_smooth, dtype=np.float32)
    alpha_arr = np.clip(alpha_arr * 1.1, 0, 255)
    alpha_smooth = Image.fromarray(alpha_arr.astype(np.uint8))
    img_rgba.putalpha(alpha_smooth)
    return img_rgba

def correct_rotation(img_rgba):
    """Detecta inclinación y corrige (análisis de masa de píxeles)"""
    alpha = np.array(img_rgba.split()[3])
    h, w = alpha.shape

    # Centroide de la mitad superior (hombros)
    top_half = alpha[:h//3, :]
    cols = np.arange(w)
    row_masses = top_half.sum(axis=0)
    if row_masses.sum() == 0:
        return img_rgba

    centroid_x = (cols * row_masses).sum() / row_masses.sum()
    skew_px = centroid_x - w / 2
    angle_deg = math.atan2(skew_px, h / 3) * 180 / math.pi * 0.5  # suave

    if abs(angle_deg) > 0.5 and abs(angle_deg) < 8:
        img_rgba = img_rgba.rotate(-angle_deg, expand=False, fillcolor=(0, 0, 0, 0))

    return img_rgba

def compose_on_background(img_rgba, bg_color, canvas_size=None):
    """Coloca la silueta sobre fondo de color"""
    if canvas_size:
        # Canvas cuadrado con la silueta centrada
        cs = canvas_size
        bg = Image.new("RGB", (cs, cs), bg_color)
        # Escalar para que quepa con padding
        max_dim = int(cs * 0.88)
        img_rgba.thumbnail((max_dim, max_dim), Image.LANCZOS)
        offset_x = (cs - img_rgba.width) // 2
        offset_y = (cs - img_rgba.height) // 2
        bg.paste(img_rgba, (offset_x, offset_y), mask=img_rgba.split()[3])
    else:
        bg = Image.new("RGB", img_rgba.size, bg_color)
        bg.paste(img_rgba, (0, 0), mask=img_rgba.split()[3])

    return bg

# ── Importar math aquí ──
import math

# ── UI ──────────────────────────────────────────────────────────────────────
col_conf, col_main = st.columns([1, 2])

with col_conf:
    st.markdown("## CONFIGURACIÓN")
    uploaded = st.file_uploader(
        "Sube foto de modelo o prenda",
        type=["jpg", "jpeg", "png", "webp"],
        help="Funciona con fotos reales, renders, ghost mannequin..."
    )

    prenda = st.selectbox("Tipo de prenda", list(PRENDAS.keys()))
    fondo_nombre = st.selectbox("Fondo de salida", list(FONDOS.keys()))
    bg_color = FONDOS[fondo_nombre]

    canvas_cuadrado = st.checkbox("Canvas cuadrado centrado", value=True,
                                   help="Resultado en formato cuadrado 1:1 (ideal para web y catálogo)")
    if canvas_cuadrado:
        canvas_px = st.selectbox("Tamaño canvas", [800, 1200, 1600, 2400], index=1)
    else:
        canvas_px = None

    refinar_bordes = st.checkbox("Refinar bordes (más suave)", value=True)
    corregir_inclinacion = st.checkbox("Corregir inclinación automática", value=True)
    exportar_png = st.checkbox("Exportar también PNG transparente", value=True)

with col_main:
    st.markdown("## RESULTADO")

    if uploaded and REMBG_OK:
        img_orig = Image.open(uploaded)
        if img_orig.width > 2000:
            r = 2000 / img_orig.width
            img_orig = img_orig.resize((2000, int(img_orig.height * r)), Image.LANCZOS)

        procesar = st.button("✂️ EXTRAER SILUETA")

        if procesar:
            params = PRENDAS[prenda]
            progress = st.progress(0)

            with st.spinner("🤖 Eliminando fondo con IA..."):
                img_rgba = remove_background(img_orig)
            progress.progress(30)

            with st.spinner("✂️ Recortando silueta..."):
                img_rgba = auto_crop(img_rgba, padding=params["crop_padding"])
            progress.progress(50)

            if refinar_bordes:
                with st.spinner("🔲 Refinando bordes..."):
                    img_rgba = smooth_edges(img_rgba, radius=params["edge_smooth"])
            progress.progress(65)

            if corregir_inclinacion and params["auto_center"]:
                with st.spinner("📐 Corrigiendo inclinación..."):
                    img_rgba = correct_rotation(img_rgba)
            progress.progress(80)

            with st.spinner("🖼️ Componiendo resultado final..."):
                result_jpg = compose_on_background(img_rgba.copy(), bg_color, canvas_size=canvas_px)
            progress.progress(100)

            # Preview
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("<p style='color:#666;font-size:0.75rem;text-align:center;'>ORIGINAL</p>", unsafe_allow_html=True)
                st.image(img_orig, use_container_width=True)
            with col_b:
                st.markdown("<p style='color:#c8ff00;font-size:0.75rem;text-align:center;'>SILUETA EXTRAÍDA</p>", unsafe_allow_html=True)
                st.image(result_jpg, use_container_width=True)

            st.markdown("---")

            # Descarga JPG
            buf_jpg = io.BytesIO()
            result_jpg.save(buf_jpg, format="JPEG", quality=95)
            buf_jpg.seek(0)
            st.download_button(
                label="⬇️  DESCARGAR JPG (fondo de color)",
                data=buf_jpg, file_name="ZZ_silueta.jpg", mime="image/jpeg"
            )

            # Descarga PNG transparente
            if exportar_png:
                buf_png = io.BytesIO()
                img_rgba.save(buf_png, format="PNG")
                buf_png.seek(0)
                st.download_button(
                    label="⬇️  DESCARGAR PNG (fondo transparente)",
                    data=buf_png, file_name="ZZ_silueta_transparente.png", mime="image/png"
                )

    elif uploaded and not REMBG_OK:
        st.error("rembg no disponible. Esta herramienta requiere el módulo de IA para eliminar fondos.")
    else:
        st.markdown("""
        <div style='background:#161616;border:1px dashed #2c2c2c;border-radius:8px;
                    padding:60px;text-align:center;'>
        <p style='color:#444;font-size:2.5rem;'>✂️</p>
        <p style='color:#666;font-size:0.85rem;'>Sube una foto de modelo o prenda</p>
        <p style='color:#444;font-size:0.75rem;'>La IA extrae la prenda y la pone sobre fondo limpio</p>
        </div>
        """, unsafe_allow_html=True)

#!/usr/bin/env python3
"""
ZZ · Fabric Wrinkle Generator
Render plano → Arrugas naturales de tela
"""
import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw
import numpy as np
import io

st.set_page_config(page_title="ZZ Fabric Wrinkle", page_icon="👕", layout="wide")

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

st.markdown("# 👕 ZZ · FABRIC WRINKLE GENERATOR")
st.markdown("<p style='color:#888;font-size:0.85rem;margin-top:-12px;'>Render plano → Arrugas naturales · Camiseta · Sudadera · Vestido · Pantalón</p>", unsafe_allow_html=True)
st.markdown("---")

# ── Parámetros por tipo de prenda ──
PRENDAS = {
    "Camiseta stretch":     {"fold_depth": 0.25, "randomness": 0.40, "tension": 0.30, "blur": 2.0},
    "Camiseta algodón":     {"fold_depth": 0.20, "randomness": 0.35, "tension": 0.25, "blur": 1.8},
    "Sudadera":             {"fold_depth": 0.30, "randomness": 0.45, "tension": 0.35, "blur": 2.5},
    "Vestido fluido":       {"fold_depth": 0.18, "randomness": 0.50, "tension": 0.15, "blur": 1.5},
    "Pantalón chino":       {"fold_depth": 0.15, "randomness": 0.25, "tension": 0.20, "blur": 1.6},
    "Chaqueta lana":        {"fold_depth": 0.35, "randomness": 0.30, "tension": 0.40, "blur": 2.8},
    "Camisa algodón":       {"fold_depth": 0.22, "randomness": 0.38, "tension": 0.28, "blur": 2.0},
    "Jersey punto":         {"fold_depth": 0.20, "randomness": 0.35, "tension": 0.25, "blur": 2.2},
}

def crear_mapa_arrugas(size, params, seed=42):
    """Genera mapa de arrugas orgánicas multi-frecuencia"""
    np.random.seed(seed)
    w, h = size

    x = np.linspace(0, 4 * np.pi, w, dtype=np.float32)
    y = np.linspace(0, 6 * np.pi, h, dtype=np.float32)
    X, Y = np.meshgrid(x, y)

    # Capas de ondas sinusoidales
    wave1 = np.sin(X * 1.2 + Y * 0.8) * 0.40
    wave2 = np.sin(X * 2.5 + Y * 1.9) * 0.25
    wave3 = np.sin(X * 4.0 - Y * 2.1) * 0.15

    wrinkle_field = wave1 + wave2 + wave3

    # Ruido orgánico
    noise = np.random.randn(h, w).astype(np.float32) * params["randomness"]
    wrinkle_field += noise

    # Líneas de tensión verticales (costuras laterales)
    for x_pos in [w * 0.12, w * 0.88]:
        gauss = np.exp(-((np.arange(w) - x_pos) / (w * 0.06)) ** 2)
        wrinkle_field += gauss[np.newaxis, :] * params["tension"] * 0.8

    # Normalizar 0-1
    wf_min, wf_max = wrinkle_field.min(), wrinkle_field.max()
    wrinkle_field = (wrinkle_field - wf_min) / (wf_max - wf_min + 1e-9)

    # Suavizar según tela
    wf_img = Image.fromarray((wrinkle_field * 255).astype(np.uint8), 'L')
    wf_img = wf_img.filter(ImageFilter.GaussianBlur(radius=params["blur"]))

    return wf_img

def aplicar_arrugas(img, mapa_arrugas, params, intensity):
    """Shadows + highlights basados en el mapa de arrugas"""
    img_arr = np.array(img.convert('RGB'), dtype=np.float32) / 255.0
    mapa_arr = np.array(mapa_arrugas, dtype=np.float32) / 255.0

    fold_depth = params["fold_depth"] * intensity

    # Zonas oscuras (valles arruga)
    shadow_factor = 1.0 - fold_depth * (1.0 - mapa_arr)
    shadow_factor = np.clip(shadow_factor, 0, 1)

    # Zonas brillantes (crestas arruga)
    edge_threshold = 0.75
    highlight_mask = np.where(mapa_arr > edge_threshold,
                              (mapa_arr - edge_threshold) / (1 - edge_threshold), 0)
    highlight_factor = 1.0 + fold_depth * 0.4 * highlight_mask

    # Combinar shadows y highlights
    result = img_arr * shadow_factor[:, :, np.newaxis] * highlight_factor[:, :, np.newaxis]
    result = np.clip(result, 0, 1)

    # Mezcla con original según intensidad
    final = img_arr * (1 - intensity * 0.7) + result * (intensity * 0.7)
    final = np.clip(final, 0, 1)

    return Image.fromarray((final * 255).astype(np.uint8))

def agregar_hilos_reflejo(img, num_hilos=25, seed=42):
    """Añade pequeños reflejos de hilos"""
    np.random.seed(seed)
    w, h = img.size
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for _ in range(num_hilos):
        x1 = int(np.random.uniform(w * 0.1, w * 0.9))
        y1 = int(np.random.uniform(h * 0.15, h * 0.7))
        length = int(np.random.uniform(20, 70))
        angle = np.random.uniform(-0.4, 0.4)
        x2 = x1 + int(np.cos(angle) * length)
        y2 = y1 + int(np.sin(angle) * length)
        alpha = int(np.random.uniform(40, 110))
        draw.line([x1, y1, x2, y2], fill=(255, 255, 255, alpha), width=1)

    blurred = overlay.filter(ImageFilter.GaussianBlur(radius=1.2))
    return Image.alpha_composite(img.convert('RGBA'), blurred).convert('RGB')

def generar_con_arrugas(base_img, prenda_nombre, intensity, seed=42):
    """Pipeline completo"""
    params = PRENDAS[prenda_nombre]

    if base_img.width > 1800:
        ratio = 1800 / base_img.width
        base_img = base_img.resize(
            (1800, int(base_img.height * ratio)), Image.LANCZOS
        )

    # 1. Mapa de arrugas
    mapa = crear_mapa_arrugas(base_img.size, params, seed=seed)

    # 2. Aplicar sombras/luces
    result = aplicar_arrugas(base_img, mapa, params, intensity)

    # 3. Reflejos de hilos
    if intensity > 0.3:
        result = agregar_hilos_reflejo(result, num_hilos=int(25 * intensity), seed=seed)

    # 4. Polish
    result = ImageEnhance.Sharpness(result).enhance(1.08)
    result = ImageEnhance.Contrast(result).enhance(1.04)

    return result

# ── UI ──────────────────────────────────────────────────────────────────────
col_conf, col_main = st.columns([1, 2])

with col_conf:
    st.markdown("## CONFIGURACIÓN")

    uploaded = st.file_uploader(
        "Sube el render / flat de prenda",
        type=["jpg", "jpeg", "png", "webp"]
    )

    prenda = st.selectbox("Tipo de prenda", list(PRENDAS.keys()))

    intensity = st.slider(
        "Intensidad de arrugas", 0.1, 1.0, 0.60, 0.05,
        help="0.1 = apenas visible  |  1.0 = arrugas profundas"
    )

    seed_val = st.slider(
        "Variación de patrón", 1, 99, 42,
        help="Cambia la distribución de arrugas sin tocar la intensidad"
    )

    st.markdown("---")
    p = PRENDAS[prenda]
    st.markdown(f"""
    <div style='background:#1a1a1a;border:1px solid #2c2c2c;border-radius:8px;
                padding:12px 16px;margin:8px 0;font-size:0.8rem;color:#888;'>
    Profundidad pliegues: {'●' * int(p['fold_depth']*20)}{'○' * (5-int(p['fold_depth']*20))}<br>
    Tensión lateral: {'●' * int(p['tension']*10)}{'○' * (5-int(p['tension']*10))}<br>
    Aleatoriedad: {'●' * int(p['randomness']*10)}{'○' * (5-int(p['randomness']*10))}
    </div>
    """, unsafe_allow_html=True)

with col_main:
    st.markdown("## PREVIEW")

    if uploaded:
        img_orig = Image.open(uploaded)

        with st.spinner("Generando arrugas..."):
            result = generar_con_arrugas(img_orig, prenda, intensity, seed=seed_val)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("<p style='color:#666;font-size:0.75rem;text-align:center;'>FLAT ORIGINAL</p>", unsafe_allow_html=True)
            st.image(img_orig, use_container_width=True)
        with col_b:
            st.markdown(f"<p style='color:#c8ff00;font-size:0.75rem;text-align:center;'>CON ARRUGAS · {prenda.upper()}</p>", unsafe_allow_html=True)
            st.image(result, use_container_width=True)

        st.markdown("---")
        buf = io.BytesIO()
        result.save(buf, format="JPEG", quality=95)
        buf.seek(0)
        fname = f"ZZ_wrinkle_{prenda.lower().replace(' ','_')}.jpg"
        st.download_button(
            label=f"⬇️  DESCARGAR — {prenda} con arrugas (JPG 95%)",
            data=buf,
            file_name=fname,
            mime="image/jpeg"
        )
    else:
        st.markdown("""
        <div style='background:#161616;border:1px dashed #2c2c2c;border-radius:8px;
                    padding:60px;text-align:center;'>
        <p style='color:#444;font-size:2.5rem;'>👕</p>
        <p style='color:#666;font-size:0.85rem;'>Sube un render de prenda para empezar</p>
        <p style='color:#444;font-size:0.75rem;'>Funciona mejor con renders sobre fondo blanco</p>
        </div>
        """, unsafe_allow_html=True)

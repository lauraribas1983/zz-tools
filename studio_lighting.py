#!/usr/bin/env python3
"""
ZZ · Studio Lighting Simulator
Render plano → Iluminación profesional de estudio
"""
import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw
import numpy as np
import io
import math

st.set_page_config(page_title="ZZ Studio Lighting", page_icon="💡", layout="wide")

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

st.markdown("# 💡 ZZ · STUDIO LIGHTING SIMULATOR")
st.markdown("<p style='color:#888;font-size:0.85rem;margin-top:-12px;'>Render plano → Iluminación profesional · eCommerce · Magazine · Lookbook · Vintage</p>", unsafe_allow_html=True)
st.markdown("---")

# ── Esquemas de iluminación ──
SETUPS = {
    "eCommerce Clean": {
        "desc": "Fondo blanco puro, luz uniforme suave. Ideal Zara/H&M.",
        "key": 0.40, "fill": 0.28, "rim": 0.12, "shadow": 18,
        "contrast": 1.06, "brightness": 1.03, "warmth": 0,
    },
    "Fashion Magazine": {
        "desc": "Contraste dramático, sombras definidas. Ideal editorial.",
        "key": 0.55, "fill": 0.15, "rim": 0.30, "shadow": 8,
        "contrast": 1.18, "brightness": 0.98, "warmth": -5,
    },
    "Streetwear Flatlay": {
        "desc": "Luz cenital suave y uniforme, sombras mínimas.",
        "key": 0.65, "fill": 0.45, "rim": 0.08, "shadow": 25,
        "contrast": 1.08, "brightness": 1.05, "warmth": 5,
    },
    "Lookbook Model": {
        "desc": "Rim light dramático, profundidad, aspecto sesión de fotos.",
        "key": 0.35, "fill": 0.20, "rim": 0.38, "shadow": 10,
        "contrast": 1.14, "brightness": 0.96, "warmth": -8,
    },
    "Product White": {
        "desc": "Sobreexposición controlada, fondo blanco puro sin sombras.",
        "key": 0.85, "fill": 0.65, "rim": 0.05, "shadow": 30,
        "contrast": 1.02, "brightness": 1.08, "warmth": 3,
    },
    "Vintage Film": {
        "desc": "Luz suave cálida, contraste bajo, grano analógico.",
        "key": 0.30, "fill": 0.18, "rim": 0.15, "shadow": 6,
        "contrast": 0.92, "brightness": 0.97, "warmth": 18,
    },
    "Neon Studio": {
        "desc": "Luz fría lateral + rim cálido. Tendencia SS26.",
        "key": 0.45, "fill": 0.20, "rim": 0.35, "shadow": 12,
        "contrast": 1.20, "brightness": 1.00, "warmth": -15,
    },
}

def make_gradient(size, cx, cy, radius, intensity):
    """Crea un gradiente radial gaussiano (numpy, eficiente)"""
    w, h = size
    x = np.arange(w, dtype=np.float32)
    y = np.arange(h, dtype=np.float32)
    X, Y = np.meshgrid(x, y)
    dist_sq = ((X - cx * w) ** 2 + (Y - cy * h) ** 2)
    gradient = np.exp(-dist_sq / (2 * (radius * w) ** 2))
    return (gradient * intensity).astype(np.float32)

def apply_key_light(img_arr, params):
    """Luz principal desde arriba-izquierda (45°)"""
    h, w = img_arr.shape[:2]
    grad = make_gradient((w, h), cx=0.25, cy=0.25, radius=0.55, intensity=params["key"])
    grad_3ch = np.stack([grad, grad, grad], axis=-1)
    # Screen blend: 1 - (1-base)*(1-light)
    result = 1.0 - (1.0 - img_arr) * (1.0 - grad_3ch)
    return np.clip(result, 0, 1)

def apply_fill_light(img_arr, params):
    """Luz de relleno suave desde derecha"""
    h, w = img_arr.shape[:2]
    grad = make_gradient((w, h), cx=0.78, cy=0.55, radius=0.65, intensity=params["fill"])
    # Warm fill (ligeramente amarillento para calidez)
    warm = np.stack([grad * 1.0, grad * 0.97, grad * 0.90], axis=-1)
    result = 1.0 - (1.0 - img_arr) * (1.0 - warm)
    return np.clip(result, 0, 1)

def apply_rim_light(img_arr, params):
    """Rim light en bordes — solo añade en los extremos"""
    h, w = img_arr.shape[:2]
    rim_intensity = params["rim"]

    # Gradiente horizontal (bordes)
    x = np.arange(w, dtype=np.float32) / w
    rim_h = (np.exp(-x / 0.08) + np.exp(-(1 - x) / 0.08)) * rim_intensity
    # Gradiente vertical (top)
    y = np.arange(h, dtype=np.float32) / h
    rim_v = np.exp(-y / 0.12) * rim_intensity * 0.6

    rim = rim_h[np.newaxis, :] + rim_v[:, np.newaxis]
    rim = np.clip(rim, 0, 1)
    rim_3ch = np.stack([rim, rim, rim * 0.95], axis=-1)  # Ligeramente frío

    result = 1.0 - (1.0 - img_arr) * (1.0 - rim_3ch)
    return np.clip(result, 0, 1)

def apply_shadow(img_arr, params):
    """Sombra suave proyectada en esquina inferior-derecha"""
    h, w = img_arr.shape[:2]
    shadow_blur = params["shadow"]

    shadow_raw = make_gradient((w, h), cx=0.72, cy=0.82, radius=0.30, intensity=0.55)
    shadow_raw = 1.0 - shadow_raw  # invertir: oscuro en la zona

    # Aplicar como multiplicación sutil
    shadow_factor = shadow_raw * 0.12 + 0.88  # rango 0.88–1.0
    shadow_3ch = np.stack([shadow_factor, shadow_factor, shadow_factor], axis=-1)
    result = img_arr * shadow_3ch
    return np.clip(result, 0, 1)

def apply_warmth(img_arr, warmth):
    """Ajuste de temperatura de color"""
    if warmth == 0:
        return img_arr
    factor = warmth / 100.0
    result = img_arr.copy()
    if factor > 0:  # Calidez: más rojo/amarillo
        result[:, :, 0] = np.clip(result[:, :, 0] + factor * 0.08, 0, 1)
        result[:, :, 2] = np.clip(result[:, :, 2] - factor * 0.06, 0, 1)
    else:  # Frío: más azul
        result[:, :, 2] = np.clip(result[:, :, 2] - factor * 0.08, 0, 1)
        result[:, :, 0] = np.clip(result[:, :, 0] + factor * 0.06, 0, 1)
    return np.clip(result, 0, 1)

def add_film_grain(img_arr, intensity=0.025, seed=42):
    """Grano analógico para el preset Vintage"""
    np.random.seed(seed)
    grain = np.random.normal(0, intensity, img_arr.shape).astype(np.float32)
    return np.clip(img_arr + grain, 0, 1)

def simulate_lighting(base_img, setup_name, intensity_mult=1.0):
    """Pipeline completo de iluminación"""
    params = {k: (v * intensity_mult if isinstance(v, float) and k in ["key","fill","rim"] else v)
              for k, v in SETUPS[setup_name].items()}
    params["key"]  = min(params["key"],  0.95)
    params["fill"] = min(params["fill"], 0.90)
    params["rim"]  = min(params["rim"],  0.90)

    img = base_img.convert("RGB")
    if img.width > 1800:
        r = 1800 / img.width
        img = img.resize((1800, int(img.height * r)), Image.LANCZOS)

    arr = np.array(img, dtype=np.float32) / 255.0

    # Pipeline
    arr = apply_key_light(arr, params)
    arr = apply_fill_light(arr, params)
    arr = apply_rim_light(arr, params)
    arr = apply_shadow(arr, params)
    arr = apply_warmth(arr, params["warmth"])

    # Grano vintage
    if setup_name == "Vintage Film":
        arr = add_film_grain(arr, intensity=0.018)

    result = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8))
    result = ImageEnhance.Contrast(result).enhance(params["contrast"])
    result = ImageEnhance.Brightness(result).enhance(params["brightness"])
    if setup_name in ["Fashion Magazine", "Lookbook Model"]:
        result = ImageEnhance.Sharpness(result).enhance(1.12)

    return result

# ── UI ──────────────────────────────────────────────────────────────────────
col_conf, col_main = st.columns([1, 2])

with col_conf:
    st.markdown("## CONFIGURACIÓN")
    uploaded = st.file_uploader(
        "Sube el render / foto de prenda",
        type=["jpg", "jpeg", "png", "webp"]
    )

    setup = st.selectbox("Esquema de iluminación", list(SETUPS.keys()))

    info = SETUPS[setup]
    st.markdown(f"""
    <div style='background:#1a1a1a;border:1px solid #2c2c2c;border-radius:8px;
                padding:12px;margin:8px 0;font-size:0.8rem;color:#888;line-height:1.6;'>
    {info['desc']}<br><br>
    Luz principal: {'●' * int(info['key']*10)}{'○' * (10-int(info['key']*10))}<br>
    Relleno: {'●' * int(info['fill']*10)}{'○' * (10-int(info['fill']*10))}<br>
    Rim: {'●' * int(info['rim']*10)}{'○' * (10-int(info['rim']*10))}
    </div>
    """, unsafe_allow_html=True)

    intensity = st.slider("Intensidad global", 0.3, 1.5, 1.0, 0.05,
                          help="< 1.0 = más sutil  |  > 1.0 = más dramático")

with col_main:
    st.markdown("## PREVIEW")

    if uploaded:
        img_orig = Image.open(uploaded)

        with st.spinner("Aplicando iluminación de estudio..."):
            result = simulate_lighting(img_orig, setup, intensity_mult=intensity)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("<p style='color:#666;font-size:0.75rem;text-align:center;'>ORIGINAL</p>", unsafe_allow_html=True)
            st.image(img_orig, use_container_width=True)
        with col_b:
            st.markdown(f"<p style='color:#c8ff00;font-size:0.75rem;text-align:center;'>{setup.upper()}</p>", unsafe_allow_html=True)
            st.image(result, use_container_width=True)

        st.markdown("---")
        buf = io.BytesIO()
        result.save(buf, format="JPEG", quality=97)
        buf.seek(0)
        fname = f"ZZ_studio_{setup.lower().replace(' ','_')}.jpg"
        st.download_button(
            label=f"⬇️  DESCARGAR — {setup} (JPG 97%)",
            data=buf, file_name=fname, mime="image/jpeg"
        )

        # Comparativa múltiple
        st.markdown("---")
        st.markdown("## COMPARATIVA TODOS LOS SETUPS")
        if st.button("🔄 GENERAR COMPARATIVA (todos los esquemas)"):
            all_cols = st.columns(4)
            setup_list = list(SETUPS.keys())
            with st.spinner("Generando comparativa..."):
                for i, sname in enumerate(setup_list):
                    with all_cols[i % 4]:
                        r = simulate_lighting(img_orig, sname, intensity_mult=intensity)
                        st.image(r, caption=sname, use_container_width=True)
    else:
        st.markdown("""
        <div style='background:#161616;border:1px dashed #2c2c2c;border-radius:8px;
                    padding:60px;text-align:center;'>
        <p style='color:#444;font-size:2.5rem;'>💡</p>
        <p style='color:#666;font-size:0.85rem;'>Sube un render para aplicar iluminación de estudio</p>
        <p style='color:#444;font-size:0.75rem;'>Funciona mejor con fondo blanco o neutro</p>
        </div>
        """, unsafe_allow_html=True)

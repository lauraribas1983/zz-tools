#!/usr/bin/env python3
"""
ZZ · Texture Overlay Pro
Aplica textura de tela realista a renders planos
"""
import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw
import numpy as np
import io

st.set_page_config(page_title="ZZ Texture Overlay", page_icon="🧵", layout="wide")

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
    .tip-box { background:#1a1a1a; border:1px solid #2c2c2c; border-radius:8px;
               padding:12px 16px; margin:8px 0; font-size:0.8rem; color:#888; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🧵 ZZ · TEXTURE OVERLAY PRO")
st.markdown("<p style='color:#888;font-size:0.85rem;margin-top:-12px;'>Render plano → Textura tela ultra-realista · Denim · Seda · Lino · Lana · Terciopelo</p>", unsafe_allow_html=True)
st.markdown("---")

# ── Parámetros por tipo de tela ──
TELAS = {
    "Algodón ligero":  {"roughness": 0.12, "noise_scale": 0.8,  "sheen": 0.15, "blur": 1.2, "contrast": 1.05},
    "Algodón pesado":  {"roughness": 0.25, "noise_scale": 1.4,  "sheen": 0.10, "blur": 1.8, "contrast": 1.08},
    "Lino":            {"roughness": 0.38, "noise_scale": 2.0,  "sheen": 0.08, "blur": 2.2, "contrast": 1.12},
    "Lana fina":       {"roughness": 0.20, "noise_scale": 1.0,  "sheen": 0.20, "blur": 1.5, "contrast": 1.06},
    "Seda satinada":   {"roughness": 0.05, "noise_scale": 0.4,  "sheen": 0.55, "blur": 0.8, "contrast": 1.03},
    "Denim":           {"roughness": 0.42, "noise_scale": 2.5,  "sheen": 0.06, "blur": 2.5, "contrast": 1.15},
    "Terciopelo":      {"roughness": 0.30, "noise_scale": 1.6,  "sheen": 0.30, "blur": 2.0, "contrast": 1.10},
    "Punto jersey":    {"roughness": 0.22, "noise_scale": 1.2,  "sheen": 0.18, "blur": 1.6, "contrast": 1.07},
    "Popelín":         {"roughness": 0.15, "noise_scale": 0.9,  "sheen": 0.22, "blur": 1.3, "contrast": 1.05},
}

def generar_textura_tela(size, params, seed=42):
    """Genera mapa de textura sintética multi-escala"""
    np.random.seed(seed)
    w, h = size

    # Noise base
    noise_raw = np.random.randn(h, w).astype(np.float32)

    # Capa fina (detalle hilo)
    img_noise = Image.fromarray(((noise_raw + 3) / 6 * 255).clip(0,255).astype(np.uint8), 'L')
    fine = img_noise.filter(ImageFilter.GaussianBlur(radius=params["blur"] * 0.5))
    coarse = img_noise.filter(ImageFilter.GaussianBlur(radius=params["blur"] * 2.5))

    fine_arr = np.array(fine, dtype=np.float32) / 255.0
    coarse_arr = np.array(coarse, dtype=np.float32) / 255.0

    # Mezcla multi-escala
    ns = params["noise_scale"] / 3.0
    texture = fine_arr * (0.55 * ns) + coarse_arr * (0.45 * (1 - ns * 0.3))
    texture = np.clip(texture, 0, 1)

    # Normalizar con offset para no oscurecer demasiado
    texture = texture * 0.4 + 0.6  # rango 0.6–1.0 (no destruye el color)

    tex_img = Image.fromarray((texture * 255).astype(np.uint8), 'L')
    return tex_img

def agregar_sheen_seda(img, sheen_intensity):
    """Añade reflejos especulares para telas brillantes (seda, popelín...)"""
    if sheen_intensity < 0.15:
        return img
    w, h = img.size
    sheen_layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(sheen_layer)

    # Gradiente de luz diagonal (esquina superior izquierda)
    steps = 60
    for i in range(steps):
        alpha = int(sheen_intensity * 180 * (1 - i / steps))
        x1 = int(w * 0.05 + i * w * 0.01)
        y1 = int(h * 0.05 + i * h * 0.008)
        x2 = int(w * 0.55 - i * w * 0.005)
        y2 = int(h * 0.45 - i * h * 0.003)
        draw.ellipse([x1, y1, x2, y2], fill=(255, 255, 255, max(0, alpha)))

    sheen_blur = sheen_layer.filter(ImageFilter.GaussianBlur(radius=w // 12))
    base = img.convert('RGBA')
    return Image.alpha_composite(base, sheen_blur).convert('RGB')

def apply_texture_overlay(base_img, tela_nombre, intensity, seed=42):
    """Aplica textura completa a la imagen base"""
    params = TELAS[tela_nombre]
    img_rgb = base_img.convert('RGB')
    w, h = img_rgb.size

    # 1. Generar textura
    tex_gray = generar_textura_tela((w, h), params, seed=seed)

    # 2. Convertir a RGB y aplicar multiply blend
    tex_rgb = tex_gray.convert('RGB')
    base_arr = np.array(img_rgb, dtype=np.float32) / 255.0
    tex_arr  = np.array(tex_rgb, dtype=np.float32) / 255.0

    # Multiply blend
    multiplied = base_arr * tex_arr

    # Mezcla con intensidad
    blended = base_arr * (1.0 - intensity) + multiplied * intensity
    blended = np.clip(blended, 0, 1)
    result = Image.fromarray((blended * 255).astype(np.uint8))

    # 3. Sheen para telas brillantes
    result = agregar_sheen_seda(result, params["sheen"] * intensity)

    # 4. Polish final
    result = ImageEnhance.Sharpness(result).enhance(1.0 + 0.15 * intensity)
    result = ImageEnhance.Contrast(result).enhance(params["contrast"])

    return result

# ── UI ──────────────────────────────────────────────────────────────────────
col_conf, col_main = st.columns([1, 2])

with col_conf:
    st.markdown("## CONFIGURACIÓN")

    uploaded = st.file_uploader(
        "Sube el render / foto de prenda",
        type=["jpg", "jpeg", "png", "webp"]
    )

    tela = st.selectbox("Tipo de tela", list(TELAS.keys()))

    intensity = st.slider(
        "Intensidad de textura", 0.1, 1.0, 0.55, 0.05,
        help="0.1 = sutil  |  1.0 = máximo efecto"
    )

    seed_val = st.slider(
        "Variación de patrón", 1, 99, 42,
        help="Cambia el patrón de ruido sin tocar la intensidad"
    )

    st.markdown("---")
    st.markdown("## INFO TELA")
    params = TELAS[tela]
    st.markdown(f"""
    <div class='tip-box'>
    Rugosidad: {'●' * int(params['roughness']*10)}{'○' * (10 - int(params['roughness']*10))}<br>
    Brillo: {'●' * int(params['sheen']*10)}{'○' * (10 - int(params['sheen']*10))}<br>
    Escala textura: {'●' * int(params['noise_scale']/3*10)}{'○' * (10 - int(params['noise_scale']/3*10))}
    </div>
    """, unsafe_allow_html=True)

with col_main:
    st.markdown("## PREVIEW")

    if uploaded:
        img_orig = Image.open(uploaded)
        if img_orig.width > 1800:
            img_orig = img_orig.resize(
                (1800, int(1800 * img_orig.height / img_orig.width)),
                Image.LANCZOS
            )

        with st.spinner("Aplicando textura..."):
            result = apply_texture_overlay(img_orig, tela, intensity, seed=seed_val)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("<p style='color:#666;font-size:0.75rem;text-align:center;'>ORIGINAL</p>", unsafe_allow_html=True)
            st.image(img_orig, use_container_width=True)
        with col_b:
            st.markdown(f"<p style='color:#c8ff00;font-size:0.75rem;text-align:center;'>CON TEXTURA · {tela.upper()}</p>", unsafe_allow_html=True)
            st.image(result, use_container_width=True)

        st.markdown("---")
        buf = io.BytesIO()
        result.save(buf, format="JPEG", quality=95)
        buf.seek(0)
        fname = f"ZZ_texture_{tela.lower().replace(' ','_')}.jpg"
        st.download_button(
            label=f"⬇️  DESCARGAR — {tela} (JPG 95%)",
            data=buf,
            file_name=fname,
            mime="image/jpeg"
        )
    else:
        st.markdown("""
        <div style='background:#161616;border:1px dashed #2c2c2c;border-radius:8px;
                    padding:60px;text-align:center;'>
        <p style='color:#444;font-size:2.5rem;'>🧵</p>
        <p style='color:#666;font-size:0.85rem;'>Sube un render de prenda para empezar</p>
        <p style='color:#444;font-size:0.75rem;'>JPG · PNG · WEBP · hasta 200MB</p>
        </div>
        """, unsafe_allow_html=True)

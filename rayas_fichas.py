#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  ZZ RAYAS & FICHAS GENERATOR — Zig Zag Studio                    ║
║  Generador interactivo de fichas de rayas con preview en vivo    ║
╚══════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import io
import os
import zipfile
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

import numpy as np

# ──────────────────────────────────────────────────────────────────
#  CONFIG PÁGINA
# ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ZZ Rayas & Fichas",
    page_icon="🧵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────────────────────────
#  ESTILOS
# ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background: #0f0f0f; color: #e8e8e8; }
    .main .block-container { padding: 1.5rem 2rem; max-width: 1600px; }
    h1 { color: #FFD700 !important; font-size: 1.6rem !important; letter-spacing: 2px; }
    h2, h3 { color: #e8e8e8 !important; }
    .stButton>button {
        background: #1a1a1a; color: #e8e8e8; border: 1px solid #333;
        border-radius: 4px; width: 100%; margin: 2px 0;
    }
    .stButton>button:hover { background: #FFD700; color: #000; }
    .download-btn>button { background: #FFD700 !important; color: #000 !important;
        font-weight: bold; font-size: 1rem; padding: 0.6rem; }
    .stripe-row {
        background: #1a1a1a; border: 1px solid #2a2a2a;
        border-radius: 6px; padding: 8px; margin: 4px 0;
    }
    .preview-container { background: #1a1a1a; border-radius: 8px; padding: 1rem; }
    .stat-box {
        background: #1a1a1a; border: 1px solid #FFD700;
        border-radius: 6px; padding: 8px 12px; text-align: center;
    }
    .pantone-chip {
        display: inline-block; width: 24px; height: 24px;
        border: 1px solid #555; border-radius: 3px; vertical-align: middle;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────
#  PANTONE DATABASE
# ──────────────────────────────────────────────────────────────────
PANTONE_DB = {
    # Neutros
    "19-0303": ("#1A1A1A", "Black"),
    "11-0601": ("#F5F1E8", "Off White"),
    "11-4001": ("#EFE9DA", "Whisper White"),
    "11-0602": ("#F8F4E8", "Cream"),
    "17-0000": ("#808080", "Med Gray"),
    "18-0201": ("#A0A0A0", "Light Gray"),
    "13-0002": ("#F2EDE4", "Stone"),
    "14-1118": ("#D4B896", "Sand"),
    "12-0108": ("#F5EDD7", "Buttercream"),
    # Clásicos ZZ
    "19-4034": ("#00205B", "Navy Blazer"),
    "19-4024": ("#002E6E", "Navy Deep"),
    "19-4040": ("#00205B", "Navy Dark"),
    "19-1724": ("#72202B", "Burgundy"),
    "19-1664": ("#C41E3A", "True Red"),
    "18-1650": ("#CC0000", "Sport Red"),
    "19-1758": ("#6B1F27", "Bordo Red"),
    "19-1606": ("#5C3042", "Burgundy Dark"),
    "19-1620": ("#6E2233", "Burdeos Oscuro"),
    "14-0846": ("#F4C430", "Yellow"),
    "13-0858": ("#FFD700", "Sport Yellow"),
    "17-4041": ("#4169E1", "Royal Blue"),
    "19-3720": ("#4B0082", "Purple"),
    # Tendencia 2026
    "16-1438": ("#C17B5B", "Terracotta"),
    "15-3817": ("#B4A7D6", "Lavender"),
    "16-0430": ("#8FA882", "Sage Green"),
    "12-0712": ("#F0E6C4", "Warm Ivory"),
    "17-3911": ("#9EA0A8", "Blue Slate"),
    "14-1513": ("#ECC9B8", "Rosa Nude"),
    "18-1048": ("#B5692E", "Naranja Quemado"),
    "19-4150": ("#1A5276", "Azul Cobalto"),
    "19-0315": ("#4A5E41", "Verde Musgo"),
    "13-4411": ("#D6E4E8", "Sky Blue"),
    "17-0535": ("#5A8A5A", "Forest Green"),
    "16-1610": ("#D4A5A5", "Dusty Rose"),
}

# ──────────────────────────────────────────────────────────────────
#  PRESETS DE COLORES
# ──────────────────────────────────────────────────────────────────
PRESETS_COLORES = {
    "Navy + Crema (Clásico ZZ)": [
        {"hex": "#00205B", "pantone": "19-4034", "nombre": "Navy Blazer", "ancho": 2.0},
        {"hex": "#EFE9DA", "pantone": "11-4001", "nombre": "Whisper White", "ancho": 2.5},
    ],
    "Tricolor ZZ (Navy·Cream·Burgundy)": [
        {"hex": "#00205B", "pantone": "19-4034", "nombre": "Navy Blazer", "ancho": 2.0},
        {"hex": "#EFE9DA", "pantone": "11-4001", "nombre": "Whisper White", "ancho": 1.5},
        {"hex": "#72202B", "pantone": "19-1724", "nombre": "Burgundy", "ancho": 1.0},
    ],
    "Breton Clásico (Navy·Blanco)": [
        {"hex": "#00205B", "pantone": "19-4034", "nombre": "Navy Blazer", "ancho": 1.5},
        {"hex": "#F5F1E8", "pantone": "11-0601", "nombre": "Off White", "ancho": 2.0},
    ],
    "Negro + Blanco": [
        {"hex": "#1A1A1A", "pantone": "19-0303", "nombre": "Black", "ancho": 1.5},
        {"hex": "#F5F1E8", "pantone": "11-0601", "nombre": "Off White", "ancho": 1.5},
    ],
    "Rojo + Blanco (Sport)": [
        {"hex": "#CC0000", "pantone": "18-1650", "nombre": "Sport Red", "ancho": 2.0},
        {"hex": "#F5F1E8", "pantone": "11-0601", "nombre": "Off White", "ancho": 2.0},
    ],
    "Terracotta SS26": [
        {"hex": "#C17B5B", "pantone": "16-1438", "nombre": "Terracotta", "ancho": 2.5},
        {"hex": "#F0E6C4", "pantone": "12-0712", "nombre": "Warm Ivory", "ancho": 2.0},
    ],
    "Multicolor Varsity": [
        {"hex": "#00205B", "pantone": "19-4034", "nombre": "Navy Blazer", "ancho": 1.5},
        {"hex": "#EFE9DA", "pantone": "11-4001", "nombre": "Whisper White", "ancho": 0.5},
        {"hex": "#72202B", "pantone": "19-1724", "nombre": "Burgundy", "ancho": 0.8},
        {"hex": "#EFE9DA", "pantone": "11-4001", "nombre": "Whisper White", "ancho": 0.5},
        {"hex": "#00205B", "pantone": "19-4034", "nombre": "Navy Blazer", "ancho": 1.0},
    ],
}

# ──────────────────────────────────────────────────────────────────
#  PRESETS DE RAPORT (CONFIGURACIONES DE RAYAS)
# ──────────────────────────────────────────────────────────────────
PRESETS_RAPORT = {
    "Marinière Clásica (2.0+2.5cm)": [
        {"hex": "#00205B", "pantone": "19-4034", "nombre": "Navy Blazer", "ancho": 2.0},
        {"hex": "#EFE9DA", "pantone": "11-4001", "nombre": "Whisper White", "ancho": 2.5},
    ],
    "Tricolor Equilibrado (1.5+1.5+1.5cm)": [
        {"hex": "#00205B", "pantone": "19-4034", "nombre": "Navy Blazer", "ancho": 1.5},
        {"hex": "#72202B", "pantone": "19-1724", "nombre": "Burgundy", "ancho": 1.5},
        {"hex": "#EFE9DA", "pantone": "11-4001", "nombre": "Whisper White", "ancho": 1.5},
    ],
    "Tricolor Navy Dom. (0.8+1.2+2.5cm)": [
        {"hex": "#EFE9DA", "pantone": "11-4001", "nombre": "Whisper White", "ancho": 0.8},
        {"hex": "#72202B", "pantone": "19-1724", "nombre": "Burgundy", "ancho": 1.2},
        {"hex": "#00205B", "pantone": "19-4034", "nombre": "Navy Blazer", "ancho": 2.5},
    ],
    "Pinstripe Fino (0.2+1.8cm)": [
        {"hex": "#1A1A1A", "pantone": "19-0303", "nombre": "Black", "ancho": 0.2},
        {"hex": "#F5F1E8", "pantone": "11-0601", "nombre": "Off White", "ancho": 1.8},
    ],
    "Rayas Anchas (3.0+3.0cm)": [
        {"hex": "#00205B", "pantone": "19-4034", "nombre": "Navy Blazer", "ancho": 3.0},
        {"hex": "#EFE9DA", "pantone": "11-4001", "nombre": "Whisper White", "ancho": 3.0},
    ],
}

# ──────────────────────────────────────────────────────────────────
#  UTILIDADES
# ──────────────────────────────────────────────────────────────────
def hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip('#')
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

def rgb_to_hex(rgb: tuple) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)

def get_pantone_name(pantone_code: str) -> tuple:
    clean = pantone_code.upper().replace(" TCX","").replace(" TPG","").strip()
    if clean in PANTONE_DB:
        return PANTONE_DB[clean]
    return (None, pantone_code)

@st.cache_data
def load_garment_template():
    """Carga el template de prenda. Busca en varias ubicaciones."""
    search_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "garment_template.png"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "garment_template.png"),
        "/sessions/hopeful-practical-curie/mnt/claude/ZZ_AI_V2/garment_template.png",
    ]
    for p in search_paths:
        if os.path.exists(p):
            return Image.open(p).convert("RGBA")
    return None

def load_fonts_for_size(px_per_cm: float) -> dict:
    serif_candidates = [
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
    ]
    sans_candidates = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    fonts = {}
    default = ImageFont.load_default()
    for fp in serif_candidates:
        if os.path.exists(fp):
            fonts['logo_main'] = ImageFont.truetype(fp, max(8, int(px_per_cm * 0.58)))
            fonts['logo_sub']  = ImageFont.truetype(fp, max(6, int(px_per_cm * 0.28)))
            break
    for fp in sans_candidates:
        if os.path.exists(fp):
            fonts['title']  = ImageFont.truetype(fp, max(8, int(px_per_cm * 0.45)))
            fonts['small']  = ImageFont.truetype(fp, max(6, int(px_per_cm * 0.30)))
            fonts['tiny']   = ImageFont.truetype(fp, max(5, int(px_per_cm * 0.24)))
            fonts['raport'] = ImageFont.truetype(fp, max(5, int(px_per_cm * 0.22)))
            break
    for key in ('logo_main', 'logo_sub', 'title', 'small', 'tiny', 'raport'):
        if key not in fonts:
            fonts[key] = default
    return fonts

def draw_zz_logo(draw, fonts, x, y, color=(25,25,25)):
    draw.text((x, y), "zig·zag", font=fonts['logo_main'], fill=color)
    try:
        bb = draw.textbbox((x, y), "zig·zag", font=fonts['logo_main'])
        mw = bb[2]-bb[0]; mh = bb[3]-bb[1]
        sb = draw.textbbox((x, y), "STUDIO", font=fonts['logo_sub'])
        sw = sb[2]-sb[0]
        draw.text((x+(mw-sw)//2, y+mh+1), "STUDIO", font=fonts['logo_sub'], fill=color)
    except:
        pass

def make_stripe_image(rayas: list, orientation: str, width: int, height: int, px_per_cm: float) -> Image.Image:
    """Genera imagen de rayas seamless."""
    total_cm = sum(r['ancho'] for r in rayas)
    if total_cm <= 0:
        return Image.new("RGB", (width, height), (200,200,200))
    total_px = total_cm * px_per_cm

    if orientation == "horizontal":
        coords = np.arange(height, dtype=np.float64)
        pos = coords % total_px
        arr = np.zeros((height, 3), dtype=np.uint8)
        acc = 0.0
        for r in rayas:
            end = acc + r['ancho'] * px_per_cm
            rgb = hex_to_rgb(r['hex'])
            mask = (pos >= acc) & (pos < end)
            arr[mask] = rgb
            acc = end
        arr[pos >= acc] = hex_to_rgb(rayas[-1]['hex'])
        img_arr = np.broadcast_to(arr[:, np.newaxis, :], (height, width, 3))
        return Image.fromarray(np.ascontiguousarray(img_arr), "RGB")
    else:  # vertical
        coords = np.arange(width, dtype=np.float64)
        pos = coords % total_px
        arr = np.zeros((width, 3), dtype=np.uint8)
        acc = 0.0
        for r in rayas:
            end = acc + r['ancho'] * px_per_cm
            rgb = hex_to_rgb(r['hex'])
            mask = (pos >= acc) & (pos < end)
            arr[mask] = rgb
            acc = end
        arr[pos >= acc] = hex_to_rgb(rayas[-1]['hex'])
        img_arr = np.broadcast_to(arr[np.newaxis, :, :], (height, width, 3))
        return Image.fromarray(np.ascontiguousarray(img_arr), "RGB")

# ──────────────────────────────────────────────────────────────────
#  GENERAR PATRÓN (página full-bleed)
# ──────────────────────────────────────────────────────────────────
def generate_patron(rayas: list, orientation: str, dpi: int = 150,
                    nombre_variante: str = "") -> Image.Image:
    px = dpi / 2.54
    DOC_W = int(29.7 * px)
    DOC_H = int(21.0 * px)
    STRIP = int(1.5 * px)

    stripe = make_stripe_image(rayas, orientation, DOC_W, DOC_H - STRIP, px)
    page = Image.new("RGB", (DOC_W, DOC_H), (255,255,255))
    page.paste(stripe, (0, 0))

    draw = ImageDraw.Draw(page)
    fonts = load_fonts_for_size(px)

    # Logo esquina inferior derecha
    logo_x = DOC_W - int(3.8 * px)
    logo_y = DOC_H - STRIP + int(0.18 * px)
    draw_zz_logo(draw, fonts, logo_x, logo_y)

    # Nombre variante — esquina inferior izquierda
    if nombre_variante:
        draw.text((int(0.5*px), DOC_H - STRIP + int(0.25*px)),
                  nombre_variante.upper(), font=fonts['small'], fill=(80,80,80))

    # Info raport
    raport = sum(r['ancho'] for r in rayas)
    draw.text((int(0.5*px), DOC_H - STRIP + int(0.65*px)),
              f"Raport: {raport:.2f} cm  ·  {orientation}",
              font=fonts['raport'], fill=(140,140,140))
    return page

# ──────────────────────────────────────────────────────────────────
#  GENERAR FICHA COMPLETA
# ──────────────────────────────────────────────────────────────────
def generate_ficha(rayas: list, orientation: str, nombre_variante: str,
                   ref_texto: str = "", dpi: int = 150,
                   garment_tmpl: Image.Image = None) -> Image.Image:
    px = dpi / 2.54
    DOC_W    = int(29.7 * px)
    DOC_H    = int(21.0 * px)
    HEADER_H = int(2.8 * px)
    BODY_Y   = HEADER_H
    BODY_H   = DOC_H - HEADER_H
    LEFT_W   = int(DOC_W * 0.44)
    RIGHT_X  = LEFT_W
    RIGHT_W  = DOC_W - LEFT_W
    MARGIN   = int(0.55 * px)

    page = Image.new("RGB", (DOC_W, DOC_H), (255,255,255))
    draw = ImageDraw.Draw(page)
    fonts = load_fonts_for_size(px)

    # ── CABECERA ──────────────────────────────────────────────────
    # Línea negra superior
    draw.rectangle([(0, 0), (DOC_W, int(0.12*px))], fill=(20,20,20))

    # Logo ZZ izquierda
    draw_zz_logo(draw, fonts, MARGIN, int(0.45*px))

    # Nombre variante centrado
    vname = nombre_variante.upper() if nombre_variante else "VARIANTE SIN NOMBRE"
    try:
        nb = draw.textbbox((0,0), vname, font=fonts['title'])
        nw = nb[2]-nb[0]
        draw.text(((DOC_W-nw)//2, int(1.0*px)), vname, font=fonts['title'], fill=(20,20,20))
    except:
        draw.text((DOC_W//2-80, int(1.0*px)), vname, font=fonts['title'], fill=(20,20,20))

    # Ref debajo del nombre
    if ref_texto:
        try:
            rb = draw.textbbox((0,0), ref_texto, font=fonts['small'])
            rw = rb[2]-rb[0]
            draw.text(((DOC_W-rw)//2, int(1.7*px)), ref_texto, font=fonts['small'], fill=(100,100,100))
        except:
            pass

    # Chips Pantone — derecha
    unique_colors = []
    seen = set()
    for r in rayas:
        key = r['hex'].upper()
        if key not in seen:
            seen.add(key)
            unique_colors.append(r)

    CHIP_SIZE = int(0.88 * px)
    CHIP_GAP  = int(0.30 * px)
    CHIP_Y0   = int(0.40 * px)
    total_w = len(unique_colors) * (CHIP_SIZE + CHIP_GAP) - CHIP_GAP
    chip_x0 = DOC_W - MARGIN - total_w

    for i, r in enumerate(unique_colors):
        cx = chip_x0 + i * (CHIP_SIZE + CHIP_GAP)
        rgb = hex_to_rgb(r['hex'])
        draw.rectangle([cx, CHIP_Y0, cx+CHIP_SIZE, CHIP_Y0+CHIP_SIZE],
                       fill=rgb, outline=(160,160,160), width=1)
        # Texto Pantone
        p_code = r.get('pantone','')
        p_name = r.get('nombre','')
        ty1 = CHIP_Y0 + CHIP_SIZE + 3
        ty2 = ty1 + int(0.28 * px)
        if p_code:
            draw.text((cx, ty1), p_code+" TCX", font=fonts['tiny'], fill=(55,55,55))
        if p_name:
            draw.text((cx, ty2), p_name, font=fonts['tiny'], fill=(100,100,100))

    # Línea separadora cabecera
    draw.line([(0, HEADER_H), (DOC_W, HEADER_H)], fill=(200,200,200), width=1)

    # ── CUERPO ────────────────────────────────────────────────────
    stripe_full = make_stripe_image(rayas, orientation, DOC_W, BODY_H, px)

    # Panel DERECHO: swatch del patrón
    right_crop = stripe_full.crop((0, 0, RIGHT_W, BODY_H))
    page.paste(right_crop, (RIGHT_X, BODY_Y))

    # Línea divisoria
    draw.line([(LEFT_W, BODY_Y), (LEFT_W, DOC_H)], fill=(180,180,180), width=1)

    # Panel IZQUIERDO: prenda con patrón
    if garment_tmpl is not None:
        try:
            PAD = int(0.8 * px)
            max_w = LEFT_W - PAD * 2
            max_h = BODY_H - int(1.0 * px)
            tw, th = garment_tmpl.size
            scale = min(max_w/tw, max_h/th)
            nw, nh = int(tw*scale), int(th*scale)
            tmpl = garment_tmpl.resize((nw, nh), Image.LANCZOS)
            cam_x = (LEFT_W - nw) // 2
            cam_y = BODY_Y + (BODY_H - nh) // 2

            stripe_g = make_stripe_image(rayas, orientation, nw, nh, px)
            s_arr = np.array(stripe_g)
            t_arr = np.array(tmpl)

            alpha    = t_arr[:,:,3]
            rgb_mean = t_arr[:,:,:3].astype(float).mean(axis=2)
            is_vis   = alpha > 10
            is_out   = is_vis & (rgb_mean <= 130)  # contorno oscuro
            is_int   = is_vis & ~is_out             # interior claro

            res = np.zeros((nh, nw, 4), dtype=np.uint8)
            res[is_int, :3] = s_arr[is_int]
            res[is_int, 3]  = 255
            res[is_out, :3] = t_arr[is_out, :3]
            res[is_out, 3]  = 255
            garment_img = Image.fromarray(res, "RGBA")
            page.paste(garment_img, (cam_x, cam_y), garment_img)
        except Exception as e:
            # Si falla el template, panel vacío con mensaje
            draw.text((MARGIN, BODY_Y + int(4*px)),
                      "Template error", font=fonts['small'], fill=(200,100,100))

    # Info raport — pie izquierdo
    raport = sum(r['ancho'] for r in rayas)
    n_col = len(unique_colors)
    draw.text((MARGIN, DOC_H - int(0.58*px)),
              f"Raport: {raport:.2f} cm  ·  {n_col} colores  ·  {orientation}",
              font=fonts['raport'], fill=(150,150,150))

    return page

# ──────────────────────────────────────────────────────────────────
#  PREVIEW RÁPIDA (pequeña, para sidebar)
# ──────────────────────────────────────────────────────────────────
def make_preview_strip(rayas: list, orientation: str,
                        width: int = 600, height: int = 120) -> Image.Image:
    if not rayas:
        return Image.new("RGB", (width, height), (30,30,30))
    return make_stripe_image(rayas, orientation, width, height, height/10)

# ──────────────────────────────────────────────────────────────────
#  INICIALIZAR SESSION STATE
# ──────────────────────────────────────────────────────────────────
def init_state():
    if 'rayas' not in st.session_state:
        # Preset por defecto: Marinière Clásica ZZ
        st.session_state['rayas'] = [
            {"hex": "#00205B", "pantone": "19-4034", "nombre": "Navy Blazer", "ancho": 2.0},
            {"hex": "#EFE9DA", "pantone": "11-4001", "nombre": "Whisper White", "ancho": 2.5},
        ]
    if 'orientacion' not in st.session_state:
        st.session_state['orientacion'] = "horizontal"
    if 'nombre_variante' not in st.session_state:
        st.session_state['nombre_variante'] = "Marinière Clásica"
    if 'ref_texto' not in st.session_state:
        st.session_state['ref_texto'] = ""
    if 'dpi' not in st.session_state:
        st.session_state['dpi'] = 150

init_state()

# ──────────────────────────────────────────────────────────────────
#  HEADER
# ──────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-bottom: 2px solid #FFD700; padding-bottom: 8px; margin-bottom: 16px;">
  <span style="color:#FFD700; font-size:1.5rem; font-weight:700; letter-spacing:3px;">ZZ</span>
  <span style="color:#888; font-size:1.1rem; margin-left:8px;">RAYAS & FICHAS GENERATOR</span>
  <span style="float:right; color:#555; font-size:0.8rem;">Zig Zag Studio · v3.0</span>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────
#  LAYOUT: sidebar (configuración) + main (preview + export)
# ──────────────────────────────────────────────────────────────────

# SIDEBAR ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuración")

    # PRESET RAPORT
    st.markdown("**Presets rápidos:**")
    preset_name = st.selectbox("Cargar preset", ["— personalizado —"] + list(PRESETS_RAPORT.keys()),
                               label_visibility="collapsed")
    if preset_name != "— personalizado —":
        if st.button("✓ Cargar preset", use_container_width=True):
            st.session_state['rayas'] = [dict(r) for r in PRESETS_RAPORT[preset_name]]
            st.session_state['nombre_variante'] = preset_name.split("(")[0].strip()
            st.rerun()

    st.divider()

    # NOMBRE Y REF
    st.session_state['nombre_variante'] = st.text_input(
        "📝 Nombre variante", st.session_state['nombre_variante'])
    st.session_state['ref_texto'] = st.text_input(
        "🏷️ Ref / Temporada", st.session_state['ref_texto'],
        placeholder="Ej: ZZ-2026-001 · SS26")

    # ORIENTACIÓN
    ori = st.radio("↕️ Orientación", ["horizontal", "vertical"],
                   index=0 if st.session_state['orientacion']=="horizontal" else 1,
                   horizontal=True)
    st.session_state['orientacion'] = ori

    # RESOLUCIÓN
    dpi_opt = st.select_slider("🖨️ Resolución",
                                options=[72, 150, 300],
                                value=st.session_state['dpi'])
    st.session_state['dpi'] = dpi_opt
    dpi_labels = {72: "Preview rápido", 150: "Prueba/pantalla", 300: "Producción print"}
    st.caption(f"→ {dpi_labels.get(dpi_opt,'')}")

    st.divider()

    # TEMPLATE PRENDA
    st.markdown("**🎽 Plantilla prenda:**")
    tmpl_option = st.radio("", ["garment_template.png (default)", "Subir PNG propio", "Sin silueta"],
                           label_visibility="collapsed")
    uploaded_tmpl = None
    if tmpl_option == "Subir PNG propio":
        uploaded_tmpl = st.file_uploader("PNG con transparencia (RGBA)", type=["png"],
                                          label_visibility="collapsed")
    garment_tmpl = None
    if tmpl_option == "garment_template.png (default)":
        garment_tmpl = load_garment_template()
        if garment_tmpl is None:
            st.warning("⚠️ garment_template.png no encontrado")
    elif tmpl_option == "Subir PNG propio" and uploaded_tmpl:
        garment_tmpl = Image.open(uploaded_tmpl).convert("RGBA")
        st.success("✅ Template cargado")

    # INFO RAPORT
    st.divider()
    rayas_actual = st.session_state['rayas']
    if rayas_actual:
        raport_total = sum(r['ancho'] for r in rayas_actual)
        n_col = len(set(r['hex'].upper() for r in rayas_actual))
        cols_s = st.columns(2)
        with cols_s[0]:
            st.markdown(f'<div class="stat-box"><div style="font-size:1.3rem;color:#FFD700;">{raport_total:.1f}<span style="font-size:0.7rem">cm</span></div><div style="font-size:0.7rem;color:#888;">raport</div></div>', unsafe_allow_html=True)
        with cols_s[1]:
            st.markdown(f'<div class="stat-box"><div style="font-size:1.3rem;color:#FFD700;">{n_col}</div><div style="font-size:0.7rem;color:#888;">colores</div></div>', unsafe_allow_html=True)

# ÁREA PRINCIPAL ───────────────────────────────────────────────────
col_config, col_preview = st.columns([1, 1.3], gap="large")

# ── COLUMNA IZQUIERDA: configuración de rayas ──────────────────────
with col_config:
    st.markdown("### 🎨 Rayas")

    # Preset de colores
    preset_c = st.selectbox("Preset colores", ["— sin preset —"] + list(PRESETS_COLORES.keys()),
                             key="preset_col")
    if preset_c != "— sin preset —":
        if st.button("↓ Aplicar colores del preset"):
            st.session_state['rayas'] = [dict(r) for r in PRESETS_COLORES[preset_c]]
            st.rerun()

    st.markdown("---")

    # Lista de rayas
    rayas = st.session_state['rayas']
    rayas_to_delete = []

    for i, raya in enumerate(rayas):
        with st.container():
            st.markdown(f'<div style="background:#1a1a1a;border-left:4px solid {raya["hex"]};padding:8px 10px;border-radius:4px;margin:4px 0;">', unsafe_allow_html=True)
            rc1, rc2, rc3, rc4 = st.columns([0.5, 1.5, 1.2, 0.5])
            with rc1:
                # Color picker
                new_hex = st.color_picker("", raya['hex'], key=f"cp_{i}", label_visibility="collapsed")
                if new_hex != raya['hex']:
                    rayas[i]['hex'] = new_hex
            with rc2:
                # Código Pantone
                new_pantone = st.text_input("Pantone", raya.get('pantone',''),
                                             key=f"pt_{i}", placeholder="19-4034 TCX",
                                             label_visibility="collapsed")
                if new_pantone != raya.get('pantone',''):
                    rayas[i]['pantone'] = new_pantone
                    hex_from_db, name_from_db = get_pantone_name(new_pantone)
                    if hex_from_db:
                        rayas[i]['hex'] = hex_from_db
                        rayas[i]['nombre'] = name_from_db
            with rc3:
                new_ancho = st.number_input("cm", min_value=0.05, max_value=20.0,
                                             value=float(raya['ancho']), step=0.1,
                                             key=f"an_{i}", format="%.2f",
                                             label_visibility="collapsed")
                rayas[i]['ancho'] = new_ancho
            with rc4:
                if st.button("✕", key=f"del_{i}", help="Eliminar raya"):
                    rayas_to_delete.append(i)
            # Nombre del color
            new_nombre = st.text_input("Nombre", raya.get('nombre',''),
                                        key=f"nm_{i}", placeholder="Navy Blazer",
                                        label_visibility="collapsed")
            rayas[i]['nombre'] = new_nombre
            st.markdown('</div>', unsafe_allow_html=True)

    # Eliminar rayas marcadas (en orden inverso)
    for idx in sorted(rayas_to_delete, reverse=True):
        rayas.pop(idx)
    st.session_state['rayas'] = rayas

    # Botones añadir
    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button("➕ Añadir raya", use_container_width=True):
            st.session_state['rayas'].append({
                "hex": "#FFFFFF", "pantone": "", "nombre": "Nuevo color", "ancho": 1.0
            })
            st.rerun()
    with bc2:
        if st.button("🔄 Duplicar patrón", use_container_width=True,
                     help="Añade una copia del patrón actual (para patrones con simetría)"):
            st.session_state['rayas'] = [dict(r) for r in st.session_state['rayas']] * 2
            st.rerun()

    # Tabla de resumen
    if rayas:
        st.markdown("---")
        st.markdown("**Resumen del raport:**")
        total = sum(r['ancho'] for r in rayas)
        for r in rayas:
            pct = (r['ancho'] / total * 100) if total > 0 else 0
            bar_w = int(pct * 1.5)
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;margin:2px 0;">'
                f'<div style="width:16px;height:16px;background:{r["hex"]};border:1px solid #444;border-radius:2px;flex-shrink:0;"></div>'
                f'<div style="font-size:0.78rem;color:#ccc;flex:1;">{r.get("nombre","") or r["hex"]}</div>'
                f'<div style="font-size:0.78rem;color:#FFD700;">{r["ancho"]:.2f}cm</div>'
                f'<div style="font-size:0.75rem;color:#666;">{pct:.0f}%</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        st.markdown(f'<div style="color:#888;font-size:0.8rem;margin-top:4px;">Total raport: **{total:.2f} cm**</div>', unsafe_allow_html=True)


# ── COLUMNA DERECHA: preview y export ─────────────────────────────
with col_preview:
    st.markdown("### 👁️ Preview")

    rayas_curr = st.session_state['rayas']
    ori_curr   = st.session_state['orientacion']
    nombre_curr = st.session_state['nombre_variante']
    ref_curr   = st.session_state['ref_texto']
    dpi_curr   = st.session_state['dpi']

    tab1, tab2, tab3 = st.tabs(["🎨 Patrón", "📋 Ficha completa", "📦 Exportar todo"])

    with tab1:
        if rayas_curr:
            with st.spinner("Generando patrón..."):
                patron_img = generate_patron(rayas_curr, ori_curr, dpi_curr, nombre_curr)
                # Escalar para preview
                pw, ph = patron_img.size
                max_preview = 900
                if pw > max_preview:
                    scale = max_preview / pw
                    patron_img_prev = patron_img.resize((max_preview, int(ph*scale)), Image.LANCZOS)
                else:
                    patron_img_prev = patron_img
                st.image(patron_img_prev, use_container_width=True,
                         caption=f"PATRÓN · {nombre_curr} · {dpi_curr}dpi")

                # Download
                buf = io.BytesIO()
                patron_img.save(buf, "PNG", dpi=(dpi_curr, dpi_curr))
                st.download_button(
                    "⬇️ Descargar PATRÓN (PNG)",
                    data=buf.getvalue(),
                    file_name=f"ZZ_patron_{nombre_curr.replace(' ','_')}.png",
                    mime="image/png",
                    use_container_width=True
                )

    with tab2:
        if rayas_curr:
            with st.spinner("Generando ficha..."):
                ficha_img = generate_ficha(rayas_curr, ori_curr, nombre_curr,
                                           ref_curr, dpi_curr, garment_tmpl)
                fw, fh = ficha_img.size
                max_p2 = 900
                if fw > max_p2:
                    scale2 = max_p2 / fw
                    ficha_prev = ficha_img.resize((max_p2, int(fh*scale2)), Image.LANCZOS)
                else:
                    ficha_prev = ficha_img
                st.image(ficha_prev, use_container_width=True,
                         caption=f"FICHA · {nombre_curr} · {dpi_curr}dpi")

                buf2 = io.BytesIO()
                ficha_img.save(buf2, "PNG", dpi=(dpi_curr, dpi_curr))
                st.download_button(
                    "⬇️ Descargar FICHA (PNG)",
                    data=buf2.getvalue(),
                    file_name=f"ZZ_ficha_{nombre_curr.replace(' ','_')}.png",
                    mime="image/png",
                    use_container_width=True
                )

    with tab3:
        st.markdown("**Exportar PDF completo con todas las páginas:**")

        variantes_export = []
        st.markdown("Genera múltiples variantes cambiando el preset y añadiéndolas aquí:")

        if 'export_variants' not in st.session_state:
            st.session_state['export_variants'] = []

        col_e1, col_e2 = st.columns(2)
        with col_e1:
            if st.button("➕ Añadir variante actual", use_container_width=True):
                st.session_state['export_variants'].append({
                    'nombre': nombre_curr or f"Variante {len(st.session_state['export_variants'])+1}",
                    'rayas': [dict(r) for r in rayas_curr],
                    'orientacion': ori_curr,
                    'ref': ref_curr,
                })
                st.success(f"✅ Añadida: {nombre_curr}")
        with col_e2:
            if st.button("🗑️ Limpiar lista", use_container_width=True):
                st.session_state['export_variants'] = []
                st.rerun()

        if st.session_state['export_variants']:
            st.markdown(f"**{len(st.session_state['export_variants'])} variante(s) en cola:**")
            for i, v in enumerate(st.session_state['export_variants']):
                raport_v = sum(r['ancho'] for r in v['rayas'])
                col_v1, col_v2 = st.columns([3, 1])
                with col_v1:
                    st.markdown(f"  `{i+1}.` **{v['nombre']}** · raport {raport_v:.1f}cm")
                with col_v2:
                    if st.button("✕", key=f"rm_v_{i}"):
                        st.session_state['export_variants'].pop(i)
                        st.rerun()

            st.divider()
            tipo_export = st.radio("Tipo PDF:", ["Solo Fichas", "Solo Patrones", "Completo (Patrón+Ficha)"], horizontal=True)

            if st.button("🖨️ GENERAR PDF COMPLETO", use_container_width=True, type="primary"):
                with st.spinner(f"Generando PDF con {len(st.session_state['export_variants'])} variantes..."):
                    all_imgs = []
                    for v in st.session_state['export_variants']:
                        if tipo_export in ["Solo Patrones", "Completo (Patrón+Ficha)"]:
                            all_imgs.append(generate_patron(v['rayas'], v['orientacion'], dpi_curr, v['nombre']))
                        if tipo_export in ["Solo Fichas", "Completo (Patrón+Ficha)"]:
                            all_imgs.append(generate_ficha(v['rayas'], v['orientacion'], v['nombre'],
                                                           v.get('ref',''), dpi_curr, garment_tmpl))

                    if all_imgs:
                        pdf_buf = io.BytesIO()
                        all_imgs[0].save(pdf_buf, "PDF", save_all=True,
                                         append_images=all_imgs[1:], resolution=dpi_curr)
                        ts = datetime.now().strftime("%y%m%d_%H%M")
                        st.download_button(
                            f"⬇️ Descargar PDF ({len(all_imgs)} páginas)",
                            data=pdf_buf.getvalue(),
                            file_name=f"ZZ_RAYAS_{tipo_export.replace(' ','_')}_{ts}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

        st.divider()
        st.markdown("**O exportar variante actual directamente:**")
        if rayas_curr and st.button("⚡ PDF rápido (variante actual)", use_container_width=True):
            with st.spinner("Generando PDF..."):
                p_img = generate_patron(rayas_curr, ori_curr, dpi_curr, nombre_curr)
                f_img = generate_ficha(rayas_curr, ori_curr, nombre_curr, ref_curr, dpi_curr, garment_tmpl)
                pdf_buf2 = io.BytesIO()
                p_img.save(pdf_buf2, "PDF", save_all=True, append_images=[f_img], resolution=dpi_curr)
                ts2 = datetime.now().strftime("%y%m%d_%H%M")
                st.download_button(
                    f"⬇️ Descargar PDF (Patrón + Ficha)",
                    data=pdf_buf2.getvalue(),
                    file_name=f"ZZ_{nombre_curr.replace(' ','_')}_{ts2}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

# ── FOOTER ────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:2rem;border-top:1px solid #2a2a2a;padding-top:8px;
            color:#444;font-size:0.7rem;text-align:center;">
  ZZ STUDIO · RAYAS & FICHAS GENERATOR v3.0 · CONFIDENTIAL
</div>
""", unsafe_allow_html=True)

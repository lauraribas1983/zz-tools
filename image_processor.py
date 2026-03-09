#!/usr/bin/env python3
"""
ZZ Image Batch Processor
- 🤖 Eliminar fondo con IA (rembg) — cualquier foto, cualquier fondo
- 🤍 Fondo blanco (ghost mannequin para PNG transparentes)
- 4 tamaños por imagen: web / catálogo / techpack / thumb
- Renombrado automático convención ZZ
"""

import streamlit as st
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import io
import zipfile
from pathlib import Path

# ── Intentar cargar rembg (IA eliminación fondo) ──
try:
    from rembg import remove as rembg_remove
    REMBG_DISPONIBLE = True
except ImportError:
    REMBG_DISPONIBLE = False

st.set_page_config(
    page_title="ZZ Image Processor",
    page_icon="🖼️",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background: #0f0f0f; color: #e8e8e8; }
    .main .block-container { padding: 2rem; max-width: 1000px; }
    h1 { color: #c8ff00 !important; font-size: 1.4rem !important; letter-spacing: 3px; }
    h2 { color: #c8ff00 !important; font-size: 0.9rem !important; font-weight:700; letter-spacing:2px; border-bottom:1px solid #2c2c2c; padding-bottom:6px; }
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
    .result-box { background:#161616; border:1px solid #2c2c2c; border-radius:8px; padding:12px; margin:8px 0; }
    div[data-testid="stImage"] img { border-radius:8px; border:1px solid #2c2c2c; }
</style>
""", unsafe_allow_html=True)

st.markdown("# ZZ · IMAGE PROCESSOR")
st.markdown("<p style='color:#888;font-size:0.85rem;margin-top:-12px;'>Fondo blanco · 3 tamaños · Renombrado ZZ automático</p>", unsafe_allow_html=True)
st.markdown("---")

# ── CONFIG ────────────────────────────────────────────────────────────────────
col_conf, col_upload = st.columns([1, 2])

with col_conf:
    st.markdown("## CONFIGURACIÓN")

    ref_base = st.text_input("Referencia base", placeholder="ZZ-RND-26-001", help="El nombre base para todos los archivos")
    temporada = st.selectbox("Temporada", ["SS26", "AW26", "SS27", "AW27"])
    categoria = st.selectbox("Categoría", ["HOO", "CRW", "TEE", "TNK", "JRS", "VES", "JOG", "LEG", "TOP", "BOD", "CAR", "JKT"])
    color_code = st.text_input("Color (código)", placeholder="BLK", help="BLK, WHT, TRC, SGE...")

    st.markdown("---")
    st.markdown("## MODO DE FONDO")

    if REMBG_DISPONIBLE:
        modo_fondo = st.radio(
            "Método",
            ["🤖 IA — Quitar cualquier fondo (fotos reales)",
             "🤍 Alpha — Solo PNG transparentes (renders)"],
            help="IA: funciona con cualquier foto. Alpha: requiere PNG con fondo ya transparente."
        )
        usar_ia = "IA" in modo_fondo
    else:
        st.warning("⚠️ rembg no instalado. Ejecuta INSTALAR_DEPENDENCIAS.bat")
        usar_ia = False
        modo_fondo = "alpha"

    st.markdown("## OPERACIONES")

    op_bg = st.checkbox("🤍 Aplicar fondo blanco", value=True,
                        help="Aplica fondo blanco puro tras la eliminación de fondo.")
    op_web = st.checkbox("🌐 Versión web (1200px)", value=True)
    op_catalog = st.checkbox("📖 Versión catálogo (2400px, alta calidad)", value=True)
    op_techpack = st.checkbox("📋 Versión techpack (800px)", value=True)
    op_thumb = st.checkbox("📱 Miniatura (400px para WhatsApp/redes)", value=True)

    st.markdown("---")
    st.markdown("## MARCA DE AGUA")
    watermark = st.checkbox("Añadir marca de agua ZZ", value=False)
    if watermark:
        wm_text = st.text_input("Texto marca de agua", value="ZZ STUDIO")
        wm_opacity = st.slider("Opacidad", 10, 80, 30)

with col_upload:
    st.markdown("## SUBIR IMÁGENES")
    st.markdown("<p style='color:#666;font-size:0.8rem;'>Sube desde ordenador o móvil. JPG, PNG, WEBP. Varias a la vez.</p>", unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Arrastra o selecciona imágenes",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True
    )

    if uploaded:
        st.markdown(f"<p style='color:#c8ff00;font-size:0.85rem;font-weight:700;'>{len(uploaded)} imagen(es) seleccionada(s)</p>", unsafe_allow_html=True)

        # Preview grid
        preview_cols = st.columns(min(len(uploaded), 4))
        for idx, f in enumerate(uploaded[:4]):
            with preview_cols[idx]:
                img = Image.open(f)
                st.image(img, caption=f.name[:20], use_container_width=True)
        if len(uploaded) > 4:
            st.markdown(f"<p style='color:#666;font-size:0.75rem;'>+{len(uploaded)-4} más...</p>", unsafe_allow_html=True)

        st.markdown("---")
        procesar = st.button("⚡ PROCESAR IMÁGENES")

        if procesar:
            if not ref_base:
                st.error("Añade una referencia base primero.")
            else:
                zip_buffer = io.BytesIO()
                processed_count = 0

                progress = st.progress(0)
                status_text = st.empty()

                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for idx, file in enumerate(uploaded):
                        status_text.markdown(f"<p style='color:#888;font-size:0.8rem;'>Procesando {file.name}...</p>", unsafe_allow_html=True)
                        progress.progress((idx + 1) / len(uploaded))

                        try:
                            img = Image.open(file).convert("RGBA")
                            orig_w, orig_h = img.size

                            # BASE NAME
                            vista = "Front" if idx == 0 else ("Back" if idx == 1 else f"Detail{idx}")
                            base_name = f"{temporada}_{categoria}{str(idx+1).zfill(3)}_{color_code}_{vista}"
                            if ref_base:
                                base_name = f"{ref_base.replace('/', '-')}_{base_name}"

                            def eliminar_fondo_ia(image_bytes):
                                """Usa rembg IA para eliminar cualquier fondo"""
                                resultado_bytes = rembg_remove(image_bytes)
                                return Image.open(io.BytesIO(resultado_bytes)).convert("RGBA")

                            def apply_white_bg(image):
                                """Pega imagen sobre fondo blanco puro"""
                                if image.mode == 'RGBA':
                                    bg = Image.new("RGB", image.size, (255, 255, 255))
                                    bg.paste(image, mask=image.split()[3])
                                    result = bg
                                else:
                                    bg = Image.new("RGBA", image.size, (255, 255, 255, 255))
                                    bg.paste(image)
                                    result = bg.convert("RGB")
                                return ImageEnhance.Brightness(result).enhance(1.03)

                            def add_watermark(image, text, opacity):
                                from PIL import ImageDraw, ImageFont
                                overlay = Image.new('RGBA', image.size, (255,255,255,0))
                                draw = ImageDraw.Draw(overlay)
                                w, h = image.size
                                # Simple text watermark diagonal
                                draw.text((w//4, h//2), text, fill=(200, 200, 200, int(opacity * 2.55)))
                                base = image.convert('RGBA')
                                combined = Image.alpha_composite(base, overlay)
                                return combined.convert('RGB')

                            def resize_pad(image, max_size):
                                """Resize manteniendo ratio, padding blanco"""
                                image.thumbnail((max_size, max_size), Image.LANCZOS)
                                bg = Image.new("RGB", (max_size, max_size), (255, 255, 255))
                                offset = ((max_size - image.width) // 2, (max_size - image.height) // 2)
                                if image.mode == 'RGBA':
                                    bg.paste(image, offset, mask=image.split()[3])
                                else:
                                    bg.paste(image, offset)
                                return bg

                            # ── Procesar fondo ──
                            if usar_ia and REMBG_DISPONIBLE:
                                status_text.markdown(
                                    f"<p style='color:#888;font-size:0.8rem;'>🤖 IA eliminando fondo: {file.name}...</p>",
                                    unsafe_allow_html=True
                                )
                                file.seek(0)
                                img_bytes_raw = file.read()
                                img_sin_fondo = eliminar_fondo_ia(img_bytes_raw)
                                processed = apply_white_bg(img_sin_fondo) if op_bg else img_sin_fondo.convert("RGB")
                            elif op_bg:
                                processed = apply_white_bg(img)
                            else:
                                processed = img.convert("RGB")

                            # Add watermark if requested
                            if watermark:
                                processed = add_watermark(processed, wm_text, wm_opacity)

                            # Generate versions
                            versions = {}
                            if op_web:
                                versions["web_1200px"] = resize_pad(processed.copy(), 1200)
                            if op_catalog:
                                versions["catalogo_2400px"] = resize_pad(processed.copy(), 2400)
                            if op_techpack:
                                versions["techpack_800px"] = resize_pad(processed.copy(), 800)
                            if op_thumb:
                                versions["thumb_400px"] = resize_pad(processed.copy(), 400)

                            # Save to ZIP
                            for version_name, img_out in versions.items():
                                folder = version_name.split("_")[0]
                                fname = f"{folder}/{base_name}_{version_name}.jpg"
                                img_bytes = io.BytesIO()
                                quality = 95 if "catalogo" in version_name else 88
                                img_out.save(img_bytes, format="JPEG", quality=quality, optimize=True)
                                zf.writestr(fname, img_bytes.getvalue())

                            processed_count += 1

                        except Exception as e:
                            st.warning(f"Error con {file.name}: {str(e)}")

                zip_buffer.seek(0)
                progress.progress(1.0)
                status_text.markdown(f"<p style='color:#c8ff00;font-size:0.85rem;font-weight:700;'>✅ {processed_count} imagen(es) procesadas</p>", unsafe_allow_html=True)

                zip_name = f"ZZ_Renders_{ref_base.replace('/', '-')}_{temporada}.zip"
                st.download_button(
                    label=f"⬇️  DESCARGAR ZIP ({processed_count} imágenes · {len([x for x in [op_web, op_catalog, op_techpack, op_thumb] if x])} versiones cada una)",
                    data=zip_buffer,
                    file_name=zip_name,
                    mime="application/zip"
                )

                st.markdown(f"""
                <div class='result-box'>
                <p style='color:#666;font-size:0.75rem;font-weight:700;letter-spacing:2px;'>ESTRUCTURA DEL ZIP</p>
                {'<p style="color:#e8e8e8;font-family:monospace;font-size:0.8rem;">📁 web/ — 1200px JPG</p>' if op_web else ''}
                {'<p style="color:#e8e8e8;font-family:monospace;font-size:0.8rem;">📁 catalogo/ — 2400px JPG alta calidad</p>' if op_catalog else ''}
                {'<p style="color:#e8e8e8;font-family:monospace;font-size:0.8rem;">📁 techpack/ — 800px JPG</p>' if op_techpack else ''}
                {'<p style="color:#e8e8e8;font-family:monospace;font-size:0.8rem;">📁 thumb/ — 400px para WhatsApp/redes</p>' if op_thumb else ''}
                <p style='color:#666;font-size:0.75rem;margin-top:8px;'>Convención: {temporada}_{categoria}001_{color_code}_Front_web_1200px.jpg</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background:#161616;border:1px dashed #2c2c2c;border-radius:8px;padding:40px;text-align:center;'>
        <p style='color:#444;font-size:2rem;'>🖼️</p>
        <p style='color:#666;font-size:0.85rem;'>Sube imágenes arriba para empezar</p>
        <p style='color:#444;font-size:0.75rem;'>Funciona desde móvil — haz foto directamente</p>
        </div>
        """, unsafe_allow_html=True)

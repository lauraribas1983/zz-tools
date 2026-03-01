"""
ZZ Studio — Trend Hunter
Captura tendencias de moda de fuentes gratuitas
Organiza por temporada, categoría y nivel de cliente (C1/C2/C3)
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
from pathlib import Path
import re
import time
import io

st.set_page_config(
    page_title="ZZ · Trend Hunter",
    page_icon="🔍",
    layout="wide"
)

# ─── STORAGE LOCAL ────────────────────────────────────────────────────────
DATA_FILE = Path("zz_trends_data.json")

def cargar_datos():
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"tendencias": [], "boards": {}}

def guardar_datos(datos):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

datos = cargar_datos()

# ─── FUENTES DE TENDENCIAS ────────────────────────────────────────────────
FUENTES = {
    "Vogue Runway": {
        "url": "https://www.vogue.com/runway",
        "tipo": "scrape",
        "gratis": True
    },
    "Who What Wear": {
        "url": "https://www.whowhatwear.com/fashion/trends",
        "tipo": "scrape",
        "gratis": True
    },
    "Refinery29 Trends": {
        "url": "https://www.refinery29.com/en-us/fashion-trends",
        "tipo": "scrape",
        "gratis": True
    },
    "Business of Fashion": {
        "url": "https://www.businessoffashion.com/sections/fashion",
        "tipo": "scrape",
        "gratis": True
    },
    "Hypebeast Fashion": {
        "url": "https://hypebeast.com/fashion",
        "tipo": "scrape",
        "gratis": True
    },
}

KEYWORDS_TENDENCIA = {
    "Siluetas": ["oversized", "boxy", "fitted", "relaxed", "slim", "wide leg", "balloon", "cocoon"],
    "Materiales": ["jersey", "fleece", "rib", "waffle", "velour", "brushed", "modal", "tencel", "recycled"],
    "Colores": ["butter", "sage", "terracotta", "chocolate", "cobalt", "burgundy", "camel", "ecru", "greige"],
    "Detalles": ["seam detail", "panel", "pocket", "ruched", "gathered", "drawstring", "zip", "contrast"],
    "Estilo": ["minimalist", "quiet luxury", "street", "athletic", "loungewear", "resort", "Y2K", "bourgeois"],
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
}

# ─── FUNCIONES SCRAPING ───────────────────────────────────────────────────

def scrape_tendencias_generico(url, max_items=10):
    """Scraper genérico que extrae titulares de tendencias"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        resultados = []

        # Buscar headings y artículos de tendencia
        for tag in ['h1', 'h2', 'h3', 'h4']:
            elementos = soup.find_all(tag)
            for el in elementos:
                texto = el.get_text(strip=True)
                # Filtrar por longitud y relevancia de moda
                if 10 < len(texto) < 150:
                    texto_lower = texto.lower()
                    palabras_moda = ['trend', 'style', 'fashion', 'wear', 'look', 'season', 'fall', 'spring',
                                    'summer', 'winter', 'collection', 'color', 'must', 'outfit']
                    if any(p in texto_lower for p in palabras_moda):
                        # Intentar obtener URL del artículo
                        parent_a = el.find_parent('a')
                        link = ""
                        if parent_a and parent_a.get('href'):
                            href = parent_a['href']
                            if href.startswith('http'):
                                link = href
                            else:
                                from urllib.parse import urljoin
                                link = urljoin(url, href)

                        if texto not in [r['titulo'] for r in resultados]:
                            resultados.append({
                                'titulo': texto,
                                'url': link,
                                'fuente': url
                            })

                if len(resultados) >= max_items:
                    break
            if len(resultados) >= max_items:
                break

        return resultados

    except Exception as e:
        return [{"error": str(e), "titulo": f"Error accediendo a {url}", "url": "", "fuente": url}]

def analizar_keywords(texto, keywords_dict):
    """Analiza qué keywords de tendencia aparecen en un texto"""
    texto_lower = texto.lower()
    encontradas = {}
    for categoria, palabras in keywords_dict.items():
        hits = [p for p in palabras if p in texto_lower]
        if hits:
            encontradas[categoria] = hits
    return encontradas

def guardar_tendencia_manual(titulo, descripcion, url, categoria, nivel_cliente, temporada, tags):
    """Guarda una tendencia agregada manualmente"""
    tendencia = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "titulo": titulo,
        "descripcion": descripcion,
        "url": url,
        "categoria": categoria,
        "nivel_cliente": nivel_cliente,
        "temporada": temporada,
        "tags": tags,
        "fuente": "Manual",
        "keywords": analizar_keywords(descripcion, KEYWORDS_TENDENCIA)
    }
    datos["tendencias"].append(tendencia)
    guardar_datos(datos)
    return tendencia

# ─── UI ───────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .trend-card {
        background: #1a1a1a;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        margin-right: 4px;
    }
    .badge-c1 { background: #FFD700; color: #000; }
    .badge-c2 { background: #C0C0C0; color: #000; }
    .badge-c3 { background: #CD7F32; color: #fff; }
    .stButton > button {
        background: #FFD700;
        color: #000;
        font-weight: bold;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔍 ZZ · Trend Hunter")
st.caption("Captura y organiza tendencias de moda • Categoriza por C1/C2/C3 • Export a informe")

# ── TABS ──────────────────────────────────────────────────────────────────
tab_live, tab_manual, tab_board, tab_export = st.tabs([
    "🌐 Escanear Web", "✏️ Agregar Manual", "📌 Mi Board", "📄 Export Informe"
])

# ────────────────────────────────────────────────────────────────────────
with tab_live:
    st.subheader("Escanear fuentes de tendencias")
    st.info("💡 Extrae titulares y artículos de tendencias de medios de moda gratuitos")

    col1, col2 = st.columns([2, 1])

    with col1:
        fuente_sel = st.selectbox("Fuente", list(FUENTES.keys()))
        url_custom = st.text_input(
            "O introduce una URL específica",
            placeholder="https://www.vogue.com/runway/spring-2026",
            help="Pega cualquier página de tendencias de moda"
        )

    with col2:
        max_resultados = st.slider("Máx. resultados", 5, 30, 10)
        st.markdown("<br>", unsafe_allow_html=True)
        buscar = st.button("🔎 ESCANEAR AHORA", use_container_width=True)

    if buscar:
        url_a_usar = url_custom if url_custom else FUENTES[fuente_sel]["url"]

        with st.spinner(f"Escaneando {url_a_usar}..."):
            resultados = scrape_tendencias_generico(url_a_usar, max_resultados)

        if resultados:
            st.success(f"✅ {len(resultados)} artículos encontrados")

            st.markdown("**Selecciona los que quieres guardar en tu board:**")

            seleccionados = []
            for i, r in enumerate(resultados):
                if "error" not in r:
                    col_check, col_info = st.columns([0.1, 0.9])
                    with col_check:
                        if st.checkbox("", key=f"sel_{i}", value=False):
                            seleccionados.append(r)
                    with col_info:
                        st.markdown(f"**{r['titulo']}**")
                        if r.get('url'):
                            st.caption(f"[🔗 Ver artículo]({r['url']})")
                        # Analizar keywords
                        kw = analizar_keywords(r['titulo'], KEYWORDS_TENDENCIA)
                        if kw:
                            tags_html = " ".join([f"`{k}`" for cat in kw.values() for k in cat])
                            st.caption(f"Tags: {tags_html}")
                else:
                    st.error(r['titulo'])

            if seleccionados:
                st.divider()
                st.markdown("**Categorizar los seleccionados:**")
                col_g1, col_g2, col_g3 = st.columns(3)
                with col_g1:
                    cat_grupo = st.selectbox("Categoría", [
                        "Siluetas", "Materiales", "Colores", "Detalles",
                        "Estampados", "Mix & Match", "Otros"
                    ], key="cat_grupo")
                with col_g2:
                    nivel_grupo = st.multiselect("Nivel cliente", ["C1", "C2", "C3"], default=["C2"], key="niv_grupo")
                with col_g3:
                    temp_grupo = st.selectbox("Temporada", ["SS26", "AW26", "SS27", "AW27", "Evergreen"], key="temp_grupo")

                if st.button("💾 GUARDAR SELECCIONADOS", use_container_width=True):
                    guardadas = 0
                    for r in seleccionados:
                        guardar_tendencia_manual(
                            titulo=r['titulo'],
                            descripcion=r['titulo'],
                            url=r.get('url', ''),
                            categoria=cat_grupo,
                            nivel_cliente=", ".join(nivel_grupo),
                            temporada=temp_grupo,
                            tags=list(analizar_keywords(r['titulo'], KEYWORDS_TENDENCIA).keys())
                        )
                        guardadas += 1
                    datos = cargar_datos()  # Recargar
                    st.success(f"✅ {guardadas} tendencias guardadas en tu board")
                    st.rerun()
        else:
            st.warning("No se encontraron resultados. Prueba con otra URL.")

# ────────────────────────────────────────────────────────────────────────
with tab_manual:
    st.subheader("✏️ Agregar tendencia manualmente")
    st.caption("Para referencias de Instagram, Pinterest, ShowroomPrive, ferias, etc.")

    with st.form("form_manual"):
        titulo = st.text_input("Titular / Tendencia *", placeholder="ej: Oversized knit coats dominan AW26")
        descripcion = st.text_area("Descripción / Notas",
            placeholder="ej: Los abrigos de punto oversized en tonos neutros (camel, ecru) dominan las pasarelas de Milán AW26. Silueta cocoon, largo midi. Relevante para Zara y P&B.",
            height=120)
        url_ref = st.text_input("URL referencia", placeholder="https://...")

        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            cat_manual = st.selectbox("Categoría", [
                "Siluetas", "Materiales", "Colores", "Detalles",
                "Estampados", "Mix & Match", "Estilos", "Otros"
            ])
        with col_f2:
            nivel_manual = st.multiselect("Nivel cliente", ["C1", "C2", "C3"], default=["C2"])
        with col_f3:
            temp_manual = st.selectbox("Temporada", ["SS26", "AW26", "SS27", "AW27", "Evergreen"])
        with col_f4:
            tags_manual = st.text_input("Tags (separados por coma)", placeholder="oversized, camel, coat")

        enviado = st.form_submit_button("💾 GUARDAR TENDENCIA", use_container_width=True)

        if enviado:
            if titulo:
                tags_lista = [t.strip() for t in tags_manual.split(",") if t.strip()]
                guardar_tendencia_manual(
                    titulo=titulo,
                    descripcion=descripcion,
                    url=url_ref,
                    categoria=cat_manual,
                    nivel_cliente=", ".join(nivel_manual),
                    temporada=temp_manual,
                    tags=tags_lista
                )
                datos = cargar_datos()
                st.success("✅ Tendencia guardada")
                st.rerun()
            else:
                st.error("El titular es obligatorio")

# ────────────────────────────────────────────────────────────────────────
with tab_board:
    st.subheader("📌 Mi Board de Tendencias")

    tendencias = datos.get("tendencias", [])

    if not tendencias:
        st.info("Tu board está vacío. Escanea la web o agrega tendencias manualmente.")
    else:
        # Filtros
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            filtro_temp = st.selectbox("Temporada", ["Todas"] + list(set(t.get("temporada","") for t in tendencias)))
        with col_f2:
            filtro_nivel = st.selectbox("Nivel cliente", ["Todos", "C1", "C2", "C3"])
        with col_f3:
            filtro_cat = st.selectbox("Categoría", ["Todas"] + list(set(t.get("categoria","") for t in tendencias)))
        with col_f4:
            filtro_buscar = st.text_input("Buscar", placeholder="palabra clave...")

        # Aplicar filtros
        filtradas = tendencias.copy()
        if filtro_temp != "Todas":
            filtradas = [t for t in filtradas if t.get("temporada") == filtro_temp]
        if filtro_nivel != "Todos":
            filtradas = [t for t in filtradas if filtro_nivel in t.get("nivel_cliente", "")]
        if filtro_cat != "Todas":
            filtradas = [t for t in filtradas if t.get("categoria") == filtro_cat]
        if filtro_buscar:
            filtradas = [t for t in filtradas if
                        filtro_buscar.lower() in t.get("titulo","").lower() or
                        filtro_buscar.lower() in t.get("descripcion","").lower()]

        st.markdown(f"**{len(filtradas)} tendencias** | {len(tendencias)} total")
        st.divider()

        # Mostrar tarjetas
        for trend in reversed(filtradas):  # Más recientes primero
            nivel = trend.get("nivel_cliente", "")
            badge_class = "badge-c1" if "C1" in nivel else "badge-c2" if "C2" in nivel else "badge-c3"

            with st.container():
                col_info, col_acc = st.columns([5, 1])

                with col_info:
                    niveles_list = [n.strip() for n in nivel.split(",") if n.strip()]
                    badges = " ".join([f"<span class='badge {badge_class}'>{n}</span>" for n in niveles_list])
                    st.markdown(
                        f"{badges} <span style='font-size:11px;color:#888'>{trend.get('categoria','')} · {trend.get('temporada','')} · {trend.get('fecha','')}</span>",
                        unsafe_allow_html=True
                    )
                    st.markdown(f"**{trend['titulo']}**")

                    if trend.get('descripcion') and trend['descripcion'] != trend['titulo']:
                        st.caption(trend['descripcion'])

                    if trend.get('url'):
                        st.caption(f"[🔗 Fuente]({trend['url']})")

                    if trend.get('tags'):
                        tags_str = " · ".join([f"`{t}`" for t in trend['tags'][:6]])
                        st.caption(tags_str)

                with col_acc:
                    if st.button("🗑️", key=f"del_{trend['id']}", help="Eliminar"):
                        datos["tendencias"] = [t for t in datos["tendencias"] if t["id"] != trend["id"]]
                        guardar_datos(datos)
                        st.rerun()

                st.divider()

# ────────────────────────────────────────────────────────────────────────
with tab_export:
    st.subheader("📄 Export Informe de Tendencias")

    tendencias = datos.get("tendencias", [])

    if not tendencias:
        st.info("Agrega tendencias para poder exportar un informe.")
    else:
        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            export_temp = st.selectbox("Temporada para el informe",
                ["Todas"] + list(set(t.get("temporada","") for t in tendencias)))
            export_nivel = st.multiselect("Niveles cliente", ["C1", "C2", "C3"], default=["C1","C2","C3"])
            titulo_informe = st.text_input("Título del informe", f"ZZ Trend Report {datetime.now().strftime('%B %Y')}")
        with col_ex2:
            autor = st.text_input("Preparado por", "ZZ Studio — Trend Team")
            notas_intro = st.text_area("Intro / Notas del equipo",
                "Selección de tendencias relevantes para la colección. Basado en análisis de pasarela, street style y reportes de medios especializados.",
                height=100)

        if st.button("📄 GENERAR INFORME TXT", use_container_width=True):
            # Filtrar
            trend_export = [t for t in tendencias if
                           (export_temp == "Todas" or t.get("temporada") == export_temp) and
                           any(n in t.get("nivel_cliente","") for n in export_nivel)]

            # Generar TXT / Markdown
            lineas = []
            lineas.append(f"{'='*60}")
            lineas.append(f"  {titulo_informe.upper()}")
            lineas.append(f"{'='*60}")
            lineas.append(f"Preparado por: {autor}")
            lineas.append(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}")
            lineas.append(f"Total tendencias: {len(trend_export)}")
            lineas.append(f"")
            lineas.append(f"INTRODUCCIÓN:")
            lineas.append(notas_intro)
            lineas.append(f"")
            lineas.append(f"{'─'*60}")

            # Agrupar por categoría
            categorias = list(set(t.get("categoria","Otros") for t in trend_export))
            for cat in sorted(categorias):
                lineas.append(f"\n📌 {cat.upper()}")
                lineas.append("─" * 40)
                cat_trends = [t for t in trend_export if t.get("categoria") == cat]
                for t in cat_trends:
                    lineas.append(f"\n• [{t.get('temporada','')} | {t.get('nivel_cliente','')}]")
                    lineas.append(f"  {t['titulo']}")
                    if t.get('descripcion') and t['descripcion'] != t['titulo']:
                        lineas.append(f"  → {t['descripcion']}")
                    if t.get('url'):
                        lineas.append(f"  🔗 {t['url']}")
                    if t.get('tags'):
                        lineas.append(f"  Tags: {', '.join(t['tags'])}")

            lineas.append(f"\n{'='*60}")
            lineas.append(f"ZZ Studio — Confidential")
            lineas.append(f"{'='*60}")

            informe_texto = "\n".join(lineas)

            st.text_area("Preview del informe:", informe_texto, height=300)

            nombre_archivo = f"ZZ_TREND_REPORT_{export_temp}_{datetime.now().strftime('%Y%m%d')}.txt"
            st.download_button(
                "⬇️ DESCARGAR INFORME",
                data=informe_texto.encode('utf-8'),
                file_name=nombre_archivo,
                mime="text/plain",
                use_container_width=True
            )

        st.divider()

        if st.button("📋 EXPORTAR DATOS (JSON)", use_container_width=True):
            json_data = json.dumps(datos, ensure_ascii=False, indent=2)
            st.download_button(
                "⬇️ Descargar JSON completo",
                data=json_data.encode('utf-8'),
                file_name=f"ZZ_trends_backup_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )

# -*- coding: utf-8 -*-
"""
Localizador Multigremio – v2.1 (Google + Empresite) + Mejoras UI + Sabueso Emails + Dashboard Pro
"""

import os
import io
import base64
import time
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

import requests
from bs4 import BeautifulSoup

import pandas as pd
import numpy as np
from PIL import Image
import streamlit as st
import plotly.express as px # <-- NUEVA LIBRERÍA DE GRÁFICOS PRO
import sqlite3 # <-- NUEVO: Para la Caja Fuerte

from concurrent.futures import ThreadPoolExecutor # <-- NUEVO: Para el Modo Turbo
from streamlit_lottie import st_lottie # <-- NUEVO: Para las animaciones
from streamlit_geolocation import streamlit_geolocation

# ------------- CONFIG INICIAL -------------
st.set_page_config(
    page_title="Localizador Multigremio Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------- DISEÑO APPLE / TESLA (ULTRA PREMIUM) -------------
st.set_page_config(page_title="A Fuego Generator", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    /* 1. TIPOGRAFÍA (Inter, simula la fuente 'SF Pro' de Apple) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; }

    /* 2. EL SECRETO DEL FONDO (F5F5F7 - El color exacto de fondo de Apple, no quema la vista) */
    .stApp { background-color: #F5F5F7; }
    
    /* Ocultamos el header y footer por defecto de Streamlit para que parezca una web real */
    header { visibility: hidden; }
    footer { visibility: hidden; }

    /* 3. TÍTULO HERO (Centrado, masivo y con confianza) */
    .hero-container { text-align: center; padding-top: 2rem; padding-bottom: 3rem; }
    .hero-title { 
        color: #1D1D1F; 
        font-size: 4.5rem !important; 
        font-weight: 800 !important; 
        letter-spacing: -2px; 
        margin-bottom: 0.5rem;
    }
    .hero-subtitle { 
        color: #86868B; 
        font-size: 1.3rem; 
        font-weight: 400; 
        letter-spacing: -0.3px;
    }
    .fuego-accent {
        background: linear-gradient(135deg, #FF416C 0%, #FF4B2B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* 4. TARJETAS DE MÉTRICAS FLOTANTES (Blanco puro para destacar sobre el fondo F5F5F7) */
    .metric-card {
        background: #FFFFFF;
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.03); /* Sombra difuminada, estilo Tesla */
        border: 1px solid rgba(0, 0, 0, 0.02);
        transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .metric-card:hover { transform: scale(1.02); }

    /* 5. DISEÑO DE CAJAS DE TEXTO ESTILO iOS (Sin bordes duros) */
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
        background-color: #E8E8ED !important; /* Gris ligero para el interior */
        border-radius: 14px !important;
        border: 2px solid transparent !important;
        transition: all 0.2s ease;
    }
    div[data-baseweb="select"] > div:hover, div[data-baseweb="input"] > div:hover, div[data-baseweb="select"] > div:focus-within {
        background-color: #FFFFFF !important;
        border: 2px solid #FF4B2B !important; /* Brilla al tocarlo */
    }

    /* 6. EL BOTÓN "TESLA" (Forma de píldora, degradado premium) */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #FF416C, #FF4B2B);
        color: white;
        border-radius: 40px; /* Forma redonda perfecta en los bordes */
        padding: 0.8rem 2rem;
        font-size: 1.15rem;
        font-weight: 600;
        border: none;
        box-shadow: 0 8px 20px rgba(255, 75, 43, 0.25);
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        width: 100%;
        margin-top: 10px;
    }
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 25px rgba(255, 75, 43, 0.4);
    }
    
    /* 7. REFINAR LA TABLA DE DATOS */
    [data-testid="stDataFrame"] { border-radius: 16px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.03); border: none !important; }
</style>
""", unsafe_allow_html=True)

# ------------- LOGOS -------------
LOGO_JELPIN_B64 = ""  
LOGO_MULTI_B64  = ""  

def _safe_load_logo(b64_str: str, fallback_path: str, width: int = 140) -> Optional[Image.Image]:
    try:
        if b64_str:
            return Image.open(io.BytesIO(base64.b64decode(b64_str))).convert("RGBA")
    except Exception: pass
    try:
        if os.path.exists(fallback_path):
            return Image.open(fallback_path).convert("RGBA")
    except Exception: pass
    return None

# ------------- ANIMACIONES LOTTIE -------------
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200: return r.json()
    except: pass
    return None

lottie_search = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_bs2nczep.json") # Animación de radar

# ------------- AUTH / LOGIN -------------
def require_login():
    expected = st.secrets.get("AUTH_PASSWORD", os.environ.get("AUTH_PASSWORD", ""))
    if not expected: return  

    if "auth_ok" not in st.session_state: st.session_state["auth_ok"] = False
    if st.session_state["auth_ok"]: return
    
    # Cargamos una animación de fuego espectacular
    lottie_fire = load_lottieurl("https://assets8.lottiefiles.com/packages/lf20_rwyzwnz6.json")

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Animación encima del login
        if lottie_fire:
            st_lottie(lottie_fire, height=180, key="fire_login")
            
        st.markdown('<h1 class="main-header">A <span class="fuego-accent">Fuego</span> Lead Generator</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Búsqueda inteligente, captación ultrarrápida. ⚡</p>', unsafe_allow_html=True)
        
        # SOLUCIÓN AL ENTER: Envolver en un st.form
        with st.form("login_form"):
            pwd = st.text_input("Contraseña de acceso", type="password", label_visibility="collapsed", placeholder="Introduce la contraseña...")
            login = st.form_submit_button("Entrar al Sistema")
            
            if login:
                if pwd == expected:
                    st.session_state["auth_ok"] = True
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta. ¡Inténtalo de nuevo!")
    st.stop()

require_login()

# ------------- ENCABEZADO MODERNO -------------
# ------------- LOGOS (ESQUINA SUPERIOR DERECHA) -------------
c_vacio, c_logos = st.columns([8, 2])
with c_logos:
    logo_col1, logo_col2 = st.columns(2)
    with logo_col1:
        img_jelpin = _safe_load_logo(LOGO_JELPIN_B64, "logo_jelpin.png")
        if img_jelpin: st.image(img_jelpin, width=90)
    with logo_col2:
        img_multi = _safe_load_logo(LOGO_MULTI_B64, "logo_multi.png")
        if img_multi: st.image(img_multi, width=90)

# ------------- CABECERA HERO (ESTILO APPLE) -------------
st.markdown("""
<div class="hero-container">
    <h1 class="hero-title">A <span class="fuego-accent">Fuego</span> Generator</h1>
    <p class="hero-subtitle">Inteligencia de prospección. Velocidad sin límites. ⚡</p>
</div>
""", unsafe_allow_html=True)

# ------------- AYUDAS GLOBALES -------------
def get_secret(name: str, default: str = "") -> str:
    return st.secrets.get(name, os.environ.get(name, default))

def to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Leads") -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

# ------------- EL SABUESO SOCIAL (EMAILS + REDES) -------------
def analyze_website(url: str) -> Dict[str, str]:
    """Entra en la web y extrae el email y redes sociales principales."""
    data = {"correo": "", "instagram": "", "linkedin": "", "facebook": ""}
    if not url or pd.isna(url) or not str(url).startswith("http"): return data
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=3) 
        if r.status_code == 200:
            text = r.text
            # Buscar emails
            emails = set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text))
            emails = {e for e in emails if not e.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.css'))}
            data["correo"] = ", ".join(emails) if emails else ""
            
            # Buscar redes sociales (usamos BeautifulSoup para buscar los links exactos)
            soup = BeautifulSoup(text, "html.parser")
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href'].lower()
                if "instagram.com" in href and not data["instagram"]: data["instagram"] = a_tag['href']
                if "linkedin.com" in href and not data["linkedin"]: data["linkedin"] = a_tag['href']
                if "facebook.com" in href and not data["facebook"]: data["facebook"] = a_tag['href']
    except Exception:
        pass
    return data

# ------------- GOOGLE PLACES -------------
V1_BASE = "https://places.googleapis.com/v1"

def v1_text_search(api_key: str, query: str, location: Optional[Tuple[float, float]] = None, radius_m: Optional[int] = None, language: str = "es", page_token: str = None) -> Dict[str, Any]:
    headers = {
        "X-Goog-Api-Key": api_key,
        # ¡NUEVO!: Añadimos nextPageToken al final del FieldMask para que Google nos dé el ticket
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.websiteUri,places.rating,places.userRatingCount,places.location,places.googleMapsUri,places.currentOpeningHours,places.regularOpeningHours,nextPageToken"
    }
    body = {"textQuery": query, "languageCode": language}
    if location and radius_m:
        body["locationBias"] = {"circle": {"center": {"latitude": location[0], "longitude": location[1]}, "radius": float(radius_m)}}
    
    # ¡NUEVO!: Si tenemos un ticket de la página anterior, lo usamos
    if page_token:
        body["pageToken"] = page_token
        
    r = requests.post(f"{V1_BASE}/places:searchText", headers=headers, json=body, timeout=30)
    r.raise_for_status()
    return r.json()

def google_run(query: str, provincia: str, idioma: str, radius_km: float = 25.0) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    api_key = get_secret("GOOGLE_MAPS_API_KEY")
    if not api_key: raise RuntimeError("Falta GOOGLE_MAPS_API_KEY en secrets.")

    centro_por_prov = {"madrid": (40.4168, -3.7038), "barcelona": (41.3874, 2.1686), "valencia": (39.4699, -0.3763)}
    center = centro_por_prov.get(provincia.lower(), (40.4168, -3.7038))

    items = []
    page_token = None
    
    # ¡NUEVO!: Bucle para pedir hasta 3 páginas (máximo 60 resultados de Google)
    for pagina in range(3):
        data = v1_text_search(api_key, f"{query} en {provincia}", center, int(radius_km * 1000), idioma or "es", page_token)

        for p in data.get("places", []):
            horarios = p.get("currentOpeningHours", {}).get("weekdayDescriptions", []) or p.get("regularOpeningHours", {}).get("weekdayDescriptions", []) or []
            items.append({
                "fuente": "Google", "nombre": p.get("displayName", {}).get("text"), "direccion": p.get("formattedAddress"),
                "telefono": p.get("nationalPhoneNumber"), "web": p.get("websiteUri"), "maps": p.get("googleMapsUri"),
                "rating": p.get("rating"), "opiniones": p.get("userRatingCount"), "lat": p.get("location", {}).get("latitude"),
                "lon": p.get("location", {}).get("longitude"), "horarios": " | ".join(horarios) if horarios else "", "correo": ""
            })
            
        # Extraemos el ticket para la siguiente página
        page_token = data.get("nextPageToken")
        
        # Si Google ya no nos da ticket, significa que ya no hay más resultados y rompemos el bucle
        if not page_token:
            break
            
        # Pequeña pausa obligatoria para que los servidores de Google preparen la siguiente página
        time.sleep(2)

    return items, {"count": len(items), "center": center}


# ------------- YELP -------------
def yelp_search(query: str, provincia: str) -> List[Dict[str, Any]]:
    """Busca negocios usando la API de Yelp Fusion."""
    api_key = get_secret("YELP_API_KEY")
    if not api_key:
        st.warning("⚠️ Falta YELP_API_KEY en secrets. Saltando Yelp...")
        return []
    
    url = "https://api.yelp.com/v3/businesses/search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "accept": "application/json"
    }
    params = {
        "term": query,
        "location": provincia,
        "limit": 50 # Yelp permite hasta 50 por página
    }
    
    empresas = []
    try:
        r = requests.get(url, headers=headers, params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            for b in data.get("businesses", []):
                # Extraemos la dirección completa
                direccion = ", ".join(b.get("location", {}).get("display_address", []))
                empresas.append({
                    "fuente": "Yelp", 
                    "nombre": b.get("name", "N/D"), 
                    "direccion": direccion, 
                    "telefono": b.get("display_phone", ""), 
                    "web": b.get("url", ""), # Yelp da el link a su ficha
                    "maps": "",
                    "rating": b.get("rating", np.nan), 
                    "opiniones": b.get("review_count", np.nan), 
                    "lat": b.get("coordinates", {}).get("latitude", np.nan), 
                    "lon": b.get("coordinates", {}).get("longitude", np.nan), 
                    "horarios": "", 
                    "correo": ""
                })
    except Exception as e:
        st.error(f"Error de conexión con Yelp: {e}")
        
    return empresas

# ------------- BASE DE DATOS (CAJA FUERTE) -------------
def init_db():
    conn = sqlite3.connect("historial_leads.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  fecha TEXT, fuente TEXT, query TEXT, provincia TEXT, resultados INTEGER)''')
    conn.commit()
    conn.close()

def save_search_to_db(fuente, query, provincia, resultados):
    conn = sqlite3.connect("historial_leads.db")
    c = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO history (fecha, fuente, query, provincia, resultados) VALUES (?, ?, ?, ?, ?)",
              (fecha, fuente, query, provincia, resultados))
    conn.commit()
    conn.close()

init_db() # Arrancamos la base de datos al abrir la app

if "last_results" not in st.session_state: st.session_state["last_results"] = None

# ------------- MOTOR DE BÚSQUEDA -------------
st.markdown("<h4 style='color: #1D1D1F; font-weight: 600; text-align: center; margin-bottom: 30px;'>¿Qué negocio buscas hoy?</h4>", unsafe_allow_html=True)

with st.container():
    col1, col2 = st.columns(2)
    
    with col1:
        tipo_busqueda = st.selectbox("Sector / Gremio objetivo", [
            "Administradores de fincas", "Residencias de ancianos", "Colegios", 
            "Fontaneros", "Electricistas", "✍️ Búsqueda libre..."
        ])
        if tipo_busqueda == "✍️ Búsqueda libre...":
            query = st.text_input("Escribe el sector a buscar:", placeholder="Ej: Carpintería metálica...")
        else:
            query = tipo_busqueda

    with col2:
        tipo_ubicacion = st.selectbox("Zona de prospección", [
            "Comunidad de Madrid", "Cataluña", "País Vasco", "Bilbao", 
            "Lleida", "📌 Por Código Postal...", "🌍 Otra ubicación..."
        ])
        if tipo_ubicacion == "🌍 Otra ubicación...":
            provincia = st.text_input("Escribe la ciudad o región:", placeholder="Ej: Valencia, Sevilla...")
        elif tipo_ubicacion == "📌 Por Código Postal...":
            provincia = st.text_input("Escribe el Código Postal:", placeholder="Ej: 28001...")
        else:
            provincia = tipo_ubicacion

    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- LA MAGIA VISUAL: Equilibrio entre GPS y Ajustes ---
    col3, col4 = st.columns(2)
    
    with col3:
        # Títulos elegantes para darle contexto al botón
        st.markdown("<p style='color: #1D1D1F; font-weight: 600; margin-bottom: 2px;'>🛰️ Trabajo de Campo (GPS)</p>", unsafe_allow_html=True)
        st.markdown("<p style='color: #86868B; font-size: 0.85rem; margin-bottom: 10px;'>Activa tu ubicación para buscar prospectos a tu alrededor.</p>", unsafe_allow_html=True)
        
        # TRUCO: Creamos mini-columnas internas. 
        # Metemos el GPS en una columna diminuta para matar el fondo blanco.
        gps_btn_col, gps_space_col = st.columns([1, 5])
        with gps_btn_col:
            ubicacion_gps = streamlit_geolocation()
        with gps_space_col:
            st.empty() # El resto de la pantalla se queda del color gris premium de fondo
        
    with col4:
        st.markdown("<p style='color: #1D1D1F; font-weight: 600; margin-bottom: 2px;'>⚙️ Configuración Adicional</p>", unsafe_allow_html=True)
        st.markdown("<p style='color: #86868B; font-size: 0.85rem; margin-bottom: 10px;'>Ajusta los parámetros del motor de búsqueda.</p>", unsafe_allow_html=True)
        
        with st.expander("Abrir ajustes avanzados", expanded=False):
            idioma = st.selectbox("Idioma de los resultados", ["es", "ca", "en"], index=0)
            radius = st.slider("Radio de búsqueda GPS (km)", 1, 50, 5, 1)
            extraer_emails = st.toggle("🕵️‍♂️ Forzar Sabueso de Emails", value=False)

    st.markdown("<br>", unsafe_allow_html=True)
    buscar = st.button("🚀 INICIAR EXTRACCIÓN", type="primary", use_container_width=True)

st.markdown("<br><br>", unsafe_allow_html=True)
# ------------- ACCIÓN -------------
def _to_df(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["fuente", "nombre", "direccion", "telefono", "web", "correo", "maps", "rating", "opiniones", "lat", "lon"])

if buscar:
    if not query.strip():
        st.sidebar.error("⚠️ Introduce una palabra clave.")
    else:
        with st.status("🔄 Procesando solicitud...", expanded=True) as status:
            try:
                t0 = time.time()
                
                st.write("📡 Conectando con Google Places...")
                
                # --- NUEVO: SEMÁFORO DEL GPS ---
                # 1. Comprobamos si hay datos en la variable del GPS
                if ubicacion_gps and ubicacion_gps.get('latitude') and ubicacion_gps.get('longitude'):
                    st.success("📍 Coordenadas GPS detectadas. Buscando a tu alrededor...")
                    centro_gps = (ubicacion_gps['latitude'], ubicacion_gps['longitude'])
                    
                    api_key = get_secret("GOOGLE_MAPS_API_KEY")
                    rows_g = []
                    page_token = None
                    
                    # Hacemos la búsqueda directa por coordenadas (hasta 60 resultados)
                    for pagina in range(3):
                        data = v1_text_search(api_key, query, location=centro_gps, radius_m=int(float(radius) * 1000), language=idioma, page_token=page_token)
                        
                        for p in data.get("places", []):
                            horarios = p.get("currentOpeningHours", {}).get("weekdayDescriptions", []) or p.get("regularOpeningHours", {}).get("weekdayDescriptions", []) or []
                            rows_g.append({
                                "fuente": "Google (GPS)", "nombre": p.get("displayName", {}).get("text"), "direccion": p.get("formattedAddress"),
                                "telefono": p.get("nationalPhoneNumber"), "web": p.get("websiteUri"), "maps": p.get("googleMapsUri"),
                                "rating": p.get("rating"), "opiniones": p.get("userRatingCount"), "lat": p.get("location", {}).get("latitude"),
                                "lon": p.get("location", {}).get("longitude"), "horarios": " | ".join(horarios) if horarios else "", "correo": ""
                            })
                        page_token = data.get("nextPageToken")
                        if not page_token: break
                        time.sleep(2)
                        
                # 2. Si no hay GPS encendido, hace la búsqueda manual de siempre
                else:
                    rows_g, meta_g = google_run(query, provincia, idioma, radius_km=float(radius))
                # -------------------------------
                
                df = _to_df(rows_g)
                fuentes_usadas = "Google Places"
                
                # ----------------- EJECUCIÓN SABUESO SOCIAL (MODO TURBO) -----------------
                if extraer_emails and not df.empty:
                    st.write("🕵️‍♂️ [MODO TURBO] Analizando dominios web en paralelo...")
                    
                    webs = df["web"].tolist()
                    resultados_turbo = []
                    
                    # Dividimos el trabajo: ¡10 webs a la vez en lugar de 1 en 1!
                    with ThreadPoolExecutor(max_workers=10) as executor:
                        # executor.map mantiene el orden exacto de la tabla
                        for resultado in executor.map(analyze_website, webs):
                            resultados_turbo.append(resultado)
                    
                    # Rellenamos las columnas con los resultados super rápidos
                    df["correo"] = [r.get("correo", "") for r in resultados_turbo]
                    df["instagram"] = [r.get("instagram", "") for r in resultados_turbo]
                    df["linkedin"] = [r.get("linkedin", "") for r in resultados_turbo]
                    df["facebook"] = [r.get("facebook", "") for r in resultados_turbo]
                # ------------------------------------------------------------

                if not df.empty:
                    st.write("🧹 Higienizando base de datos...")
                    df["nombre_temp"] = df["nombre"].str.lower().str.strip()
                    df = df.drop_duplicates(subset=["nombre_temp"], keep="first").drop(columns=["nombre_temp"])
                    
                    if "telefono" in df.columns:
                        def make_wa_link(phone):
                            if not phone or pd.isna(phone): return ""
                            num = re.sub(r'\D', '', str(phone))
                            if len(num) == 9 and num.startswith(('6', '7')):
                                return f"https://wa.me/34{num}"
                            return ""
                        df["whatsapp"] = df["telefono"].apply(make_wa_link)
                    # --- NUEVO: EXTRACCIÓN DE CP Y CIUDAD ---
                    if "direccion" in df.columns:
                        st.write("📍 Separando Códigos Postales y Ciudades...")
                        cps, ciudades = [], []
                        for dir_text in df["direccion"]:
                            if pd.isna(dir_text) or not dir_text:
                                cps.append("")
                                ciudades.append("")
                                continue
                            
                            # Expresión regular: busca 5 dígitos exactos y captura el texto hasta la coma
                            match = re.search(r'\b(\d{5})\s*([^,]+)', str(dir_text))
                            if match:
                                cps.append(match.group(1).strip())
                                ciudades.append(match.group(2).strip())
                            else:
                                cps.append("")
                                ciudades.append("")
                                
                        # Añadimos las nuevas columnas al DataFrame
                        df["cp"] = cps
                        df["ciudad"] = ciudades
                    # -----------------------------------------

                st.session_state["last_results"] = df
                save_search_to_db(fuentes_usadas, query.strip(), provincia.strip(), len(df))
                status.update(label=f"✅ ¡Completado! {len(df)} leads en {time.time()-t0:.1f}s", state="complete", expanded=False)
                    
            except Exception as e:
                status.update(label="❌ Error crítico", state="error")
                st.exception(e)

# ------------- DASHBOARD DE RESULTADOS -------------
df = st.session_state.get("last_results", None)

if df is not None and not df.empty:
    st.markdown("---")
    
    # MÉTRICAS DESTACADAS
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{len(df)}</div><div class="metric-label">Leads Encontrados</div></div>', unsafe_allow_html=True)
    with m2:
        con_web = df['web'].replace('', np.nan).notna().sum()
        st.markdown(f'<div class="metric-card"><div class="metric-value">{con_web}</div><div class="metric-label">Con Página Web</div></div>', unsafe_allow_html=True)
    with m3:
        con_email = df['correo'].replace('', np.nan).notna().sum() if 'correo' in df.columns else 0
        st.markdown(f'<div class="metric-card"><div class="metric-value">{con_email}</div><div class="metric-label">Emails Extraídos</div></div>', unsafe_allow_html=True)
    with m4:
        con_tel = df['telefono'].replace('', np.nan).notna().sum() if 'telefono' in df.columns else 0
        st.markdown(f'<div class="metric-card"><div class="metric-value">{con_tel}</div><div class="metric-label">Teléfonos</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # PESTAÑAS DEL DASHBOARD
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Base de Datos", "🗺️ Mapa Geográfico", "📊 Analítica Pro", "🗄️ Historial Guardado"])

    with tab1:
        # Filtros rápidos
        st.markdown("##### 🔍 Refinar Resultados")
        f1, f2, f3, f4 = st.columns([1,1,1,3])
        solo_email = f1.checkbox("📧 Solo Emails")
        solo_web = f2.checkbox("🌐 Solo Webs")
        top_rating = f3.checkbox("⭐ Rating > 4")

        df_filtrado = df.copy()
        if solo_email and "correo" in df_filtrado.columns: df_filtrado = df_filtrado[df_filtrado["correo"] != ""]
        if solo_web and "web" in df_filtrado.columns: df_filtrado = df_filtrado[df_filtrado["web"] != ""]
        if top_rating and "rating" in df_filtrado.columns: df_filtrado = df_filtrado[df_filtrado["rating"] >= 4.0]

        # SORPRESA: Tabla tipo Excel editable sin perder los enlaces
        st.data_editor(
            df_filtrado, 
            use_container_width=True, 
            height=450,
            num_rows="dynamic", # Permite añadir o borrar filas
            column_config={
                "web": st.column_config.LinkColumn("Página Web", display_text="Visitar Web 🔗"),
                "whatsapp": st.column_config.LinkColumn("Chat", display_text="Abrir WhatsApp 💬") if "whatsapp" in df_filtrado.columns else None
            }
        )
        
        xls = to_excel_bytes(df_filtrado)
        st.download_button("💾 Exportar a Excel (Filtrado)", data=xls, file_name=f"leads_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")

    with tab2:
        if "lat" in df_filtrado.columns and "lon" in df_filtrado.columns:
            df_mapa = df_filtrado.dropna(subset=["lat", "lon"])
            if not df_mapa.empty:
                st.map(df_mapa, latitude="lat", longitude="lon", color="#2563EB", size=40)
            else:
                st.info("📍 No hay coordenadas disponibles para mostrar en el mapa.")

    with tab3:
        c_graf1, c_graf2 = st.columns(2)
        
        # SORPRESA: Gráficos interactivos de alta calidad
        if "rating" in df.columns and df["rating"].notna().any():
            with c_graf1:
                st.markdown("**⭐ Distribución de Reseñas**")
                ratings = df["rating"].dropna().astype(float).value_counts().sort_index().reset_index()
                ratings.columns = ["Estrellas", "Cantidad"]
                fig1 = px.bar(ratings, x="Estrellas", y="Cantidad", text="Cantidad", color="Estrellas", color_continuous_scale="Sunsetdark")
                fig1.update_layout(plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=10, b=10))
                st.plotly_chart(fig1, use_container_width=True)
                
        with c_graf2:
            st.markdown("**🏢 Origen de los Datos**")
            fuentes = df["fuente"].value_counts().reset_index()
            fuentes.columns = ["Fuente", "Cantidad"]
            fig2 = px.pie(fuentes, names="Fuente", values="Cantidad", hole=0.4, color_discrete_sequence=["#2563EB", "#10B981"])
            fig2.update_traces(textinfo='percent+label')
            fig2.update_layout(margin=dict(t=10, b=10), showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
  
    with tab4:
        st.markdown("### 🗄️ Historial Permanente de Búsquedas")
        st.caption("Estos datos están guardados de forma segura en tu ordenador. No se borran al cerrar la página.")
        
        try:
            conn = sqlite3.connect("historial_leads.db")
            df_history = pd.read_sql_query("SELECT fecha, fuente, query as Búsqueda, provincia as Ubicación, resultados FROM history ORDER BY id DESC", conn)
            conn.close()
            
            if not df_history.empty:
                st.dataframe(df_history, use_container_width=True)
            else:
                st.info("Aún no hay búsquedas guardadas en la caja fuerte.")
        except Exception as e:
            st.error(f"No se pudo cargar el historial: {e}")
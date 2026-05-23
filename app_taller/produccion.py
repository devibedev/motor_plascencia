"""
MundoCanceles - Aplicación de Taller (Producción)
Presenta un estilo de "Cuaderno de Croquis" interactivo para los operarios del taller,
calculando cortes en tiempo real a partir de coeficientes almacenados en PostgreSQL.
"""
import streamlit as st
import pandas as pd
import re
from core.database import get_db_connection, extraer_mm_desde_formula

# Configuración de página de alta visibilidad para tabletas/pantallas industriales
st.set_page_config(
    page_title="MundoCanceles - Taller de Producción",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de Estilos CSS "Cuaderno de Croquis"
# Utiliza fuentes estilo manuscrito y Courier Prime (técnico), con cuadrícula de cuaderno (#FDFBF7)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Architects+Daughter&family=Courier+Prime:ital,wght@0,400;0,700;1,400;1,700&display=swap');
    
    /* Fondo del cuaderno de cuadrícula */
    .stApp {
        background-color: #FDFBF7 !important;
        background-image: 
            linear-gradient(rgba(230, 220, 205, 0.3) 1px, transparent 1px),
            linear-gradient(90deg, rgba(230, 220, 205, 0.3) 1px, transparent 1px) !important;
        background-size: 25px 25px !important;
        color: #2E2924 !important;
        font-family: 'Courier Prime', monospace !important;
    }
    
    /* Títulos estilo bosquejo manual */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Architects Daughter', cursive !important;
        color: #3D352E !important;
        border-bottom: 2px dashed #D6CEBF !important;
        padding-bottom: 5px;
    }
    
    /* Sidebar estilo croquis */
    section[data-testid="stSidebar"] {
        background-color: #F7F3EB !important;
        border-right: 2px solid #D6CEBF !important;
        font-family: 'Architects Daughter', cursive !important;
    }
    
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] label {
        font-family: 'Architects Daughter', cursive !important;
        color: #3D352E !important;
    }
    
    /* Contenedor de métrica como tarjeta croquis */
    div[data-testid="metric-container"] {
        background-color: #FCF9F2 !important;
        border: 2px solid #5C544A !important;
        border-radius: 8px !important;
        padding: 20px !important;
        box-shadow: 4px 4px 0px #5C544A !important;
        margin-bottom: 20px !important;
        transition: transform 0.2s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translate(-2px, -2px);
        box-shadow: 6px 6px 0px #5C544A !important;
    }
    
    /* Etiquetas e indicadores de medidas */
    div[data-testid="stMetricLabel"] {
        font-family: 'Architects Daughter', cursive !important;
        font-size: 1.25rem !important;
        color: #5C544A !important;
        font-weight: bold !important;
    }
    
    div[data-testid="stMetricValue"] {
        font-family: 'Courier Prime', monospace !important;
        font-size: 2.5rem !important;
        color: #B22222 !important; /* Rojo lápiz industrial */
        font-weight: 700 !important;
    }
    
    /* Inputs y controles */
    .stNumberInput input {
        font-family: 'Courier Prime', monospace !important;
        font-size: 1.3rem !important;
        background-color: #FCF9F2 !important;
        border: 2px solid #5C544A !important;
        border-radius: 4px !important;
        color: #2E2924 !important;
    }
    
    .stSelectbox div[data-baseweb="select"] {
        font-family: 'Courier Prime', monospace !important;
        border: 2px solid #5C544A !important;
        border-radius: 4px !important;
        background-color: #FCF9F2 !important;
    }
</style>
""", unsafe_allow_html=True)

def evaluar_corte(formula_o_descuento, base_val, variable_name, default_subtraction=True):
    """
    Evalúa matemáticamente un descuento o fórmula paramétrica de forma segura.
    """
    if formula_o_descuento is None:
        return base_val
        
    try:
        # Si ya es un valor puramente numérico
        if isinstance(formula_o_descuento, (int, float)):
            return base_val - formula_o_descuento if default_subtraction else formula_o_descuento
            
        # Convertir unidades a milímetros
        cleaned = extraer_mm_desde_formula(formula_o_descuento)
        
        # Si tras limpiar es un número simple
        try:
            val = float(cleaned)
            return base_val - val if default_subtraction else val
        except ValueError:
            pass
            
        # Evaluar expresión matemática
        expr = str(cleaned).upper()
        expr = expr.replace(variable_name.upper(), str(base_val))
        # Sanitizar para evitar inyecciones
        expr = re.sub(r"[^0-9\+\-\*\/\.\(\)]", "", expr)
        
        # Evaluar de forma segura
        resultado = float(eval(expr))
        return resultado
    except Exception as e:
        st.warning(f"Error evaluando fórmula '{formula_o_descuento}': {e}")
        return base_val

def obtener_sistemas():
    """
    Obtiene la lista completa de sistemas/series disponibles en la base de datos.
    """
    try:
        conn = get_db_connection()
        query = "SELECT clave, nombre FROM sistemas_ventana ORDER BY nombre ASC;"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"⚠️ Error al conectar con PostgreSQL: {e}")
        # Retornar datos semilla locales en caso de desconexión temporal
        return pd.DataFrame([
            {"clave": "SERIE_70_FIJO", "nombre": "Serie 70 Fijo (Respaldo)"},
            {"clave": "SERIE_1400_CORREDIZO", "nombre": "Serie 1400 Corredizo (Respaldo)"}
        ])

def obtener_sistema_detalle(clave):
    """
    Extrae la configuración detallada de descuentos del sistema seleccionado.
    """
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT clave, nombre, descuento_jamba, descuento_horizontal, descuento_junquillo, descuento_vidrio 
                FROM sistemas_ventana 
                WHERE clave = %s;
            """, (clave,))
            row = cur.fetchone()
        conn.close()
        if row:
            return dict(row)
    except Exception as e:
        st.warning(f"Usando fallback para el sistema '{clave}' debido a: {e}")
        
    # Fallback locales por seguridad
    fallbacks = {
        "SERIE_70_FIJO": {
            "clave": "SERIE_70_FIJO", "nombre": "Serie 70 Fijo",
            "descuento_jamba": "10.00", "descuento_horizontal": "12.00",
            "descuento_junquillo": "15.00", "descuento_vidrio": "25.00"
        },
        "SERIE_1400_CORREDIZO": {
            "clave": "SERIE_1400_CORREDIZO", "nombre": "Serie 1400 Corredizo",
            "descuento_jamba": "125.00", "descuento_horizontal": "145.00",
            "descuento_junquillo": "18.00", "descuento_vidrio": "30.00"
        }
    }
    return fallbacks.get(clave, {
        "clave": clave, "nombre": clave,
        "descuento_jamba": "0", "descuento_horizontal": "0",
        "descuento_junquillo": "0", "descuento_vidrio": "0"
    })

# --- INTERFAZ DEL CROQUIS ---

# Título de la aplicación con tipografía manuscrita
st.markdown("<h1 style='text-align: center;'>✏️ CUADERNO DE CROQUIS - TALLER DE CORTES</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic; color: #5C544A;'>Manufactura Paramétrica Atómica (Dimensiones en Milímetros - mm)</p>", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("## ⚙️ Parámetros de Selección")
sistemas_df = obtener_sistemas()

if not sistemas_df.empty:
    seleccion_nombre = st.sidebar.selectbox(
        "Seleccione la Serie/Sistema:",
        options=sistemas_df["nombre"].tolist()
    )
    
    # Extraer clave
    clave_seleccionada = sistemas_df[sistemas_df["nombre"] == seleccion_nombre]["clave"].values[0]
else:
    clave_seleccionada = st.sidebar.selectbox(
        "Seleccione la Serie/Sistema:",
        options=["SERIE_70_FIJO", "SERIE_1400_CORREDIZO"]
    )

# Cargar detalles del sistema
detalles = obtener_sistema_detalle(clave_seleccionada)

st.sidebar.markdown("---")
st.sidebar.markdown(f"### 📋 Configuración Activa: **{detalles['nombre']}**")

# Mostrar coeficientes crudos extraídos de la BD en el sidebar
with st.sidebar.expander("Ver Coeficientes de Descuento"):
    st.write(f"**Jamba (V):** {detalles['descuento_jamba']}")
    st.write(f"**Horizontal (H):** {detalles['descuento_horizontal']}")
    st.write(f"**Junquillo:** {detalles['descuento_junquillo']}")
    st.write(f"**Vidrio:** {detalles['descuento_vidrio']}")

# Entradas principales
col_w, col_h = st.columns(2)

with col_w:
    ancho = st.number_input(
        "📐 ANCHO TOTAL (W) en mm:",
        min_value=1.0,
        max_value=10000.0,
        value=1500.0,
        step=5.0,
        format="%f"
    )

with col_h:
    alto = st.number_input(
        "📐 ALTO TOTAL (H) en mm:",
        min_value=1.0,
        max_value=10000.0,
        value=1200.0,
        step=5.0,
        format="%f"
    )

# --- CÁLCULOS PARAMÉTRICOS ---
corte_jamba = evaluar_corte(detalles["descuento_jamba"], alto, 'H')
corte_horizontal = evaluar_corte(detalles["descuento_horizontal"], ancho, 'W')

corte_junquillo_w = evaluar_corte(detalles["descuento_junquillo"], ancho, 'W')
corte_junquillo_h = evaluar_corte(detalles["descuento_junquillo"], alto, 'H')

corte_vidrio_w = evaluar_corte(detalles["descuento_vidrio"], ancho, 'W')
corte_vidrio_h = evaluar_corte(detalles["descuento_vidrio"], alto, 'H')

# --- RENDERIZADO DE RESULTADOS ---
st.markdown("<br><h2>📏 ORDEN DE CORTE Y DIMENSIONADO</h2>", unsafe_allow_html=True)

# Grid de resultados
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        label="🪟 Corte Jamba (Vertical)",
        value=f"{corte_jamba:.1f} mm"
    )
    st.caption("Corte para perfiles verticales de marco.")

with c2:
    st.metric(
        label="🪟 Corte Cabezal/Zoclo (Horiz.)",
        value=f"{corte_horizontal:.1f} mm"
    )
    st.caption("Corte para perfiles horizontales de marco.")

with c3:
    st.metric(
        label="🪵 Junquillos",
        value=f"W: {corte_junquillo_w:.1f} mm"
    )
    st.caption(f"H: {corte_junquillo_h:.1f} mm")

with c4:
    st.metric(
        label="💎 Vidrio Templado/Claro",
        value=f"{corte_vidrio_w:.1f} x {corte_vidrio_h:.1f}"
    )
    st.caption("Dimensiones finales de corte de vidrio en mm.")

# Representación gráfica abstracta estilo boceto
st.markdown("<br><h2>✏️ DIAGRAMA ESQUEMÁTICO (CROQUIS)</h2>", unsafe_allow_html=True)
st.markdown(f"""
<div style='border: 2px dashed #5C544A; padding: 25px; background-color: #FCF9F2; border-radius: 8px; font-family: "Courier Prime", monospace; color: #5C544A; margin-top: 10px;'>
    <div style='text-align: center; font-weight: bold;'>
        ANCHO DE CORTE HORIZONTAL: {corte_horizontal:.1f} mm (W: {ancho} mm)
    </div>
    <div style='display: flex; justify-content: space-between; align-items: center; height: 180px; border: 3px double #5C544A; margin: 15px auto; width: 60%; padding: 10px; background-color: #F7F3EB;'>
        <div style='font-size: 0.8rem; writing-mode: vertical-rl; text-orientation: mixed;'>
            JAMBA IZQUIERDA: {corte_jamba:.1f} mm
        </div>
        <div style='border: 1px dashed #B22222; width: 80%; height: 80%; display: flex; flex-direction: column; justify-content: center; align-items: center; background-color: #FFFDF9;'>
            <div style='font-weight: bold; color: #B22222;'>VIDRIO</div>
            <div style='font-size: 0.9rem; color: #B22222;'>{corte_vidrio_w:.1f} x {corte_vidrio_h:.1f} mm</div>
        </div>
        <div style='font-size: 0.8rem; writing-mode: vertical-rl; text-orientation: mixed;'>
            JAMBA DERECHA: {corte_jamba:.1f} mm (H: {alto} mm)
        </div>
    </div>
    <div style='text-align: center; font-size: 0.85rem;'>
        <b>Corte de Junquillos requeridos:</b> {corte_junquillo_w:.1f} mm (2 horizontales) / {corte_junquillo_h:.1f} mm (2 verticales)
    </div>
</div>
""", unsafe_allow_html=True)
import psycopg2.extras # import local to verify standard library uses

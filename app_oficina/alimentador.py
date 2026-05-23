"""
MundoCanceles - Aplicación de Oficina (Alimentador Técnico)
Diseñado con una interfaz tipo "Plano de Ingeniería / Blueprint".
Permite cargar archivos maestros de despieces (.json o .txt),
parsea sus coeficientes y realiza un UPSERT seguro en Postgres.
"""
import streamlit as st
import pandas as pd
import json
import re
from core.database import get_db_connection, limpiar_clave, limpiar_texto, extraer_mm_desde_formula

# Configuración de página
st.set_page_config(
    page_title="MundoCanceles - Oficina de Diseño",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS "Plano de Ingeniería / Blueprint"
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Courier+Prime:ital,wght@0,400;0,700;1,400;1,700&family=Orbitron:wght@400;700&display=swap');
    
    /* Fondo azul blueprint con rejilla */
    .stApp {
        background-color: #0B2447 !important;
        background-image: 
            linear-gradient(rgba(0, 173, 181, 0.15) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 173, 181, 0.15) 1px, transparent 1px) !important;
        background-size: 30px 30px !important;
        color: #E2F6F6 !important;
        font-family: 'Courier Prime', monospace !important;
    }
    
    /* Encabezados y títulos en fuente tipo radar/futurista */
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        color: #00ADB5 !important;
        text-shadow: 0px 0px 8px rgba(0, 173, 181, 0.5) !important;
        border-bottom: 1px solid #00ADB5 !important;
        padding-bottom: 8px;
    }
    
    /* Contenedor central principal */
    div.stAlert, div[data-testid="stBlock"] {
        background-color: rgba(25, 55, 109, 0.85) !important;
        border: 2px solid #00ADB5 !important;
        border-radius: 8px !important;
        box-shadow: 0px 0px 15px rgba(0, 173, 181, 0.2) !important;
    }
    
    /* Modificar el botón principal */
    .stButton>button {
        background-color: #00ADB5 !important;
        color: #0B2447 !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: bold !important;
        border: 2px solid #E2F6F6 !important;
        border-radius: 4px !important;
        padding: 10px 24px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton>button:hover {
        background-color: #E2F6F6 !important;
        color: #0B2447 !important;
        box-shadow: 0px 0px 12px #00ADB5 !important;
        transform: translateY(-1px);
    }
    
    /* Tablas de pandas / dataframes */
    div[data-testid="stTable"] table, div[data-testid="stDataFrame"] {
        border: 1px solid #00ADB5 !important;
        background-color: rgba(25, 55, 109, 0.9) !important;
        color: #E2F6F6 !important;
    }
    
    /* Elementos de subida de archivos */
    div[data-testid="stFileUploader"] {
        border: 2px dashed #00ADB5 !important;
        background-color: rgba(25, 55, 109, 0.5) !important;
        border-radius: 8px !important;
        padding: 15px !important;
    }
</style>
""", unsafe_allow_html=True)

def parsear_contenido_archivo(contenido_str, extension):
    """
    Parsea de forma robusta e inteligente datos cargados desde JSON o TXT.
    Normaliza y extrae los descuentos convertidos a milímetros.
    """
    sistemas_detectados = []
    
    if extension == "json":
        try:
            datos = json.loads(contenido_str)
            # Asegurar que sea una lista para procesar en bucle
            if isinstance(datos, dict):
                datos = [datos]
                
            for idx, item in enumerate(datos):
                clave = limpiar_clave(item.get("clave", f"SISTEMA_{idx+1}"))
                nombre = limpiar_texto(item.get("nombre", f"Sistema {clave}"))
                
                # Coeficientes crudos
                dj = item.get("descuento_jamba", "0")
                dh = item.get("descuento_horizontal", "0")
                dju = item.get("descuento_junquillo", "0")
                dv = item.get("descuento_vidrio", "0")
                
                sistemas_detectados.append({
                    "clave": clave,
                    "nombre": nombre,
                    "descuento_jamba_original": dj,
                    "descuento_jamba_mm": extraer_mm_desde_formula(dj),
                    "descuento_horizontal_original": dh,
                    "descuento_horizontal_mm": extraer_mm_desde_formula(dh),
                    "descuento_junquillo_original": dju,
                    "descuento_junquillo_mm": extraer_mm_desde_formula(dju),
                    "descuento_vidrio_original": dv,
                    "descuento_vidrio_mm": extraer_mm_desde_formula(dv),
                })
        except json.JSONDecodeError as je:
            st.error(f"❌ Error al decodificar JSON técnico: {je}")
            
    elif extension == "txt":
        # Formato de clave=valor, soporta múltiples bloques separados por '---' o línea en blanco
        bloques = re.split(r'\n\s*---\s*\n|\n\s*\n', contenido_str.strip())
        for idx, bloque in enumerate(bloques):
            if not bloque.strip():
                continue
                
            lineas = bloque.strip().split("\n")
            valores = {}
            for linea in lineas:
                if "=" in linea:
                    k, v = linea.split("=", 1)
                    valores[k.strip().lower()] = v.strip()
                    
            if valores:
                clave = limpiar_clave(valores.get("clave", f"SISTEMA_TXT_{idx+1}"))
                nombre = limpiar_texto(valores.get("nombre", f"Sistema {clave}"))
                
                dj = valores.get("descuento_jamba", "0")
                dh = valores.get("descuento_horizontal", "0")
                dju = valores.get("descuento_junquillo", "0")
                dv = valores.get("descuento_vidrio", "0")
                
                sistemas_detectados.append({
                    "clave": clave,
                    "nombre": nombre,
                    "descuento_jamba_original": dj,
                    "descuento_jamba_mm": extraer_mm_desde_formula(dj),
                    "descuento_horizontal_original": dh,
                    "descuento_horizontal_mm": extraer_mm_desde_formula(dh),
                    "descuento_junquillo_original": dju,
                    "descuento_junquillo_mm": extraer_mm_desde_formula(dju),
                    "descuento_vidrio_original": dv,
                    "descuento_vidrio_mm": extraer_mm_desde_formula(dv),
                })
                
    return sistemas_detectados

def guardar_en_base_de_datos(lista_sistemas):
    """
    Realiza un UPSERT seguro de forma transaccional (ON CONFLICT DO UPDATE) en Postgres.
    """
    conn = None
    exitos = 0
    errores = 0
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            for sys in lista_sistemas:
                try:
                    cur.execute("""
                        INSERT INTO sistemas_ventana (clave, nombre, descuento_jamba, descuento_horizontal, descuento_junquillo, descuento_vidrio)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (clave)
                        DO UPDATE SET
                            nombre = EXCLUDED.nombre,
                            descuento_jamba = EXCLUDED.descuento_jamba,
                            descuento_horizontal = EXCLUDED.descuento_horizontal,
                            descuento_junquillo = EXCLUDED.descuento_junquillo,
                            descuento_vidrio = EXCLUDED.descuento_vidrio;
                    """, (
                        sys["clave"],
                        sys["nombre"],
                        str(sys["descuento_jamba_mm"]),
                        str(sys["descuento_horizontal_mm"]),
                        str(sys["descuento_junquillo_mm"]),
                        str(sys["descuento_vidrio_mm"])
                    ))
                    exitos += 1
                except Exception as row_error:
                    errores += 1
                    st.warning(f"Error procesando clave '{sys['clave']}': {row_error}")
            
            # Confirmar transacción completa si no hubo errores críticos de conexión
            conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        st.error(f"❌ Error transaccional crítico en Postgres: {e}")
        return False, 0, 0
    finally:
        if conn:
            conn.close()
            
    return True, exitos, errores

# --- RENDERIZADO DE INTERFAZ ---

st.markdown("<h1 style='text-align: center;'>🛰️ ADUANA TÉCNICA - ALIMENTADOR DE SISTEMAS</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic; color: #00ADB5;'>Gestión Paramétrica de Coeficientes e Ingestión Segura a la Base de Datos</p>", unsafe_allow_html=True)

st.markdown("### 📥 1. Cargar Archivo de Despiece")
st.write("Sube un archivo técnico en formato **.json** o **.txt** con la estructura de cortes de ventanas.")

col_upload, col_instructions = st.columns([2, 1])

with col_upload:
    archivo_cargado = st.file_uploader(
        "Arrastra aquí tu archivo maestro o búscalo en tu explorador:",
        type=["json", "txt"]
    )

with col_instructions:
    st.markdown("""
    **💡 Estructura Recomendada:**
    
    *Ejemplo JSON:*
    ```json
    {
      "clave": "SERIE_80_CORREDIZO",
      "nombre": "Serie 80 Corredizo",
      "descuento_jamba": "1.2 cm",
      "descuento_horizontal": "14 mm",
      "descuento_junquillo": "1.8 cm",
      "descuento_vidrio": "H - 2.5 cm"
    }
    ```
    """)

if archivo_cargado is not None:
    contenido = archivo_cargado.read().decode("utf-8")
    ext = archivo_cargado.name.split(".")[-1].lower()
    
    # Procesar
    sistemas_parseados = parsear_contenido_archivo(contenido, ext)
    
    if sistemas_parseados:
        st.markdown("### 🔍 2. Preview de Sanidad e Integridad de Datos")
        st.write("Verifique cómo se han transformado sus unidades en milímetros (mm) atómicos antes de subirlos a la base de datos:")
        
        # Convertir a DataFrame para visualización impecable
        df_preview = pd.DataFrame(sistemas_parseados)
        
        # Reordenar y renombrar columnas para máxima legibilidad humana
        df_human = df_preview[[
            "clave", "nombre", 
            "descuento_jamba_original", "descuento_jamba_mm",
            "descuento_horizontal_original", "descuento_horizontal_mm",
            "descuento_junquillo_original", "descuento_junquillo_mm",
            "descuento_vidrio_original", "descuento_vidrio_mm"
        ]].copy()
        
        df_human.columns = [
            "Clave Única", "Nombre del Sistema", 
            "Jamba (Original)", "Jamba (mm)",
            "Horizontal (Original)", "Horizontal (mm)",
            "Junquillo (Original)", "Junquillo (mm)",
            "Vidrio (Original)", "Vidrio (mm)"
        ]
        
        st.dataframe(df_human, use_container_width=True)
        
        st.markdown("### 💾 3. Ingestión Segura en Base de Datos")
        st.write("Al presionar el botón de abajo, se realizará un **UPSERT transaccional**. Si el sistema ya existe, se actualizarán sus coeficientes. Si no existe, se creará uno nuevo.")
        
        if st.button("🚀 CONFIRMAR E INGERIR EN POSTGRESQL"):
            with st.spinner("Estableciendo transacción segura con Postgres..."):
                ok, exitosos, fallidos = guardar_en_base_de_datos(sistemas_parseados)
                if ok:
                    st.success(f"🎉 Ingestión completada con éxito. {exitosos} registros creados/actualizados, {fallidos} fallidos.")
                else:
                    st.error("Hubo un problema al realizar la transacción en la base de datos.")
                    
    else:
        st.warning("⚠️ No se detectó ningún sistema de ventana válido en el archivo. Verifique el formato e intente nuevamente.")
else:
    # Mostrar tabla de sistemas cargados actualmente
    st.markdown("### 📊 Coeficientes de Sistemas Activos en el Servidor")
    try:
        conn = get_db_connection()
        df_activos = pd.read_sql("SELECT clave, nombre, descuento_jamba, descuento_horizontal, descuento_junquillo, descuento_vidrio FROM sistemas_ventana ORDER BY created_at DESC;", conn)
        conn.close()
        
        if not df_activos.empty:
            df_activos.columns = ["Clave Única", "Nombre", "Descuento Jamba", "Descuento Horizontal", "Descuento Junquillo", "Descuento Vidrio"]
            st.dataframe(df_activos, use_container_width=True)
        else:
            st.info("No hay sistemas de ventana cargados actualmente en la base de datos.")
    except Exception as e:
        st.error(f"No se pudo cargar la vista de sistemas activos: {e}")

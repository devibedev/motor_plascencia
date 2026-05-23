# app.py
import streamlit as st
import pandas as pd
import psycopg2
from psycopg2 import sql
import os

# ----------------------------------------------------------------------
# 1. INYECCIÓN DE CSS PARA CORREGIR EL CONTRASTE DE LOS SELECTBOX
# ----------------------------------------------------------------------
st.markdown("""
    <style>
    /* --- CORRECCIÓN DE ALTO CONTRASTE PARA SELECTBOX (OPCIONES DESPLEGADAS) --- */
    div[data-baseweb="popover"] ul, 
    ul[role="listbox"] {
        background-color: #FFFFFF !important;
        border: 2px solid #000000 !important;
    }

    div[data-baseweb="popover"] li, 
    ul[role="listbox"] li, 
    div[data-baseweb="select"] * {
        color: #000000 !important;
        background-color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    /* Efecto Hover e interacción activa obligatoria */
    div[data-baseweb="popover"] li:hover, 
    ul[role="listbox"] li:hover,
    div[role="option"]:hover {
        background-color: #000000 !important;
        color: #FFFFFF !important;
    }
    
    /* Corrección del texto dentro del contenedor cerrado del selectbox */
    div[data-baseweb="select"] div[aria-selected="true"] {
        color: #000000 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# 2. CONFIGURACIÓN DE LA BASE DE DATOS (Ajusta según tu Docker)
# ----------------------------------------------------------------------
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "atoms_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

@st.cache_resource
def get_db_connection():
    """Crea y cachea la conexión a la base de datos."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False  # Control manual de transacciones
        return conn
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        st.stop()

# ----------------------------------------------------------------------
# 3. FUNCIONES DE BASE DE DATOS (Modularizadas como en queries.py)
# ----------------------------------------------------------------------
def obtener_sistemas_disponibles(conn):
    """Obtiene todos los sistemas registrados en catalogo_sistemas."""
    try:
        query = "SELECT nombre_sistema FROM catalogo_sistemas ORDER BY nombre_sistema;"
        return pd.read_sql(query, conn)
    except Exception:
        return pd.DataFrame(columns=["nombre_sistema"])

def obtener_detalles_sistema(conn, nombre_sistema):
    """Devuelve los descuentos e IX de un sistema en concreto."""
    query = sql.SQL("""
        SELECT descuento_jamba_mm, descuento_junquillo_mm,
               descuento_vidrio_w_mm, descuento_vidrio_h_mm,
               momento_inercia_ix
        FROM catalogo_sistemas
        WHERE nombre_sistema = %s;
    """)
    try:
        cur = conn.cursor()
        cur.execute(query, (nombre_sistema,))
        result = cur.fetchone()
        cur.close()
        return result
    except Exception as e:
        st.error(f"Error al leer el sistema {nombre_sistema}: {e}")
        return None

def obtener_vidrios(conn):
    """Obtiene el catálogo de vidrios disponibles."""
    try:
        return pd.read_sql("SELECT clave, tipo, espesor_mm FROM vidrios_medidas;", conn)
    except Exception:
        return pd.DataFrame(columns=["clave", "tipo", "espesor_mm"])

def registrar_orden_produccion(conn, nombre_proyecto, items_materiales):
    """
    Guarda el proyecto y su lista de materiales en la BD.
    items_materiales: lista de diccionarios con claves:
        tipo, clave, descripcion, cantidad, unidad
    """
    cur = conn.cursor()
    try:
        # Insertar proyecto
        cur.execute(
            "INSERT INTO proyectos (nombre) VALUES (%s) RETURNING id_proyecto;",
            (nombre_proyecto,)
        )
        id_proy = cur.fetchone()[0]

        # Insertar cada renglón de materiales
        insert_material = """
            INSERT INTO proyecto_materiales_detalles
                (id_proyecto, tipo_material, clave_material, descripcion, cantidad, unidad_medida)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        for item in items_materiales:
            cur.execute(insert_material, (
                id_proy,
                item["tipo"],
                item["clave"],
                item["descripcion"],
                item["cantidad"],
                item["unidad"]
            ))
        conn.commit()
        return id_proy
    except Exception as e:
        conn.rollback()
        st.error(f"No se pudo guardar el proyecto: {e}")
        return None
    finally:
        cur.close()

# ----------------------------------------------------------------------
# 4. INTERFAZ PRINCIPAL DE STREAMLIT
# ----------------------------------------------------------------------
def main():
    st.title("🏭 Planta de Producción – Corte Dinámico de Aluminio")
    st.markdown("Utiliza los **sistemas reales** cargados por la Maquinita Tragadata desde la base de datos.")

    # Conexión a la BD (cacheada)
    conn = get_db_connection()

    # Cargar sistemas disponibles
    df_sistemas = obtener_sistemas_disponibles(conn)
    if df_sistemas.empty:
        st.warning("⚠️ No hay sistemas en el catálogo. Usando valores genéricos predeterminados.")
        # Valores de respaldo para poder operar sin BD
        desc_jamba, desc_junquillo, desc_vidrio_w, desc_vidrio_h, ix_perfil = 55, 56, 42, 42, 1.85
        sistema_seleccionado = "Sistema Genérico"
    else:
        sistema_seleccionado = st.sidebar.selectbox(
            "1️⃣ Selecciona la Línea de Aluminio",
            df_sistemas["nombre_sistema"].tolist()
        )
        detalles = obtener_detalles_sistema(conn, sistema_seleccionado)
        if detalles:
            desc_jamba, desc_junquillo, desc_vidrio_w, desc_vidrio_h, ix_perfil = detalles
            st.sidebar.success(f"✅ Sistema cargado: Ix = {ix_perfil:.3f}")
        else:
            st.sidebar.error("Error al cargar el sistema. Se usarán valores por defecto.")
            desc_jamba, desc_junquillo, desc_vidrio_w, desc_vidrio_h, ix_perfil = 55, 56, 42, 42, 1.85

    # Dimensiones de la ventana (en mm)
    w_input = st.sidebar.number_input("Ancho del vano (mm)", min_value=100, max_value=5000, value=1000, step=10)
    h_input = st.sidebar.number_input("Alto del vano (mm)", min_value=100, max_value=5000, value=1200, step=10)

    # Catálogo de vidrios
    df_vidrios = obtener_vidrios(conn)
    vidrio_clave = None
    if not df_vidrios.empty:
        vidrio_opciones = df_vidrios["tipo"].tolist()
        vidrio_elegido = st.sidebar.selectbox("2️⃣ Tipo de Vidrio", vidrio_opciones)
        vidrio_row = df_vidrios[df_vidrios["tipo"] == vidrio_elegido].iloc[0]
        vidrio_clave = vidrio_row["clave"]
        espesor_vidrio = vidrio_row["espesor_mm"]
        desc_vidrio = f"{vidrio_elegido} ({espesor_vidrio} mm)"
    else:
        st.sidebar.info("Catálogo de vidrios no disponible.")
        desc_vidrio = "Vidrio estándar (sin BD)"

    # ------------------------------------------------------------------
    # Cálculos de corte (como en tu lógica original, pero dinámica)
    # ------------------------------------------------------------------
    corte_cabezal = w_input
    corte_zoclo = w_input
    corte_jamba = h_input - desc_jamba
    corte_junquillo_horizontal = w_input - desc_junquillo    # 2 piezas
    corte_junquillo_vertical = h_input - desc_junquillo      # 2 piezas (usamos mismo descuento)

    ancho_vidrio = w_input - desc_vidrio_w
    alto_vidrio = h_input - desc_vidrio_h

    # Mostramos los resultados en una tabla amigable
    st.subheader("📋 Despiece de Corte")
    data = {
        "Componente": [
            "Cabezal", "Zoclo (Suelo)", "Jamba (2 piezas)",
            "Junquillo horizontal (2 piezas)", "Junquillo vertical (2 piezas)",
            "Vidrio"
        ],
        "Longitud (mm)": [
            corte_cabezal, corte_zoclo, corte_jamba,
            corte_junquillo_horizontal, corte_junquillo_vertical,
            f"{ancho_vidrio:.1f} × {alto_vidrio:.1f}"
        ],
        "Unidad": ["mm", "mm", "mm c/u", "mm c/u", "mm c/u", "mm (ancho × alto)"]
    }
    df_cortes = pd.DataFrame(data)
    st.table(df_cortes)

    # Cálculo adicional: deflexión estimada (opcional)
    st.caption(f"📐 Momento de inercia Ix del perfil: {ix_perfil:.3f} cm⁴")

    # ------------------------------------------------------------------
    # Guardar proyecto en la base de datos
    # ------------------------------------------------------------------
    st.subheader("💾 Registrar Proyecto")
    nombre_proyecto = st.text_input("Nombre del proyecto o número de obra", "")
    if st.button("Guardar orden de producción en la base de datos"):
        if not nombre_proyecto.strip():
            st.warning("Debes ingresar un nombre de proyecto.")
        else:
            # Construimos la lista de materiales (BOM)
            materiales = [
                {"tipo": "perfil", "clave": "CABEZAL", "descripcion": f"Cabezal {sistema_seleccionado}",
                 "cantidad": corte_cabezal, "unidad": "mm"},
                {"tipo": "perfil", "clave": "ZOCLO", "descripcion": f"Zoclo {sistema_seleccionado}",
                 "cantidad": corte_zoclo, "unidad": "mm"},
                {"tipo": "perfil", "clave": "JAMBA", "descripcion": f"Jamba {sistema_seleccionado}",
                 "cantidad": corte_jamba * 2, "unidad": "mm"},  # total mm de jambas
                {"tipo": "perfil", "clave": "JUNQUILLO", "descripcion": f"Junquillo {sistema_seleccionado}",
                 "cantidad": (corte_junquillo_horizontal * 2) + (corte_junquillo_vertical * 2), "unidad": "mm"},
                {"tipo": "vidrio", "clave": vidrio_clave if vidrio_clave else "VD-DEFAULT",
                 "descripcion": f"Vidrio {desc_vidrio}",
                 "cantidad": 1, "unidad": "pza"},
            ]
            id_proyecto = registrar_orden_produccion(conn, nombre_proyecto.strip(), materiales)
            if id_proyecto:
                st.success(f"✅ Proyecto registrado con ID {id_proyecto} – materiales guardados.")
            else:
                st.error("No se pudo guardar el proyecto.")

if __name__ == "__main__":
    main()
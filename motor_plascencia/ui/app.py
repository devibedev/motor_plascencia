"""
Punto de entrada de la aplicación Streamlit para la Planta de Producción.
Utiliza los módulos config, database, src y ui/styles.
"""

import streamlit as st
import pandas as pd

# Módulos propios
from config.settings import validate_db_config
from database.connection import get_connection, release_connection
from database.queries import (
    obtener_sistemas_disponibles,
    obtener_detalles_sistema,
    obtener_vidrios,
    registrar_orden_produccion,
)
from ui.styles import high_contrast_css

# ----------------------------------------------------------------------
# Inyectar CSS para corregir contraste de selectbox
# ----------------------------------------------------------------------
st.markdown(high_contrast_css, unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Conexión a la base de datos (cacheada para toda la sesión)
# ----------------------------------------------------------------------
@st.cache_resource
def get_db_connection():
    """Obtiene y cachea una conexión del pool."""
    return get_connection()

# ----------------------------------------------------------------------
# Funciones de la interfaz
# ----------------------------------------------------------------------
def sidebar(conn):
    """
    Renderiza la barra lateral con los selectores y devuelve los valores
    necesarios para los cálculos.
    """
    st.sidebar.title("⚙️ Configuración del Corte")

    # Cargar sistemas desde la BD
    df_sistemas = obtener_sistemas_disponibles(conn)

    if df_sistemas.empty:
        st.sidebar.warning("⚠️ No hay sistemas en el catálogo.")
        sistema_seleccionado = None
        desc_jamba = desc_junquillo = desc_vidrio_w = desc_vidrio_h = 55
        ix_perfil = 1.85
    else:
        sistema_seleccionado = st.sidebar.selectbox(
            "1️⃣ Línea de Aluminio",
            df_sistemas["nombre_sistema"].tolist(),
        )
        # Obtener descuentos reales del sistema
        detalles = obtener_detalles_sistema(conn, sistema_seleccionado)
        if detalles:
            desc_jamba, desc_junquillo, desc_vidrio_w, desc_vidrio_h, ix_perfil = detalles
            st.sidebar.success(f"Ix = {ix_perfil:.3f} cm⁴")
        else:
            st.sidebar.error("Error al cargar el sistema. Usando valores genéricos.")
            desc_jamba, desc_junquillo, desc_vidrio_w, desc_vidrio_h, ix_perfil = 55, 56, 42, 42, 1.85

    # Dimensiones del vano
    w_input = st.sidebar.number_input(
        "Ancho del vano (mm)", min_value=100, max_value=5000, value=1000, step=10
    )
    h_input = st.sidebar.number_input(
        "Alto del vano (mm)", min_value=100, max_value=5000, value=1200, step=10
    )

    # Catálogo de vidrios
    df_vidrios = obtener_vidrios(conn)
    if not df_vidrios.empty:
        tipo_vidrio = st.sidebar.selectbox("2️⃣ Tipo de Vidrio", df_vidrios["tipo"].tolist())
        vidrio_row = df_vidrios[df_vidrios["tipo"] == tipo_vidrio].iloc[0]
        vidrio_clave = vidrio_row["clave"]
        espesor = vidrio_row["espesor_mm"]
        desc_vidrio = f"{tipo_vidrio} ({espesor} mm)"
    else:
        st.sidebar.info("Catálogo de vidrios no disponible.")
        vidrio_clave = "VD-DEFAULT"
        desc_vidrio = "Vidrio estándar (sin BD)"
        espesor = None

    return {
        "sistema": sistema_seleccionado if not df_sistemas.empty else "Genérico",
        "w": w_input,
        "h": h_input,
        "desc_jamba": desc_jamba,
        "desc_junquillo": desc_junquillo,
        "desc_vidrio_w": desc_vidrio_w,
        "desc_vidrio_h": desc_vidrio_h,
        "ix": ix_perfil,
        "vidrio_clave": vidrio_clave,
        "vidrio_desc": desc_vidrio,
        "espesor": espesor,
    }


def calcular_cortes(params):
    """
    Realiza los cálculos de corte a partir de los parámetros.
    Retorna un diccionario con las longitudes calculadas.
    """
    w = params["w"]
    h = params["h"]
    return {
        "Cabezal": w,
        "Zoclo (Suelo)": w,
        "Jamba (2 piezas)": h - params["desc_jamba"],
        "Junquillo horizontal (2 piezas)": w - params["desc_junquillo"],
        "Junquillo vertical (2 piezas)": h - params["desc_junquillo"],
        "Vidrio (ancho)": w - params["desc_vidrio_w"],
        "Vidrio (alto)": h - params["desc_vidrio_h"],
    }


def mostrar_resultados(cortes, params):
    """Muestra la tabla de cortes y detalles adicionales."""
    st.subheader("📋 Despiece de Corte")

    data = {
        "Componente": list(cortes.keys()),
        "Longitud (mm)": [f"{v:.1f}" if isinstance(v, float) else str(v) for v in cortes.values()],
        "Unidad": ["mm", "mm", "mm c/u", "mm c/u", "mm c/u", "mm", "mm"],
    }
    df = pd.DataFrame(data)
    st.table(df)

    st.caption(f"📐 Momento de inercia Ix del perfil: {params['ix']:.3f} cm⁴")
    st.caption(f"🪟 Vidrio seleccionado: {params['vidrio_desc']}")


def guardar_proyecto(conn, params, cortes):
    """Interfaz para guardar el proyecto en la base de datos."""
    st.subheader("💾 Registrar Proyecto")
    nombre = st.text_input("Nombre del proyecto o número de obra", "")

    if st.button("Guardar orden de producción"):
        if not nombre.strip():
            st.warning("Debes ingresar un nombre de proyecto.")
            return

        # Construir lista de materiales (BOM)
        materiales = [
            {
                "tipo": "perfil",
                "clave": "CABEZAL",
                "descripcion": f"Cabezal {params['sistema']}",
                "cantidad": cortes["Cabezal"],
                "unidad": "mm",
            },
            {
                "tipo": "perfil",
                "clave": "ZOCLO",
                "descripcion": f"Zoclo {params['sistema']}",
                "cantidad": cortes["Zoclo (Suelo)"],
                "unidad": "mm",
            },
            {
                "tipo": "perfil",
                "clave": "JAMBA",
                "descripcion": f"Jamba {params['sistema']}",
                "cantidad": cortes["Jamba (2 piezas)"] * 2,  # total mm de jambas
                "unidad": "mm",
            },
            {
                "tipo": "perfil",
                "clave": "JUNQUILLO",
                "descripcion": f"Junquillo {params['sistema']}",
                "cantidad": (
                    cortes["Junquillo horizontal (2 piezas)"] * 2
                    + cortes["Junquillo vertical (2 piezas)"] * 2
                ),
                "unidad": "mm",
            },
            {
                "tipo": "vidrio",
                "clave": params["vidrio_clave"],
                "descripcion": params["vidrio_desc"],
                "cantidad": 1,
                "unidad": "pza",
            },
        ]

        id_proy = registrar_orden_produccion(conn, nombre.strip(), materiales)
        if id_proy:
            st.success(f"✅ Proyecto registrado con ID {id_proy}. Materiales guardados.")
        else:
            st.error("❌ No se pudo guardar el proyecto.")


# ----------------------------------------------------------------------
# Función principal
# ----------------------------------------------------------------------
def main():
    st.title("🏭 Planta de Producción – Corte Dinámico de Aluminio")
    st.markdown(
        "Utiliza los **sistemas reales** cargados por la Maquinita Tragadata "
        "desde la base de datos."
    )

    # Conexión a BD
    try:
        conn = get_db_connection()
    except Exception as e:
        st.error(f"Error de conexión a la base de datos: {e}")
        st.stop()

    # Barra lateral y parámetros
    params = sidebar(conn)

    # Cálculos
    cortes = calcular_cortes(params)

    # Resultados
    mostrar_resultados(cortes, params)

    # Registro de proyecto
    guardar_proyecto(conn, params, cortes)

    # Liberar conexión al cerrar (opcional, Streamlit lo maneja al terminar)
    # release_connection(conn)  # No necesario con cache_resource


if __name__ == "__main__":
    main()
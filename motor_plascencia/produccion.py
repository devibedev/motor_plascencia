"""
App Taller - Producción Paramétrica
Visualización de cortes con estilo Sketchbook.
"""
import streamlit as st
import pandas as pd
from core.database import get_db_connection

st.set_page_config(page_title="Taller | MundoCanceles", layout="wide")

# Estilo Cuaderno de Croquis
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Architects+Daughter&family=Courier+Prime&display=swap');
    
    .stApp {
        background-color: #FDFBF7;
        background-image: radial-gradient(#D1D1D1 1px, transparent 1px);
        background-size: 20px 20px;
    }
    
    h1, h2, h3, .stMetric label {
        font-family: 'Architects Daughter', cursive !important;
        color: #2C3E50;
    }
    
    .stMetric value {
        font-family: 'Courier Prime', monospace !important;
    }
    
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.8);
        border: 1px solid #BDC3C7;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

def main():
    st.title("⚒️ Cuaderno de Cortes - Planta")
    
    conn = get_db_connection()
    if not conn:
        st.error("Error: No hay conexión con la base de datos de átomos.")
        return

    # Sidebar: Selección de Sistema
    st.sidebar.header("Configuración")
    try:
        sistemas_df = pd.read_sql("SELECT nombre_sistema FROM sistemas_ventana ORDER BY nombre_sistema", conn)
        sistema = st.sidebar.selectbox("Selecciona la Serie", sistemas_df['nombre_sistema'])
    except:
        st.sidebar.warning("Tabla 'sistemas_ventana' no inicializada.")
        return

    # Dimensiones Base
    ancho_vano = st.sidebar.number_input("Ancho Vano (mm)", min_value=0, value=1000)
    alto_vano = st.sidebar.number_input("Alto Vano (mm)", min_value=0, value=1000)

    # Consulta de Descuentos
    cur = conn.cursor()
    cur.execute("""
        SELECT desc_jamba, desc_junquillo, desc_vidrio_w, desc_vidrio_h 
        FROM sistemas_ventana WHERE nombre_sistema = %s
    """, (sistema,))
    params = cur.fetchone()
    cur.close()
    conn.close()

    if params:
        dj, dju, dvw, dvh = params
        
        # Cálculos Atómicos (mm)
        corte_h = ancho_vano
        corte_v = alto_vano - dj
        junquillo_h = ancho_vano - dju
        junquillo_v = alto_vano - dju
        vidrio_w = ancho_vano - dvw
        vidrio_h = alto_vano - dvh

        st.subheader(f"Despiece: {sistema}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Cabezal/Zoclo (mm)", f"{corte_h}")
            st.metric("Vidrio Ancho (mm)", f"{vidrio_w}")
        
        with col2:
            st.metric("Jambas (mm)", f"{corte_v}")
            st.metric("Vidrio Alto (mm)", f"{vidrio_h}")
            
        with col3:
            st.metric("Junquillo H (mm)", f"{junquillo_h}")
            st.metric("Junquillo V (mm)", f"{junquillo_v}")
            
        st.info(f"Nota: Todos los valores están en milímetros (mm).")
    else:
        st.error("No se encontraron parámetros para este sistema.")

if __name__ == "__main__":
    main()
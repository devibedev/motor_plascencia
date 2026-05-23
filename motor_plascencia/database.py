"""
Core Database Module - MundoCanceles
Manejo de conexiones y utilidades de conversión paramétrica.
"""
import psycopg2
import re
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Establece conexión con el servicio Postgres."""
    try:
        conn = psycopg2.connect(
            host="postgres_db",
            database="atoms_db",
            user="maestro_aluminero",
            password="password_seguro123"
        )
        return conn
    except Exception as e:
        print(f"Error crítico de conexión: {e}")
        return None

def limpiar_clave(valor):
    """Normaliza claves de sistemas (mayúsculas y sin espacios)."""
    return str(valor).strip().upper() if valor else ""

def limpiar_texto(valor):
    """Limpia descripciones técnicas."""
    return str(valor).strip() if valor else ""

def extraer_mm_desde_formula(formula):
    """
    Convierte valores de fórmulas (cm, in, mm) a flotantes en milímetros.
    Regex: Busca número y opcionalmente la unidad.
    """
    if not formula: return 0.0
    
    # Extraer magnitud y unidad
    match = re.search(r"(\d+(\.\d+)?)\s*(cm|in|mm)?", str(formula).lower())
    if not match:
        return 0.0
        
    valor = float(match.group(1))
    unidad = match.group(3)
    
    if unidad == "cm":
        return valor * 10.0
    elif unidad == "in":
        return valor * 25.4
    return valor # Default mm
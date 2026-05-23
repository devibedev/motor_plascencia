"""
MundoCanceles Database and Core Utilities
Provides robust database connections and pure mathematical / text utility functions.
"""
import os
import re
import psycopg2
import psycopg2.extras

DB_HOST = os.getenv("DB_HOST", "postgres_db")
DB_NAME = os.getenv("DB_NAME", "atoms_db")
DB_USER = os.getenv("DB_USER", "maestro_aluminero")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password_seguro123")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_db_connection():
    """
    Establece una conexión robusta y limpia con la base de datos PostgreSQL.
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            connect_timeout=5
        )
        return conn
    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")
        raise e

def init_database_schema():
    """
    Inicializa el esquema de base de datos en caso de que no exista la tabla principal.
    Esto permite que la aplicación arranque de inmediato.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Crear la tabla de sistemas si no existe
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sistemas_ventana (
                    clave VARCHAR(100) PRIMARY KEY,
                    nombre VARCHAR(255) NOT NULL,
                    descuento_jamba VARCHAR(100) DEFAULT '0',
                    descuento_horizontal VARCHAR(100) DEFAULT '0',
                    descuento_junquillo VARCHAR(100) DEFAULT '0',
                    descuento_vidrio VARCHAR(100) DEFAULT '0',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Insertar algunos valores semilla si la tabla está vacía
            cur.execute("SELECT COUNT(*) FROM sistemas_ventana;")
            if cur.fetchone()[0] == 0:
                seed_data = [
                    ("SERIE_70_FIJO", "Serie 70 Fijo", "10", "12", "15", "25"),
                    ("SERIE_1400_CORREDIZO", "Serie 1400 Corredizo", "12.5 cm", "14.5 cm", "18.0 mm", "30.0 mm"),
                    ("SERIE_3_PULGADAS", "Serie Fija 3 Pulgadas", "2 in", "1.5 pulg", "0.5 in", "3 in")
                ]
                for row in seed_data:
                    cur.execute("""
                        INSERT INTO sistemas_ventana (clave, nombre, descuento_jamba, descuento_horizontal, descuento_junquillo, descuento_vidrio)
                        VALUES (%s, %s, %s, %s, %s, %s);
                    """, row)
            conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error inicializando el esquema: {e}")
    finally:
        if conn:
            conn.close()

def limpiar_clave(valor):
    """
    Función pura para limpiar y estandarizar claves identificadoras de sistemas.
    Quita espacios innecesarios, caracteres especiales y convierte a mayúsculas.
    """
    if valor is None:
        return ""
    # Quitar acentos y caracteres raros, pasar a mayúsculas
    s = str(valor).strip().upper()
    s = re.sub(r'[^A-Z0-9_]', '_', s)
    s = re.sub(r'_+', '_', s)
    return s.strip('_')

def limpiar_texto(valor):
    """
    Función pura para limpiar texto del usuario. Remueve espacios dobles y datos nulos de forma defensiva.
    """
    if valor is None:
        return ""
    return " ".join(str(valor).strip().split())

def extraer_mm_desde_formula(formula):
    """
    Analiza una cadena de texto técnica y convierte cualquier unidad de medida (cm, pulgadas/in, mm) a mm.
    Si la entrada es una fórmula completa (ej. 'H - 1.5 cm'), convierte los valores numéricos con unidades a mm.
    Si es una dimensión simple (ej. '12.5 cm'), retorna el valor float correspondiente en mm.
    
    Equivalencias:
    - 1 cm = 10 mm
    - 1 in = 25.4 mm
    - 1 mm = 1 mm
    """
    if not formula:
        return "0"
        
    formula_str = str(formula).strip().lower()
    
    # Patrón para identificar números seguidos de unidades opcionales
    # Grupo 1: Número (entero o decimal)
    # Grupo 2: Espacio opcional seguido de la unidad (cm, mm, in, pulgadas, pulg, ", inch, inches)
    pattern = r"([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|in|pulgadas|pulg|inch|inches|\")?"
    
    def replacer(match):
        value = float(match.group(1))
        unit = match.group(2)
        
        if not unit:
            # Si no hay unidad especificada, asumimos mm por defecto (nuestra unidad atómica)
            return f"{value}"
            
        unit = unit.replace('"', '').strip()
        
        if unit in ['cm', 'centimetro', 'centimetros', 'cms']:
            val_mm = value * 10.0
        elif unit in ['in', 'pulgada', 'pulgadas', 'pulg', 'inch', 'inches', '']:
            val_mm = value * 25.4
        elif unit in ['mm', 'milimetro', 'milimetros', 'mms']:
            val_mm = value
        else:
            val_mm = value
            
        # Retornamos el valor en milímetros con precisión flotante
        return f"{val_mm:.2f}"

    # Reemplazamos todos los números con unidades por su equivalente en mm
    formula_con_mm = re.sub(pattern, replacer, formula_str)
    
    # Si la fórmula resultante es un número simple, retornamos el flotante
    try:
        if re.match(r"^[0-9]+(?:\.[0-9]+)?$", formula_con_mm):
            return float(formula_con_mm)
    except ValueError:
        pass
        
    return formula_con_mm

# Ejecutar inicialización de esquema al importar el módulo
init_database_schema()

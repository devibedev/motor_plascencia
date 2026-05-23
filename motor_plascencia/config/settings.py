"""
Carga las variables de entorno desde un archivo .env (si existe)
y expone las configuraciones necesarias para la aplicación.
"""

import os
from dotenv import load_dotenv

# Cargar .env ubicado en la raíz del proyecto (motor_plascencia/.env)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Base de datos
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "atoms_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# Opcional: clave secreta para Streamlit (si la necesitas en el futuro)
SECRET_KEY = os.getenv("SECRET_KEY", None)

# Construcción de la cadena de conexión (para psycopg2)
DB_CONFIG = {
    "host": DB_HOST,
    "port": DB_PORT,
    "dbname": DB_NAME,
    "user": DB_USER,
    "password": DB_PASSWORD,
}

# Validación simple (puedes expandir con pydantic si lo deseas)
def validate_db_config():
    """Lanza una excepción si faltan parámetros críticos."""
    if not DB_NAME or not DB_USER or DB_PASSWORD == "postgres":
        import warnings
        warnings.warn("Estás usando credenciales por defecto. Cambia el .env en producción.")
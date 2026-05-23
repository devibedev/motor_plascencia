"""
Gestión de conexiones a PostgreSQL usando un pool de hilos.
Adecuado para entornos multi-hilo como Streamlit.
"""

import psycopg2
from psycopg2 import pool
from config.settings import DB_CONFIG, validate_db_config

# Variable global para el pool (se inicializa bajo demanda)
_connection_pool = None

def get_connection_pool(minconn=1, maxconn=5):
    """
    Retorna un pool de conexiones SimpleConnectionPool.
    Si no existe, lo crea usando la configuración de DB_CONFIG.
    """
    global _connection_pool
    if _connection_pool is None:
        validate_db_config()
        try:
            _connection_pool = pool.SimpleConnectionPool(
                minconn, maxconn, **DB_CONFIG
            )
        except Exception as e:
            raise RuntimeError(f"No se pudo crear el pool de conexiones: {e}")
    return _connection_pool

def get_connection():
    """
    Obtiene una conexión del pool.
    Úsala dentro de un contexto o asegúrate de cerrarla después.
    """
    pool = get_connection_pool()
    try:
        conn = pool.getconn()
        # Asegurar autocommit desactivado (control manual en queries.py)
        conn.autocommit = False
        return conn
    except Exception as e:
        raise RuntimeError(f"No se pudo obtener conexión del pool: {e}")

def release_connection(conn):
    """Devuelve una conexión al pool."""
    pool = get_connection_pool()
    if conn:
        pool.putconn(conn)

def close_all_connections():
    """Cierra todas las conexiones del pool (útil al terminar la app)."""
    global _connection_pool
    if _connection_pool:
        _connection_pool.closeall()
        _connection_pool = None

# Context manager para usar con 'with'
from contextlib import contextmanager

@contextmanager
def db_connection():
    """
    Context manager que obtiene una conexión del pool y la devuelve al salir.
    Uso:
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute(...)
    """
    conn = get_connection()
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        release_connection(conn)
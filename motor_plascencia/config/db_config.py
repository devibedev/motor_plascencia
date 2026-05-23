from psycopg2 import pool

def get_connection_pool():
    return pool.SimpleConnectionPool(1, 5, **DB_PARAMS)
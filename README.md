# "Motor_Plascencia" #
estructura de calculo para despiece de ventanas 

Estructura del workspace para la planta de producción de aluminio y vidrio, 
basada en Streamlit + PostgreSQL + Docker.

## Árbol de directorios

touch config/__init__.py database/__init__.py src/__init__.py ui/__init__.py ui/components/__init__.py tests/__init__.py
# 1. Clonar o crear la estructura
# 2. Copiar .env.example a .env y editar credenciales
cp .env.example .env

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Aplicar migraciones (si existen)
bash scripts/run_migrations.sh

# 5. Sembrar datos iniciales (solo la primera vez)
python scripts/seed_data.py

# 6. Ejecutar la aplicación
streamlit run ui/app.py

## estructura de repositorio
motor_plascencia/
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml               # opcional, para definir el proyecto
│
├── config/
│   ├── __init__.py
│   ├── settings.py              # carga variables de entorno con validación
│   └── db_config.py             # lógica de conexión (pool, retry, etc.)
│
├── database/
│   ├── __init__.py
│   ├── queries.py               # operaciones SQL modulares (tal como ya lo tienes)
│   ├── connection.py            # funciones de conexión y contexto
│   └── migrations/
│       ├── 001_initial_schema.sql   # el script que ya creaste
│       └── README.md            # cómo aplicar migraciones
│
├── src/
│   ├── __init__.py
│   ├── calculos.py              # lógica de negocio pura (cortes, descuentos)
│   ├── proyectos.py             # registrar proyectos, generar BOM
│   └── vidrios.py               # consultas de vidrios, cálculos
│
├── ui/
│   ├── __init__.py
│   ├── app.py                   # la aplicación Streamlit principal
│   ├── styles.py                # CSS y temas (allí va tu bloque de estilos)
│   └── components/
│       ├── __init__.py
│       ├── sidebar.py           # selectores de sistema, dimensiones, vidrio
│       └── results.py           # tablas de resultados y gráficos
│
├── tests/
│   ├── __init__.py
│   ├── test_calculos.py         # pruebas unitarias de descuentos y cortes
│   ├── test_queries.py          # pruebas de integración con BD de prueba
│   └── conftest.py              # fixtures (base de datos efímera)
│
└── scripts/
    ├── run_migrations.sh        # aplica todas las migraciones en orden
    ├── seed_data.py             # inserts iniciales (sistemas, vidrios)
    └── backup_db.sh             # respaldo automático de la base de datos

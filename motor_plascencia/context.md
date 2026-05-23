# Contexto del Proyecto: motor_plascencia

## Propósito
Aplicación industrial para el cálculo dinámico de cortes de aluminio y vidrio, 
impulsada por una base de datos PostgreSQL que almacena las configuraciones 
reales de los sistemas (descuentos, momentos de inercia). 
La interfaz se ejecuta con Streamlit sobre una Raspberry Pi, 
con soporte Docker para despliegue.

## Tecnologías
- Python 3.11
- Streamlit (interfaz de usuario)
- PostgreSQL 15 (base de datos, tablas: `catalogo_sistemas`, `vidrios_medidas`, `proyectos`, `proyecto_materiales_detalles`)
- psycopg2 (conexión a BD)
- Docker / Docker Compose (contenedores)
- CSS personalizado para accesibilidad (alto contraste en selectboxes)

## Estructura deseada (modular)
motor_plascencia/
├── config/
│ ├── init.py
│ ├── settings.py # Carga .env con DB_CONFIG
│ └── db_config.py # (opcional, no usado)
├── database/
│ ├── init.py
│ ├── connection.py # Pool de conexiones y context manager
│ ├── queries.py # Funciones SQL (sistemas, vidrios, proyectos)
│ └── migrations/
│ └── 001_initial_schema.sql
├── src/
│ ├── init.py
│ └── calculos.py # Lógica de negocio pura (cálculo de cortes)
├── ui/
│ ├── init.py
│ ├── app.py # Punto de entrada Streamlit
│ ├── styles.py # CSS de alto contraste
│ └── components/
│ ├── init.py
│ ├── sidebar.py # Widgets de la barra lateral
│ └── results.py # Tablas, guardado de proyectos
├── tests/
│ └── init.py
├── scripts/
│ └── run_migrations.sh
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md

text

## Estado actual del repositorio (problemas detectados)
1. Existen dos puntos de entrada: `app.py` en la raíz (monolítico funcional) y `ui/app.py` (modular pero roto porque importa módulos inexistentes).
2. Archivos con espacios en el nombre: `" Dockerfile "` y `".env.example "` impiden que Docker los reconozca.
3. `config/_init_.py` está mal escrito (guion bajo simple en vez de doble).
4. Faltan los archivos `__init__.py` en `database`, `src`, `ui/components` y `tests`.
5. No existen los módulos `database/queries.py`, `ui/styles.py`, `ui/components/sidebar.py`, `ui/components/results.py`, `src/calculos.py`.
6. `ui/app.py` actual tiene imports incorrectos y lógica redundante; necesita ser simplificado.
7. `requirements.txt` está en la raíz del repositorio pero debería estar dentro de `motor_plascencia/` (si esa es la carpeta del proyecto; en realidad el repo ya es `motor_plascencia`, así que está en la ubicación correcta, pero el `README.md` y la estructura sugieren que todo debe estar en la raíz).
8. `config/db_config.py` no se usa en ninguna parte.

## Objetivo final
- Obtener un proyecto completamente modular, con todos los imports funcionando.
- La aplicación `ui/app.py` debe arrancar con `streamlit run ui/app.py`.
- La base de datos PostgreSQL debe estar disponible (local o Docker) con las tablas creadas.
- El CSS de alto contraste debe aplicarse correctamente.
- El flujo de trabajo del agente debe dejar el repositorio listo para desarrollo y despliegue.
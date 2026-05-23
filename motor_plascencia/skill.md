# Skill: project-setup

## Nombre
Configuración rigurosa de motor_plascencia

## Descripción
Skill que ejecuta un procedimiento paso a paso para corregir la estructura del proyecto, 
crear los módulos faltantes, eliminar redundancias y verificar que la aplicación Streamlit funcione correctamente 
con la base de datos PostgreSQL.

## Pasos de la habilidad

### Paso 0: Validación del entorno
- Asegurarse de estar en la raíz del repositorio (donde se encuentra `README.md`).
- Verificar que existe el archivo `.env.example` (con el nombre correcto, sin espacios).

### Paso 1: Renombrar archivos con espacios
```bash
mv " Dockerfile " "Dockerfile" 2>/dev/null
mv ".env.example " ".env.example" 2>/dev/null
Si los archivos no existen con espacios, ignorar el error.

Paso 2: Corregir nombre de config/_init_.py
bash
mv config/_init_.py config/__init__.py 2>/dev/null
Si __init__.py ya existe correctamente, omitir.

Paso 3: Crear __init__.py faltantes
Crear archivos vacíos con un comentario identificador:

bash
echo "# Paquete de acceso a datos" > database/__init__.py
echo "# Lógica de negocio" > src/__init__.py
mkdir -p ui/components
echo "# Componentes de UI" > ui/components/__init__.py
echo "# Pruebas unitarias" > tests/__init__.py
Paso 4: Generar database/queries.py
Crear el archivo con el siguiente contenido (ya definido en el plan de corrección).

Paso 5: Generar ui/styles.py
Crear el archivo con el CSS de alto contraste.

Paso 6: Generar ui/components/sidebar.py
Crear el componente de barra lateral que usa database.queries.

Paso 7: Generar ui/components/results.py
Crear el componente de visualización de resultados y registro de proyectos.

Paso 8: Generar src/calculos.py
Crear el módulo de lógica de negocio pura.

Paso 9: Simplificar ui/app.py
Reemplazar el contenido de ui/app.py con la versión que importa los nuevos módulos (usando st.cache_resource, etc.).

Paso 10: Manejar archivos redundantes
Mover el app.py raíz a app_backup.py (o eliminarlo si no se necesita).

Asegurarse de que requirements.txt está en la raíz del proyecto (si no, copiarlo desde la ubicación correcta).

Paso 11: Instalar dependencias
bash
pip install -r requirements.txt
(Opcional, si el entorno ya está configurado, verificar que todas las dependencias están instaladas).

Paso 12: Configurar variables de entorno
Copiar .env.example a .env (si no existe) y solicitar al usuario que edite las credenciales.

Verificar que .env contiene las variables necesarias: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD.

Paso 13: Inicializar la base de datos (si es posible)
Si hay un servicio PostgreSQL accesible, ejecutar el script de migración:

bash
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f database/migrations/001_initial_schema.sql
Si no, mostrar un mensaje informativo.

Paso 14: Verificación final de la aplicación
Ejecutar streamlit run ui/app.py en modo headless (sin navegador) para detectar errores de importación.

Corregir cualquier error de módulo faltante o sintaxis.

Comprobar que la interfaz carga los sistemas desde la base de datos si está disponible.



#!/bin/bash
# =================================================================
# Aplica las migraciones SQL sobre la base de datos atoms_db
# Usa las variables del archivo .env (debe estar en la raíz)
# =================================================================
set -a
source .env
set +a

echo "Aplicando migraciones en $DB_NAME sobre $DB_HOST:$DB_PORT..."

for migration in database/migrations/*.sql; do
    echo "Ejecutando: $migration"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$migration"
    if [ $? -ne 0 ]; then
        echo "Error en la migración $migration. Abortando."
        exit 1
    fi
done

echo "Todas las migraciones aplicadas correctamente."
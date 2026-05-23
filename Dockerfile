FROM python:3.10-slim

# Evitar que Python escriba archivos .pyc y habilitar el búfer de salida directo
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema para compilar psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del proyecto
COPY . .

# Exponer los puertos de Streamlit (Taller y Oficina)
EXPOSE 8501
EXPOSE 8502

# Los contenedores individuales ejecutarán sus respectivos comandos desde docker-compose
FROM python:3.11-slim

# Evitar escritura de archivos .pyc y forzar salida stdout/stderr sin búfer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requerimientos e instalar paquetes de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del proyecto
COPY . /app/

# Exponer el puerto del servidor Django
EXPOSE 8000

# Script de arranque por defecto: aplicar migraciones e iniciar servidor
CMD ["sh", "-c", "python chatbot/manage.py migrate && python chatbot/manage.py runserver 0.0.0.0:8000"]

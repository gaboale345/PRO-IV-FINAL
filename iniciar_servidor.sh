#!/usr/bin/env bash
# Script para iniciar el servidor ChatBot accesible en la red 172.25.4.128/25

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
MANAGE_PY="$SCRIPT_DIR/chatbot/manage.py"

echo "=========================================================="
echo "    Iniciando Servidor ChatBot con Django y Ollama       "
echo "=========================================================="
echo "IP Local del Equipo: 172.25.4.247"
echo "Subred: 172.25.4.128/25"
echo "URL Local:           http://127.0.0.1:8000/"
echo "URL en tu Red:       http://172.25.4.247:8000/"
echo "=========================================================="
echo "Escuchando en todas las interfaces (0.0.0.0:8000)..."
echo "Presiona Ctrl + C para detener el servidor."
echo "----------------------------------------------------------"

exec "$VENV_PYTHON" "$MANAGE_PY" runserver 0.0.0.0:8000

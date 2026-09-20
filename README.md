# ChatBot con IA (Django + Ollama)

Esta aplicación web de chatbot proporciona una experiencia interactiva moderna con un diseño elegante de estilo *glassmorphism*, animaciones fluidas y respuestas en español impulsadas por **Ollama**. Permite enviar mensajes, recibir respuestas generadas por IA y consultar el historial completo de conversaciones.

## Características Principales
1. **Funcionamiento Local / Fuera de Línea** – La IA se ejecuta en tu propia máquina mediante Ollama, garantizando privacidad, seguridad y disponibilidad total sin conexión externa.
2. **Acceso en Red Local** – Configurado para escuchar en todas las interfaces (`0.0.0.0:8000`) y ser accesible desde la subred `172.25.4.128/25` a través de la dirección IP `172.25.4.247`.
3. **Interfaz Moderna y 100% en Español** – Diseño visual intuitivo con estilo *glassmorphism*, soporte para tecla Enter, indicador animado de escritura, paleta de colores sobria y sugerencias rápidas.
4. **Sistema de Personalidades y Plantillas de Prompts (Nueva Funcionalidad)** – Selector dinámico de roles (Asistente General, Programador Python, Tutor Académico y Redactor Creativo) que ajusta la plantilla de instrucciones del modelo en tiempo real.
5. **Exportación Multiformato del Historial (Nueva Funcionalidad)** – Descarga directa del historial de conversaciones en formatos Markdown (`.md`), Texto plano (`.txt`) o JSON estructurado (`.json`).
6. **Historial y Gestión de Conversaciones** – Permite revisar mensajes anteriores con marcas de tiempo en un panel lateral deslizable y vaciar la base de datos de manera limpia cuando se requiera.
7. **Comunicación Segura** – Protección CSRF configurada para soportar peticiones en red local sin bloqueos.
8. **Diseño Responsivo** – Optimizado para dispositivos de escritorio y móviles.

---

## Tecnologías Utilizadas 📌

### Frontend 📫
- HTML5 semántico
- CSS3 Moderno (Glassmorphism, Flexbox, animaciones clave)
- JavaScript nativo (Fetch API, manipulación asíncrona del DOM)
- Tipografía Plus Jakarta Sans

### Backend 🛠️
- Python 3.11+
- Django 5.1
- LangChain / LangChain-Ollama
- Ollama (Modelos locales `qwen2.5:0.5b` y `qwen2.5:1.5b`)

### Base de Datos 🗃️
- SQLite3

---

## Requisitos Previos
- Python 3.11 o superior
- Ollama instalado y en ejecución (`systemctl is-active ollama`)
- Modelo descargado en Ollama:
  ```bash
  ollama pull qwen2.5:0.5b
  # o también:
  ollama pull qwen2.5:1.5b
  ```

---

## Cómo Iniciar el Proyecto

### 1. Iniciar con el Script Rápido (Recomendado)
Desde la raíz del proyecto, ejecuta:
```bash
./iniciar_servidor.sh
```

### 2. O Iniciar Manualmente con el Entorno Virtual:
```bash
# Activar entorno virtual
source .venv/bin/activate

# Iniciar el servidor escuchando en todas las interfaces de red
python chatbot/manage.py runserver 0.0.0.0:8000
```

---

## Ejecución de Pruebas Automatizadas

El proyecto cuenta con un conjunto de pruebas unitarias automatizadas que verifican la interfaz, endpoints del chat, roles, exportación y base de datos:

```bash
# Con el entorno virtual activado:
python chatbot/manage.py test app
```

---

## Direcciones de Acceso

- **En este mismo equipo:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Desde cualquier equipo de tu red (172.25.4.128/25):** [http://172.25.4.247:8000/](http://172.25.4.247:8000/)
